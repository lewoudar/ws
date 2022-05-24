import click
import trio

from ws.client import websocket_client
from ws.console import configure_console_recording, console, save_output
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
from ws.utils.io import function_runner, signal_handler, sleep_until


async def make_pong(url: str, number: int, interval: float, message: bytes = None, filename: str = None) -> None:
    message = b'' if message is None else message
    payload_length = len(message)
    configure_console_recording(console, get_settings(), filename)
    plural = 's' if payload_length > 1 else ''
    console.print(f'Sent unsolicited PONG of {payload_length} byte{plural} of data to [info]{url}[/]')

    counter = 0
    async with websocket_client(url) as client:
        while True:
            counter += 1
            beginning = trio.current_time()
            await client.pong(message)
            duration = trio.current_time() - beginning
            console.print(f'[label]sequence[/]=[number]{counter}[/], [label]time[/]=[number]{duration:.2f}s[/]')

            if 0 < number <= counter:
                break

            await trio.sleep(interval)


async def main(
    url: str, number: int, interval: float, message: bytes = None, duration: float = None, filename: str = None
) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, make_pong, url, number, interval, message, filename)
        nursery.start_soon(signal_handler, nursery.cancel_scope)
        nursery.start_soon(sleep_until, nursery.cancel_scope, duration)

    if filename:
        save_output(console, filename)


@click.command()
@url_argument
@message_option('Message to send in the pong, MUST NOT be more than 125 bytes.')
@number_option(
    'Number of pongs to make, a negative value means infinite.', validate_number('The number of pongs cannot be 0')
)
@interval_option('Interval between pongs in seconds.')
@duration_option
@filename_option
def pong(url: str, number: int, interval: float, message: bytes, duration: float, filename: str):
    """
    Sends a pong to websocket server located at URL.
    This query does not wait for an answer.
    """
    trio.run(main, url, number, interval, message, duration, filename)
