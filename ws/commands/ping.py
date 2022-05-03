import click
import trio

from ws.console import console
from ws.options import (
    duration_option,
    filename_option,
    interval_option,
    message_option,
    number_option,
    url_argument,
    validate_number,
)
from ws.settings import get_settings
from ws.utils import (
    catch_pydantic_error,
    catch_too_slow_error,
    configure_console_recording,
    function_runner,
    save_output,
    signal_handler,
    sleep_until,
    websocket_client,
)


@catch_too_slow_error
@catch_pydantic_error
async def make_ping(url: str, number: int, interval: float, message: bytes = None, filename: str = None) -> None:
    settings = get_settings()
    configure_console_recording(console, settings, filename)
    # trio_websockets by default sends 32 bytes if no payload is given
    payload_length = len(message) if message is not None else 32
    console.print(f'PING [info]{url}[/] with [info]{payload_length}[/] bytes of data')
    counter = 0
    async with websocket_client(url) as client:
        while True:
            counter += 1
            beginning = trio.current_time()
            with trio.fail_after(settings.response_timeout):
                await client.ping(message)
                duration = trio.current_time() - beginning
                console.print(f'[label]sequence[/]=[info]{counter}[/], [label]time[/]=[info]{duration:.2f}[/]s')

            if 0 < number <= counter:
                break

            await trio.sleep(interval)


async def main(
    url: str, number: int, interval: float, message: bytes = None, duration: float = None, filename: str = None
) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, make_ping, url, number, interval, message, filename)
        nursery.start_soon(signal_handler, nursery.cancel_scope)
        nursery.start_soon(sleep_until, nursery.cancel_scope, duration)

    if filename:
        save_output(console, filename)


@click.command()
@url_argument
@message_option('Message to send in the ping, MUST NOT be more than 125 bytes.')
@number_option(
    'Number of pings to make, a negative value means infinite.', validate_number('The number of pings cannot be 0')
)
@interval_option('Interval between pings in seconds.')
@duration_option
@filename_option
def ping(url: str, message: bytes, number: int, interval: int, duration: float, filename: str):
    """Pings a websocket server located at URL."""
    trio.run(main, url, number, interval, message, duration, filename)
