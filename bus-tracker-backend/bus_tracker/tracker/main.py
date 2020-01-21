import contextlib
import functools

import asyncclick as click
import trio
from trio_websocket import serve_websocket

from bus_tracker.logger import set_logger, get_logger
from .server import handle_tracking, handle_webclients


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
    "--timeout",
    "-t",
    type=float,
    default=1.0,
    envvar="BUS_TRACKER_TIMEOUT",
    help="response to browser interval"
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="verbosity",
)
async def main(
        bus_port: int, browser_port: int, timeout: float, verbose: int
) -> None:
    set_logger(verbose)
    logger = get_logger(__name__)
    serve_buses = functools.partial(
        serve_websocket,
        handler=handle_tracking,
        host="0.0.0.0",
        port=bus_port,
        ssl_context=None
    )

    handler = functools.partial(handle_webclients, timeout=timeout)

    serve_webclients = functools.partial(
        serve_websocket,
        handler=handler,
        host='0.0.0.0',
        port=browser_port,
        ssl_context=None
    )

    logger.info("starting service")
    with contextlib.suppress(KeyboardInterrupt):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(serve_buses)
            nursery.start_soon(serve_webclients)
    logger.info("service stopped")
