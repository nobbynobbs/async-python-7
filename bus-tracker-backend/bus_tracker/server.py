import contextlib
import dataclasses
import functools
import json
from typing import Dict, Any, Tuple

import trio
from trio_websocket import (
    serve_websocket, ConnectionClosed, WebSocketRequest, WebSocketConnection,
)
import asyncclick as click

from bus_tracker.logger import logger
from bus_tracker.json_encoder import dumps


MIN_LAT: float = -90  # south pole
MAX_LAT: float = +90  # north pole
MIN_LNG: float = -180  # west
MAX_LNG: float = +180  # east


buses: Dict[str, Any] = {}


@dataclasses.dataclass()
class Bus:
    busId: str
    route: str
    lat: float
    lng: float

    @classmethod
    def from_dict(cls, bus_info: Dict[str, Any]) -> "Bus":
        return cls(**bus_info)

    @property
    def position(self) -> Tuple[float, float]:
        return self.lat, self.lng


@dataclasses.dataclass()
class WindowBounds:
    south_lat: float = MIN_LAT
    north_lat: float = MAX_LAT
    west_lng: float = MIN_LNG
    east_lng: float = MAX_LNG

    def update(
            self,
            south_lat: float,
            north_lat: float,
            west_lng: float,
            east_lng: float
    ) -> None:
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng

    def contains(self, lat: float, lng: float) -> bool:
        return (self.south_lat < lat < self.north_lat
                and self.west_lng < lng < self.east_lng)


async def listen_browser(
        ws: WebSocketConnection, bounds: WindowBounds
) -> None:
    while True:
        try:
            message = json.loads(await ws.get_message())
            logger.debug("received from client %s", message)
            bounds.update(**message["data"])
        except json.JSONDecodeError:
            pass
        except ConnectionClosed:
            break


async def _send_buses(ws: WebSocketConnection, bounds: WindowBounds) -> None:
    buses_list = list(buses.values())
    buses_list = [bus for bus in buses_list if bounds.contains(*bus.position)]
    await ws.send_message(
        dumps({"msgType": "Buses", "buses": buses_list})
    )


async def talk_to_browser(
        ws: WebSocketConnection, bounds: WindowBounds
) -> None:
    while True:
        try:
            await _send_buses(ws, bounds)
        except ConnectionClosed:
            break
        await trio.sleep(1)


async def handle_weblients(request: WebSocketRequest) -> None:
    ws = await request.accept()
    bounds = WindowBounds()
    logger.debug("accept webclient connection")
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds)
        nursery.start_soon(talk_to_browser, ws, bounds)
    logger.debug("webclient connection closed")


async def handle_tracking(request: WebSocketRequest) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            logger.debug("received bus info: %s", message)
            bus_info = json.loads(message)
            buses[bus_info["busId"]] = Bus.from_dict(bus_info)
        except ConnectionClosed:
            break


@click.command()
@click.option(
    "--bus_port",
    type=int,
    default=8080,
    envvar="BUS_TRACKER_BUS_PORT",
    help="listen for bus coordinates info",
)
@click.option(
    "--browser_port",
    type=int,
    default=8000,
    envvar="BUS_TRACKER_BROWSER_PORT",
    help="listen for service clients"
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="verbosity",
)
async def main(bus_port: int, browser_port: int, verbose: int) -> None:
    if verbose < 1:
        logger.setLevel("WARNING")
    if verbose == 1:
        logger.setLevel("INFO")
    if verbose > 1:
        logger.setLevel("DEBUG")

    serve_buses = functools.partial(
        serve_websocket,
        handler=handle_tracking,
        host="0.0.0.0",
        port=bus_port,
        ssl_context=None
    )

    serve_webclients = functools.partial(
        serve_websocket,
        handler=handle_weblients,
        host='0.0.0.0',
        port=browser_port,
        ssl_context=None
    )
    with contextlib.suppress(KeyboardInterrupt):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(serve_buses)
            nursery.start_soon(serve_webclients)
