import click
import trio

from ws.console import console
from ws.parameters import WS_URL, ByteParamType
from ws.settings import get_settings
from ws.utils import catch_too_slow_error, function_runner, signal_handler, websocket_client

SETTINGS = get_settings()


def validate_number(ctx: click.Context, param: click.Parameter, value: int) -> int:
    if value == 0:
        raise click.BadParameter('The number of pings cannot be 0')
    return value


@catch_too_slow_error
async def make_ping(url: str, number: int, interval: float, message: bytes = None) -> None:
    # trio_websockets by default sends 32 bytes if no payload is given
    payload_length = len(message) if message is not None else 32
    console.print(f'PING [blue]{url}[/] with {payload_length} bytes of data')
    counter = 0
    async with websocket_client(url) as client:
        while True:
            counter += 1
            beginning = trio.current_time()
            with trio.fail_after(SETTINGS.response_timeout):
                await client.ping(message)
                duration = trio.current_time() - beginning
                console.print(f'[label]sequence[/]=[info]{counter}[/], [label]time[/]=[info]{duration:.2f}[/]s')

            if 0 < number <= counter:
                break

            await trio.sleep(interval)


async def main(url: str, number: int, interval: float, message: bytes = None) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, make_ping, url, number, interval, message)
        nursery.start_soon(signal_handler, nursery.cancel_scope)


@click.command()
@click.argument('url', type=WS_URL)
# we choose a length of 125 for the following reasons:
# - A control frame like ping should not be fragmented
# - The maximum length to feat the size in one octet in the resulting websocket packet is 125, and it seems a
# reasonable value to avoid error messages related to message size on the server side
@click.option(
    '-m',
    '--message',
    type=ByteParamType(max_length=125),
    help='Message to send in the ping, MUST NOT be more than 125 bytes',
)
@click.option(
    '-n',
    '--number',
    type=int,
    default=1,
    show_default=True,
    callback=validate_number,
    help='Number of pings to make, a negative value means infinite.',
)
@click.option(
    '-i',
    '--interval',
    type=click.FloatRange(min=0, min_open=True),
    default=1.0,
    show_default=True,
    help='Interval between pings.',
)
def ping(url: str, message: bytes, number: int, interval: int):
    """Pings a websocket server located at URL."""
    trio.run(main, url, number, interval, message)
