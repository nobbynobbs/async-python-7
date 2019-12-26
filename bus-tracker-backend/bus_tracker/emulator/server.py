import copy
import dataclasses
import functools
import itertools
import json
import os
import random
from typing import List, Optional, Tuple, AsyncIterable, TYPE_CHECKING

import trio
from trio_websocket import open_websocket_url

from bus_tracker.logger import get_logger
from . import BASE_DIR
from .utils import load_routes, generate_bus_id, reconnect

if TYPE_CHECKING:
    from typing_extensions import TypedDict

logger = get_logger(__name__)


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
        bus_index: int = None,
        emulator_id: str = "",
        refresh_timeout: float = .1,
) -> AsyncIterable[BusPositionInfo]:
    route_name = route["name"]
    bus_info = BusPositionInfo(
        busId=generate_bus_id(route_name, bus_index, emulator_id),
        route=route_name,
    )
    for coordinate in itertools.cycle(route["coordinates"]):
        bus_info.lat, bus_info.lng = coordinate
        yield bus_info
        await trio.sleep(refresh_timeout)


async def send_route_info(
        route: RouteInfo,
        bus_index: int,
        emulator_id: str,
        refresh_timeout: float,
        channels: List[trio.MemorySendChannel]
) -> None:
    bus_info_generator = run_bus(
        route, bus_index, emulator_id, refresh_timeout
    )
    async for bus_position_info in bus_info_generator:
        message = dataclasses.asdict(bus_position_info)
        channel: trio.MemorySendChannel = random.choice(channels)
        await channel.send(json.dumps(message))


@reconnect
async def send_messages(url: str, channel: trio.MemoryReceiveChannel) -> None:
    logger.info("starting messages sender")
    async with open_websocket_url(url) as ws:
        logger.debug("successfully connected to %s", url)
        async for message in channel:
            await ws.send_message(message)
    logger.info("messages sender finished")


ChannelsList = List[Tuple[trio.MemorySendChannel, trio.MemoryReceiveChannel]]


async def serve(
        url: str,
        routes_count: int = 500,
        buses_per_route: int = 2,
        concurrency: int = 5,
        emulator_id: str = "",
        refresh_timeout: float = 0.1,
) -> None:
    channels: ChannelsList = []
    for _ in range(concurrency):
        channels.append(trio.open_memory_channel(0))
    send_channels = [ch for ch, _ in channels]
    receive_channels = [ch for _, ch in channels]

    async with trio.open_nursery() as nursery:  # type: trio.Nursery
        routes_generator = zip(
            range(routes_count), load_routes(os.path.join(BASE_DIR, "routes"))
        )
        for route_index, route in routes_generator:
            for bus_index in range(buses_per_route):
                route = copy.copy(route)
                bus_id_suffix = route_index * buses_per_route + bus_index
                coordinates = route["coordinates"]
                start_offset = random.randint(0, 2 * len(coordinates) // 3)
                route["coordinates"] = coordinates[start_offset:]
                partial_send_info = functools.partial(
                    send_route_info,
                    route=route,
                    bus_index=bus_id_suffix,
                    emulator_id=emulator_id,
                    refresh_timeout=refresh_timeout,
                    channels=send_channels,
                )
                nursery.start_soon(partial_send_info)

        for channel in receive_channels:
            nursery.start_soon(send_messages, url, channel)
