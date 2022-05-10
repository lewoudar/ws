import argparse
import enum
import re
from typing import List

from pydantic.dataclasses import dataclass
from rich.console import Console
from rich.markdown import Markdown

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
    raw = re.split(r'\W+', command)
    args = [item for item in raw if item]
    return CommandHelper(args[0], args[1:])


def handle_help_command(arguments: List[str], terminal: Console) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='?')
    obj, unknown_arguments = parser.parse_known_args(arguments)
    if unknown_arguments:
        plural = 's' if len(unknown_arguments) > 1 else ''
        arguments = ' '.join(unknown_arguments)
        terminal.print(f'Unknown argument{plural}: [warning]{arguments}[/]')
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
