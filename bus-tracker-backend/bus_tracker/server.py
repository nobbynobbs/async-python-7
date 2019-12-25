import contextlib
import functools
import json
from typing import Dict, Any

from bus_tracker.logger import logger

import trio
from trio_websocket import serve_websocket, ConnectionClosed, WebSocketRequest

from bus_tracker.emulator.server import serve as track_buses


buses: Dict[str, Any] = {}
buses_lock = trio.Lock()


async def handle_weblients(request: WebSocketRequest) -> None:
        ws = await request.accept()
        while True:
            try:
                async with buses_lock:
                    l = list(buses.values())
                await ws.send_message(
                    json.dumps({
                        "msgType": "Buses",
                        "buses": l,
                    })
                )
            except ConnectionClosed:
                break
            await trio.sleep(.1)


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


async def serve_webclients():
    await serve_websocket(handle_weblients, '0.0.0.0', 8000, ssl_context=None)


async def serve_tracking():
    await serve_websocket(handle_tracking, "127.0.0.1", 8080, ssl_context=None)


async def serve():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_tracking)
        nursery.start_soon(serve_webclients)
        nursery.start_soon(track_buses, "ws://127.0.0.1:8080")


def main():
    with contextlib.suppress(KeyboardInterrupt):
        trio.run(serve)
