import functools
import os
import json
from typing import Generator, Any, Callable, Awaitable

import trio
from bus_tracker.logger import get_logger
from trio_websocket import HandshakeError, ConnectionClosed


logger = get_logger(__name__)


def load_routes(directory_path: str = 'routes') -> Generator[Any, None, None]:
    filenames = (f for f in os.listdir(directory_path) if f.endswith(".json"))
    for filename in filenames:
        filepath = os.path.join(directory_path, filename)
        with open(filepath, 'r', encoding='utf8') as file:
            yield json.load(file)


def generate_bus_id(
        route_id: str,
        bus_index: int = None,
        emulator_id: str = ""
) -> str:
    if bus_index is not None:
        route_id = f"{route_id}-{bus_index}"
    if emulator_id:
        route_id = f"{emulator_id}-{route_id}"
    return route_id


AsyncFunction = Callable[..., Awaitable]


def reconnect(func: AsyncFunction) -> AsyncFunction:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        while True:
            try:
                await func(*args, **kwargs)
            except (HandshakeError, ConnectionClosed):
                msg = "cannot connect to server, reconnect in %d seconds"
                logger.warning(msg, 1)
                await trio.sleep(1)
            else:
                break
    return wrapper
