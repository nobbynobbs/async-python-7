import contextlib
import itertools
import json
import logging
import os
import dataclasses
import random
from sys import stderr
from typing import Union, List, Optional, Tuple, AsyncIterable, Iterable

from trio_websocket import open_websocket_url, WebSocketConnection

import trio

from . import BASE_DIR
from .utils import load_routes, generate_bus_id

from typing_extensions import TypedDict


@dataclasses.dataclass()
class BusPositionInfo:
    busId: str
    route: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class RouteInfo(TypedDict):
    name: str
    station_start_name: str
    station_stop_name: str
    coordinates: List[Tuple[float, float]]


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
        logging.debug(dataclasses.asdict(bus_info))
        yield bus_info
        await trio.sleep(0.1)


async def send_route_info(
        route, channels: List[trio.MemorySendChannel]
) -> None:
    async for bus_position_info in run_bus(route):
        message = dataclasses.asdict(bus_position_info)
        channel: trio.MemorySendChannel = random.choice(channels)
        await channel.send(json.dumps(message))


async def send_messages(url: str, channel: trio.MemoryReceiveChannel) -> None:
    try:
        async with open_websocket_url(url) as ws:
            async for message in channel:
                await ws.send_message(message)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


ChannelsList = List[Tuple[trio.MemorySendChannel, trio.MemoryReceiveChannel]]


import trio
from sys import stderr
from trio_websocket import open_websocket_url


async def serve(url: str):
    concurrency = 10
    channels: ChannelsList = []
    for _ in range(concurrency):
        channels.append(trio.open_memory_channel(0))

    send_channels = [ch for ch, _ in channels]
    receive_channels = [ch for _, ch in channels]

    async with trio.open_nursery() as nursery:
        for route in load_routes(os.path.join(BASE_DIR, "routes")):
            nursery.start_soon(send_route_info, route, send_channels)

        for channel in receive_channels:
            nursery.start_soon(send_messages, url, channel)


def main():
    with contextlib.suppress(KeyboardInterrupt):
        trio.run(serve)
