import contextlib
import functools

import asyncclick as click
import trio
from bus_tracker.logger import logger
from bus_tracker.server import handle_tracking, handle_weblients
from trio_websocket import serve_websocket


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
