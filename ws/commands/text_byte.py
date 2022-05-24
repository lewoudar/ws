from typing import AnyStr

import click
import trio

from ws.client import websocket_client
from ws.console import console
from ws.options import url_argument
from ws.parameters import ByteParamType, TextParamType
from ws.utils.io import function_runner, signal_handler
from ws.utils.size import get_readable_size


async def send_message(url: str, message: AnyStr) -> None:
    async with websocket_client(url) as client:
        await client.send_message(message)
        length = len(message)
        console.print(f'Sent [number]{get_readable_size(length)}[/] of data over the wire.')
        # the sleep is to give time to the server to handle the message before closing the client
        # and also to make the tests passed :D
        await trio.sleep(0.1)


async def main(url: str, message: AnyStr) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, send_message, url, message)
        nursery.start_soon(signal_handler, nursery.cancel_scope)


@click.command()
@url_argument
@click.argument('message', type=ByteParamType())
def byte(url: str, message: bytes):
    """Sends binary message to URL endpoint."""
    trio.run(main, url, message)


@click.command()
@url_argument
@click.argument('message', type=TextParamType())
def text(url: str, message: str):
    """Sends text message on URL endpoint."""
    trio.run(main, url, message)
