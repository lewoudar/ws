import argparse
import enum
from typing import List, Sequence

import click
import trio
from click.parser import split_arg_string
from pydantic.dataclasses import dataclass
from rich.console import Console
from rich.markdown import Markdown
from trio_websocket import WebSocketConnection

from ws.parameters import get_normalized_message
from ws.settings import Settings
from ws.utils.documentation import BYTE_HELP, CLOSE_HELP, HELP, PING_HELP, PONG_HELP, QUIT_HELP, TEXT_HELP
from ws.utils.size import get_readable_size


@dataclass(frozen=True)
class CommandHelper:
    name: str
    args: List[str]


class CustomConfig:
    arbitrary_types_allowed = True


@dataclass(frozen=True, config=CustomConfig)
class NamespaceData:
    obj: argparse.Namespace
    unknown_arguments: List[str]


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


def get_namespace_data(arguments: List[str], argument: str, nargs: str = '?') -> NamespaceData:
    parser = argparse.ArgumentParser()
    parser.add_argument(argument, nargs=nargs)
    return NamespaceData(*parser.parse_known_args(arguments))


def print_unknown_command_message(unknown_command: str, commands: List[str], terminal: Console) -> None:
    terminal.print(f'Unknown command [error]{unknown_command}[/], available commands are:')
    for command in commands:
        terminal.print(f'• [info]{command}')
    terminal.print()


def handle_help_command(arguments: List[str], terminal: Console) -> None:
    namespace_data = get_namespace_data(arguments, 'command')
    if namespace_data.unknown_arguments:
        handle_unknown_arguments(namespace_data.unknown_arguments, terminal)
        return

    if namespace_data.obj.command is None:
        terminal.print(HELP)
        return

    commands = [command.value for command in Command if command.value != 'help']
    if namespace_data.obj.command not in commands:
        print_unknown_command_message(namespace_data.obj.command, commands, terminal)
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
        if key == namespace_data.obj.command:
            terminal.print(Markdown(value))
            return


async def handle_ping_command(
    url: str, arguments: List[str], terminal: Console, client: WebSocketConnection, settings: Settings
) -> None:
    namespace_data = get_namespace_data(arguments, 'message')
    if namespace_data.unknown_arguments:
        handle_unknown_arguments(namespace_data.unknown_arguments, terminal)
        return

    # trio_websocket by default sends 32 bytes if no payload is given
    if namespace_data.obj.message is None:
        payload_length = 32
        message = None
    else:
        message = namespace_data.obj.message.encode()
        payload_length = len(message)

    if payload_length > 125:
        terminal.print(
            '[error]The message of a PING must not exceed a length'
            f' of [number]125[/] bytes but you provided [number]{payload_length}[/] bytes.\n'
        )
        return

    plural = 's' if payload_length > 1 else ''
    terminal.print(f'PING {url} with {payload_length} byte{plural} of data')

    beginning = trio.current_time()
    with trio.move_on_after(settings.response_timeout) as scope:
        await client.ping(message)
        duration = trio.current_time() - beginning

    if scope.cancelled_caught:
        terminal.print(
            f'[warning]Unable to receive pong before configured response timeout'
            f' ([/][number]{settings.response_timeout}[/]s).\n'
        )
    else:
        terminal.print(f'Took [number]{duration:.2f}s[/] to receive a PONG.\n')


async def handle_pong_command(url: str, arguments: List[str], terminal: Console, client: WebSocketConnection) -> None:
    namespace_data = get_namespace_data(arguments, 'message')
    if namespace_data.unknown_arguments:
        handle_unknown_arguments(namespace_data.unknown_arguments, terminal)
        return

    if namespace_data.obj.message is None:
        message = b''
        payload_length = 0
    else:
        message = namespace_data.obj.message.encode()
        payload_length = len(message)

    if payload_length > 125:
        terminal.print(
            '[error]The message of a PONG must not exceed a length'
            f' of [number]125[/] bytes but you provided [number]{payload_length}[/] bytes.\n'
        )
        return

    plural = 's' if payload_length > 1 else ''
    terminal.print(f'PONG {url} with {payload_length} byte{plural} of data')

    before = trio.current_time()
    await client.pong(message)
    duration = trio.current_time() - before
    terminal.print(f'Took [number]{duration:.2f}s[/] to send the PONG.\n')


async def handle_data_command(
    arguments: List[str], terminal: Console, client: WebSocketConnection, is_byte: bool = False
) -> None:
    namespace_data = get_namespace_data(arguments, 'message')
    if namespace_data.unknown_arguments:
        handle_unknown_arguments(namespace_data.unknown_arguments, terminal)
        return

    if namespace_data.obj.message is None:
        terminal.print('[error]The message is mandatory.\n')
        return

    try:
        message = get_normalized_message(namespace_data.obj.message, is_bytes=is_byte)
    except click.BadParameter as e:
        terminal.print(f'[error]{e.message}\n')
        return

    await client.send_message(message)
    length = len(message)
    terminal.print(f'Sent [number]{get_readable_size(length)}[/] of data over the wire.\n')


async def handle_close(arguments: List[str], terminal: Console, client: WebSocketConnection) -> bool:
    parser = argparse.ArgumentParser()
    parser.add_argument('code', default='1000')
    parser.add_argument('reason', nargs='?')
    obj, unknown_arguments = parser.parse_known_args(arguments)
    if unknown_arguments:
        handle_unknown_arguments(unknown_arguments, terminal)
        return False

    try:
        code = int(obj.code)
    except ValueError:
        terminal.print(f'[error]code "{obj.code}" is not an integer.\n')
        return False

    if not 0 <= code < 5000:
        terminal.print(f'[error]code {code} is not in the range [0, 4999].\n')
        return False

    if obj.reason is not None and len(obj.reason) > 123:
        terminal.print(
            '[error]reason must not exceed a length of [number]123[/]'
            f' bytes but you provided [number]{len(obj.reason)}[/] bytes.\n'
        )
        return False

    await client.aclose(code, obj.reason)  # type: ignore
    return True
