import click
import trio

from ws.options import url_argument
from ws.parameters import ByteParamType
from ws.utils import function_runner, signal_handler, websocket_client


async def send_bytes(url: str, message: bytes) -> None:
    async with websocket_client(url) as client:
        await client.send_message(message)
        # the sleep is to give time to the server to handle the message before closing the client
        await trio.sleep(0.5)


async def main(url: str, message: bytes) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, send_bytes, url, message)
        nursery.start_soon(signal_handler, nursery.cancel_scope)


@click.command()
@url_argument
@click.argument('message', type=ByteParamType())
def byte(url: str, message: bytes):
    """Sends binary message to URL endpoint."""
    trio.run(main, url, message)
