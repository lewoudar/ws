import argparse
import enum
from typing import List, Sequence

import trio
from click.parser import split_arg_string
from pydantic.dataclasses import dataclass
from rich.console import Console
from rich.markdown import Markdown
from trio_websocket import WebSocketConnection

from ws.settings import Settings
from ws.utils.documentation import BYTE_HELP, CLOSE_HELP, HELP, PING_HELP, PONG_HELP, QUIT_HELP, TEXT_HELP


@dataclass(frozen=True)
class CommandHelper:
    name: str
    args: List[str]


class Command(str, enum.Enum):
    QUIT = 'quit'
    CLOSE = 'close'
    PING = 'ping'
    PONG = 'pong'
    TEXT = 'text'
    BYTE = 'byte'
    HELP = 'help'


def parse_command(command: str) -> CommandHelper:
    args = split_arg_string(command)
    return CommandHelper(args[0], args[1:])


def plural_form(sequence: Sequence) -> str:
    return 's' if len(sequence) > 1 else ''


def handle_unknown_arguments(unknown_arguments: List[str], terminal: Console) -> None:
    arguments = ' '.join(unknown_arguments)
    terminal.print(f'Unknown argument{plural_form(unknown_arguments)}: [warning]{arguments}[/]')


def handle_help_command(arguments: List[str], terminal: Console) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='?')
    obj, unknown_arguments = parser.parse_known_args(arguments)
    if unknown_arguments:
        handle_unknown_arguments(unknown_arguments, terminal)
        return

    if obj.command is None:
        terminal.print(HELP)
        return

    commands = [command.value for command in Command if command.value != 'help']
    if obj.command not in commands:
        terminal.print(f'Unknown command [error]{obj.command}[/], available commands are:')
        for command in commands:
            terminal.print(f'• [info]{command}')
        return

    help_messages = {
        Command.PING.value: PING_HELP,
        Command.PONG.value: PONG_HELP,
        Command.QUIT.value: QUIT_HELP,
        Command.CLOSE.value: CLOSE_HELP,
        Command.TEXT.value: TEXT_HELP,
        Command.BYTE.value: BYTE_HELP,
    }

    for key, value in help_messages.items():
        if key == obj.command:
            terminal.print(Markdown(value))
            return


async def handle_ping_command(
    url: str, arguments: List[str], terminal: Console, client: WebSocketConnection, settings: Settings
) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('message', nargs='?')
    obj, unknown_arguments = parser.parse_known_args(arguments)
    if unknown_arguments:
        handle_unknown_arguments(unknown_arguments, terminal)
        return

    # trio_websocket by default sends 32 bytes if no payload is given
    if obj.message is None:
        payload_length = 32
        message = None
    else:
        message = obj.message.encode()
        payload_length = len(message)

    plural = 's' if payload_length > 1 else ''
    terminal.print(f'PING {url} with {payload_length} byte{plural} of data')

    beginning = trio.current_time()
    with trio.move_on_after(settings.response_timeout) as scope:
        await client.ping(message)
        duration = trio.current_time() - beginning

    if scope.cancelled_caught:
        terminal.print(
            f'[warning]Unable to receive pong before configured response timeout'
            f' ([/][number]{settings.response_timeout}[/][warning]s).\n'
        )
    else:
        terminal.print(f'Took [number]{duration:.2f}[/]s to receive a PONG.\n')
