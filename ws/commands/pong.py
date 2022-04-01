import click
import trio

from ws.console import console
from ws.options import interval_option, message_option, number_option, url_argument, validate_number
from ws.utils import function_runner, signal_handler, websocket_client


async def make_pong(url: str, number: int, interval: float, message: bytes = None) -> None:
    message = b'' if message is None else message
    payload_length = len(message)
    console.print(f'Sent unsolicited PONG of [info]{payload_length}[/] bytes of data to [info]{url}[/]')

    counter = 0
    async with websocket_client(url) as client:
        while True:
            counter += 1
            beginning = trio.current_time()
            await client.pong(message)
            duration = trio.current_time() - beginning
            console.print(f'[label]sequence[/]=[info]{counter}[/], [label]time[/]=[info]{duration:.2f}[/]s')

            if 0 < number <= counter:
                break

            await trio.sleep(interval)


async def main(url: str, number: int, interval: float, message: bytes = None) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, make_pong, url, number, interval, message)
        nursery.start_soon(signal_handler, nursery.cancel_scope)


@click.command()
@url_argument
@message_option('Message to send in the pong, MUST NOT be more than 125 bytes.')
@number_option(
    'Number of pongs to make, a negative value means infinite.', validate_number('The number of pongs cannot be 0')
)
@interval_option('Interval between pongs.')
def pong(url: str, number: int, interval: float, message: bytes = None):
    """
    Sends a pong to websocket server located at URL.
    This query does not wait for an answer.
    """
    trio.run(main, url, number, interval, message)