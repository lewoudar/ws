import json
from datetime import datetime
from typing import AnyStr

import click
import trio
from rich.console import Console
from rich.markup import escape

from ws.client import websocket_client
from ws.console import configure_console_recording, console, save_output
from ws.options import duration_option, filename_option, url_argument
from ws.settings import get_settings
from ws.utils.io import function_runner, signal_handler, sleep_until


def trace_rule(terminal: Console, is_bytes: bool) -> None:
    date = datetime.now()
    message_type = 'BINARY' if is_bytes else 'TEXT'

    terminal.rule(f'[bold info]{message_type} message on {date:%Y-%m-%d %H:%M:%S}')


def print_message(terminal: Console, message: AnyStr, is_bytes: bool) -> None:
    if is_bytes:
        terminal.print(message)
    else:
        terminal.print(escape(message))


def print_json(terminal: Console, message: AnyStr, is_bytes: bool) -> None:
    if is_bytes:
        try:
            message = message.decode()
        except UnicodeError:
            terminal.print(message)
            return
    try:
        terminal.print_json(escape(message))
    except json.JSONDecodeError:
        terminal.print(escape(message))


async def listen_messages(url: str, is_json: bool, filename: str = None) -> None:
    configure_console_recording(console, get_settings(), filename)

    async with websocket_client(url) as client:
        while True:
            message = await client.get_message()
            is_bytes = isinstance(message, bytes)
            trace_rule(console, is_bytes)

            if is_json:
                print_json(console, message, is_bytes)
            else:
                print_message(console, message, is_bytes)


async def main(url: str, is_json: bool, duration: float = None, filename: str = None) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, listen_messages, url, is_json, filename)
        nursery.start_soon(signal_handler, nursery.cancel_scope)
        nursery.start_soon(sleep_until, nursery.cancel_scope, duration)

    if filename:
        save_output(console, filename)


@click.command()
@url_argument
@click.option('-j', '--json', 'is_json', is_flag=True)
@duration_option
@filename_option
def listen(url: str, is_json: bool, duration: float, filename: str):
    """Listens messages on a given URL."""
    trio.run(main, url, is_json, duration, filename)
