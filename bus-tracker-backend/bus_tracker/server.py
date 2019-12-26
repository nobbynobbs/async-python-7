import contextlib
import json
from typing import Dict, Any

from bus_tracker.logger import logger

import trio
from trio_websocket import (
    serve_websocket, ConnectionClosed, WebSocketRequest, WebSocketConnection,
)

buses: Dict[str, Any] = {}
buses_lock = trio.Lock()


def in_box(box: Dict[str, float], bus_info: Dict[str, Any]) -> bool:
    return (box["south_lat"] < bus_info["lat"] < box["north_lat"]
            and box["west_lng"] < bus_info["lng"] < box["east_lng"])


async def update_bounds(
        ws: WebSocketConnection, bounds: Dict[str, float]
) -> None:
    while True:
        try:
            message = json.loads(await ws.get_message())
        except json.JSONDecodeError:
            pass
        else:
            bounds.update(message["data"])


async def send_buses(
        ws: WebSocketConnection, bounds: Dict[str, float]
) -> None:
    while True:
        try:
            async with buses_lock:
                buses_list = list(buses.values())
            if bounds:
                buses_list = [bus for bus in buses_list if in_box(bounds, bus)]
            await ws.send_message(
                json.dumps({
                    "msgType": "Buses",
                    "buses": buses_list,
                })
            )
        except ConnectionClosed:
            break
        await trio.sleep(1)


async def handle_weblients(request: WebSocketRequest) -> None:
    ws = await request.accept()
    bounds: Dict[str, float] = {}
    async with trio.open_nursery() as nursery:
        nursery.start_soon(update_bounds, ws, bounds)
        nursery.start_soon(send_buses, ws, bounds)


async def handle_tracking(request: WebSocketRequest) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            logger.debug(message)
            bus_info = json.loads(message)
            async with buses_lock:
                buses[bus_info["busId"]] = bus_info
        except ConnectionClosed:
            break


async def serve_webclients() -> None:
    await serve_websocket(handle_weblients, '0.0.0.0', 8000, ssl_context=None)


async def serve_tracking() -> None:
    await serve_websocket(handle_tracking, "0.0.0.0", 8080, ssl_context=None)


async def serve() -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_tracking)
        nursery.start_soon(serve_webclients)


def main() -> None:
    with contextlib.suppress(KeyboardInterrupt):
        trio.run(serve)
