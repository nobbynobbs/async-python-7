import contextlib
import json
from typing import Dict

import trio
from bus_tracker.tracker.validators import validate_bus_data, \
    validate_bounds_message
from trio_websocket import (
    ConnectionClosed, WebSocketRequest, WebSocketConnection,
)

from .entities import Bus, WindowBounds
from .responses import ErrorMessage, BusesMessage
from .exceptions import ValidationError
from bus_tracker.logger import get_logger

buses: Dict[str, Bus] = {}
logger = get_logger(__name__)


async def _listen_browser(
        ws: WebSocketConnection, bounds: WindowBounds
) -> None:
    """receive and update window bounds info"""
    while True:
        try:
            raw_message = await ws.get_message()
        except ConnectionClosed:
            break

        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.warning("received non-valid json: <%s>", raw_message)
            response = ErrorMessage(["requires valid JSON"])
            with contextlib.suppress(ConnectionClosed):
                await ws.send_message(response.json())
            continue
        else:
            logger.debug("received from client %s", message)

        try:
            validate_bounds_message(message)
        except ValidationError as e:
            logger.warning("unable to update bounds: %s", str(e))
            response = ErrorMessage([str(e)])
            with contextlib.suppress(ConnectionClosed):
                await ws.send_message(response.json())
        else:
            bounds.update(**message["data"])


async def _send_buses(ws: WebSocketConnection, bounds: WindowBounds) -> None:
    buses_list = [b for b in buses.values() if bounds.contains(*b.position)]
    response = BusesMessage(buses_list)
    await ws.send_message(response.json())


async def _talk_to_browser(
        ws: WebSocketConnection,
        bounds: WindowBounds,
        timeout: float,
) -> None:
    while True:
        try:
            await _send_buses(ws, bounds)
        except ConnectionClosed:
            break
        await trio.sleep(timeout)


async def handle_weblients(
        request: WebSocketRequest,
        timeout: float = 1,
) -> None:
    ws = await request.accept()
    bounds = WindowBounds()
    logger.debug("accept webclient connection")
    async with trio.open_nursery() as nursery:
        nursery.start_soon(_listen_browser, ws, bounds)
        nursery.start_soon(_talk_to_browser, ws, bounds, timeout)
    logger.debug("webclient connection closed")


async def handle_tracking(request: WebSocketRequest) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
        except ConnectionClosed:
            break
        else:
            logger.debug("received bus info: %s", message)

        try:
            bus_dict = json.loads(message)
        except json.JSONDecodeError:
            response = ErrorMessage(["requires valid JSON"])
            with contextlib.suppress(ConnectionClosed):
                await ws.send_message(response.json())
            logger.warning("received broken json")
            continue

        try:
            validate_bus_data(bus_dict)
        except ValidationError as e:
            response = ErrorMessage([str(e)])
            with contextlib.suppress(ConnectionClosed):
                await ws.send_message(response.json())
        else:
            bus = Bus(**bus_dict)
            buses[bus.busId] = bus
