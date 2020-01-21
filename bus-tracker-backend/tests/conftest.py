import functools
import socket
from typing import Callable

import pytest
import trio
from trio_websocket import (
    serve_websocket, open_websocket_url, WebSocketConnection
)

from bus_tracker.tracker.server import handle_webclients, handle_tracking


@pytest.fixture(scope="session")
def unused_port():
    def f():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1', 0))
            return sock.getsockname()[1]
    return f


@pytest.fixture(scope="function")
async def webclient_socket(
        nursery: trio.Nursery, unused_port: Callable[[], int]
) -> WebSocketConnection:
    port = unused_port()
    server = functools.partial(
        serve_websocket,
        handler=handle_webclients,
        host='127.0.0.1',
        port=port,
        ssl_context=None
    )
    await nursery.start(server)
    async with open_websocket_url(f"ws://127.0.0.1:{port}") as ws:
        yield ws


@pytest.fixture(scope="function")
async def tracking_socket(
        nursery: trio.Nursery, unused_port: Callable[[], int]
) -> WebSocketConnection:
    port = unused_port()
    server = functools.partial(
        serve_websocket,
        handler=handle_tracking,
        host='127.0.0.1',
        port=port,
        ssl_context=None
    )
    await nursery.start(server)
    async with open_websocket_url(f"ws://127.0.0.1:{port}") as ws:
        yield ws
