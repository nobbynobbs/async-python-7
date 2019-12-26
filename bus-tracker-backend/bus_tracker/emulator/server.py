import contextlib
import copy
import dataclasses
import itertools
import json
import os
import random
from typing import List, Optional, Tuple, AsyncIterable, TYPE_CHECKING
from sys import stderr

import trio
from trio_websocket import open_websocket_url

from bus_tracker.logger import logger

from . import BASE_DIR
from .utils import load_routes, generate_bus_id

if TYPE_CHECKING:
    from typing_extensions import TypedDict


@dataclasses.dataclass()
class BusPositionInfo:
    busId: str
    route: str
    lat: Optional[float] = None
    lng: Optional[float] = None


if TYPE_CHECKING:
    class RouteInfo(TypedDict):
        name: str
        station_start_name: str
        station_stop_name: str
        coordinates: List[Tuple[float, float]]
else:
    RouteInfo = None


async def run_bus(
        route: RouteInfo,
        bus_index: int = None
) -> AsyncIterable[BusPositionInfo]:
    route_name = route["name"]
    bus_info = BusPositionInfo(
        busId=generate_bus_id(route_name, bus_index),
        route=route_name,
    )
    for coordinate in itertools.cycle(route["coordinates"]):
        bus_info.lat, bus_info.lng = coordinate
        # logging.debug(dataclasses.asdict(bus_info))
        yield bus_info
        await trio.sleep(0.1)


async def send_route_info(
        route: RouteInfo,
        bus_index: int,
        channels: List[trio.MemorySendChannel]
) -> None:
    async for bus_position_info in run_bus(route, bus_index):
        message = dataclasses.asdict(bus_position_info)
        channel: trio.MemorySendChannel = random.choice(channels)
        await channel.send(json.dumps(message))


async def send_messages(url: str, channel: trio.MemoryReceiveChannel) -> None:
    logger.info("starting messages sender")
    try:
        async with open_websocket_url(url) as ws:
            async for message in channel:
                await ws.send_message(message)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


ChannelsList = List[Tuple[trio.MemorySendChannel, trio.MemoryReceiveChannel]]


async def serve(url: str, routes_count: int = 500) -> None:
    concurrency = 10
    channels: ChannelsList = []
    for _ in range(concurrency):
        channels.append(trio.open_memory_channel(0))
    send_channels = [ch for ch, _ in channels]
    receive_channels = [ch for _, ch in channels]

    async with trio.open_nursery() as nursery:
        for i, route in zip(range(routes_count), itertools.cycle(
                load_routes(os.path.join(BASE_DIR, "routes")))):
            route = copy.copy(route)
            coordinates = route["coordinates"]
            start_offset = random.randint(0, 2 * len(coordinates) // 3)
            route["coordinates"] = coordinates[start_offset:]
            nursery.start_soon(send_route_info, route, i, send_channels)

        for channel in receive_channels:
            nursery.start_soon(send_messages, url, channel)


def main() -> None:
    with contextlib.suppress(KeyboardInterrupt):
        trio.run(serve, "ws://tracker:8080", 20_000)
