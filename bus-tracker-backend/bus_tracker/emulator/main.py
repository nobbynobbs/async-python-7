import contextlib

import asyncclick as click
from bus_tracker.emulator.server import serve
from bus_tracker.logger import set_logger

ROUTES_COUNT = 595


@click.command()
@click.option(
    "-s",
    "--server",
    "url",
    type=str,
    default="ws://localhost:8080",
    envvar="BUS_EMULATOR_SERVER",
    help="websocket server endpoint"
)
@click.option(
    "-r",
    "--routes_count",
    type=click.IntRange(min=1, max=ROUTES_COUNT),
    default=ROUTES_COUNT,
    envvar="BUS_EMULATOR_ROUTES",
    help="count of different routes"
)
@click.option(
    "-x",
    "--buses_per_route",
    type=click.IntRange(min=1, max=50, clamp=True),
    default=2,
    envvar="BUS_EMULATOR_BUSES_PER_ROUTE",
    help="count of buses spawned on each route"
)
@click.option(
    "-w",
    "--websockets_count",
    type=click.IntRange(min=1, max=10, clamp=True),
    default=5,
    envvar="BUS_EMULATOR_WEBSOCKETS",
    help="count of websockets connected to server",
)
@click.option(
    "--emulator_id",
    type=str,
    default="",
    envvar="BUS_EMULATOR_ID",
    help="bus id prefix",
)
@click.option(
    "-t",
    "--refresh_timeout",
    type=float,
    default=.1,
    envvar="BUS_EMULATOR_TIMEOUT",
    help="set coordinates update frequency"
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="verbosity"
)
async def main(
        url: str,
        routes_count: int,
        buses_per_route: int,
        websockets_count: int,
        emulator_id: str,
        refresh_timeout: float,
        verbose: int
) -> None:
    set_logger(verbose)

    with contextlib.suppress(KeyboardInterrupt):
        await serve(
            url=url,
            routes_count=routes_count,
            buses_per_route=buses_per_route,
            concurrency=websockets_count,
            emulator_id=emulator_id,
            refresh_timeout=refresh_timeout,
        )
