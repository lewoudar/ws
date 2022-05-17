import click
import trio

from ws.client import websocket_client
from ws.console import configure_console_recording, console, save_output
from ws.options import filename_option, url_argument
from ws.settings import get_settings
from ws.utils.command import (
    Command,
    handle_close,
    handle_data_command,
    handle_help_command,
    handle_ping_command,
    handle_pong_command,
    parse_command,
    print_unknown_command_message,
)
from ws.utils.decorators import catch_pydantic_error
from ws.utils.documentation import INTRODUCTION
from ws.utils.io import function_runner, signal_handler


@catch_pydantic_error
async def interact(url: str, filename: str = None) -> None:
    settings = get_settings()
    if filename:
        configure_console_recording(console, settings, filename)

    console.print(INTRODUCTION)
    good_bye_message = '[info]Bye! :waving_hand:'
    async with websocket_client(url) as client:
        while True:
            try:
                user_input = console.input('[bold][prompt]>[/][/] ')
                user_input = user_input.strip()
                if not user_input:
                    continue

                command = parse_command(user_input)
                if command.name == Command.QUIT.value:
                    console.print(good_bye_message)
                    break

                elif command.name == Command.CLOSE.value:
                    ok = await handle_close(command.args, console, client)
                    if ok:
                        console.print(good_bye_message)
                        break

                elif command.name == Command.HELP.value:
                    handle_help_command(command.args, console)

                elif command.name == Command.PING.value:
                    await handle_ping_command(url, command.args, console, client, settings)

                elif command.name == Command.PONG.value:
                    await handle_pong_command(url, command.args, console, client)

                elif command.name == Command.TEXT.value:
                    await handle_data_command(command.args, console, client)

                elif command.name == Command.BYTE.value:
                    await handle_data_command(command.args, console, client, is_byte=True)

                else:
                    commands = [command.value for command in Command]
                    print_unknown_command_message(command.name, commands, console)
            except EOFError:
                console.print(good_bye_message)
                break


async def main(url: str, filename: str = None) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, interact, url, filename)
        nursery.start_soon(signal_handler, nursery.cancel_scope)

    if filename:
        save_output(console, filename)


@click.command()
@url_argument
@filename_option
def session(url: str, filename: str):
    """Opens an interactive session to communicate with endpoint located at URL."""
    trio.run(main, url, filename)
