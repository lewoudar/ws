import json
from datetime import datetime
from typing import AnyStr

import click
import trio
from rich.console import Console
from rich.markup import escape

from ws.console import console
from ws.options import url_argument
from ws.utils import function_runner, signal_handler, websocket_client


def trace_rule(console: Console, is_bytes: bool) -> None:
    timestamp = trio.current_time()
    date = datetime.fromtimestamp(timestamp)
    message_type = 'BINARY' if is_bytes else 'TEXT'

    console.rule(f'[bold info]{message_type} message at {date:%Y-%m-%d %H:%M:%S}')


def print_message(console: Console, message: AnyStr, is_bytes: bool) -> None:
    if is_bytes:
        console.print(message)
    else:
        console.print(escape(message))


def print_json(console: Console, message: AnyStr, is_bytes: bool) -> None:
    if is_bytes:
        try:
            message = message.decode()
        except UnicodeError:
            console.print(message)
            return
    try:
        console.print_json(escape(message))
    except json.JSONDecodeError:
        console.print(escape(message))


async def listen_messages(url: str, is_json: bool) -> None:
    async with websocket_client(url) as client:
        while True:
            message = await client.get_message()
            is_bytes = isinstance(message, bytes)
            trace_rule(console, is_bytes)

            if is_json:
                print_json(console, message, is_bytes)
            else:
                print_message(console, message, is_bytes)


async def main(url: str, is_json: bool) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, listen_messages, url, is_json)
        nursery.start_soon(signal_handler, nursery.cancel_scope)


@click.command()
@url_argument
@click.option('-j', '--json', 'is_json', is_flag=True)
def listen(url: str, is_json: bool):
    """Listens messages on a given URL."""
    trio.run(main, url, is_json)
