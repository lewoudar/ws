import pytest
from trio_websocket import serve_websocket

from tests.helpers import get_fake_input, server_handler
from ws.commands.session import main
from ws.utils.command import Command


async def test_should_print_general_help_and_exit_program(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('help'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')

    output = capsys.readouterr().out
    # rich auto-detects terminal width and split content in a way I don't understand
    # since some lines of HELP message are too long to fit in a row, I just test a subset of the string I'm sure
    # will be present (in general 60 characters is a sure minimal value)
    assert 'The session program lets you interact with a websocket' in output
    assert '• ping <message>: Sends a ping with an optional message.\n' in output
    assert '• pong <message>: Sends a pong with an optional message.\n' in output
    assert '• text message: Sends text message.\n' in output
    assert '• byte message: Sends byte message.\n' in output
    assert '• close <code> <reason>: Closes the websocket connection' in output
    assert '• quit: equivalent to close 1000.\n' in output


@pytest.mark.parametrize(
    ('input_data', 'message'),
    [('help ping bar', 'Unknown argument: bar\n'), ('help ping foo bar', 'Unknown arguments: foo bar\n')],
)
async def test_should_print_message_unknown_arguments_when_they_are_passed_to_help_sub_command(
    capsys, mocker, nursery, input_data, message
):
    mocker.patch('ws.console.console.input', get_fake_input(input_data))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert message in output


async def test_should_print_list_of_commands_when_unknown_command_is_passed_as_argument(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('help foo'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Unknown command foo, available commands are:\n' in output
    for command in Command:
        if command.value != 'help':
            assert f'• {command.value}\n' in output


async def test_should_print_ping_help_and_exit(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('help ping'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'The ping command sends a PING control frame with an optional' in output
    assert 'Example usage:' in output
    assert 'A random 32 bytes of data will be sent to the server as ping' in output
    assert 'Sends a ping with the message "hello world"' in output
    assert output.count('> ping') == 2
    assert '> ping "hello world"' in output
    assert 'Bye!' in output


async def test_should_print_pong_help_and_exit(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('help pong'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'The pong command sends a PONG control frame with an optional' in output
    assert 'Example usage:' in output
    assert 'An empty pong will be sent on the wire.' in output
    assert 'Sends a pong with the message "hello world"' in output
    assert output.count('> pong') == 2
    assert '> pong "hello world"' in output
    assert 'Bye!' in output


async def test_should_print_quit_help_and_exit(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('help quit'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Exits the session program.' in output
    assert 'Technically it is the equivalent of the following command:' in output
    assert '> close 1000' in output
    assert 'Bye!' in output


async def test_should_print_close_help_and_exit(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('help close'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Closes the session given a code and an optional reason.' in output
    assert 'Example usage:' in output
    assert 'If no code is given, 1000 is considered as default meaning a normal closure.' in output
    assert 'The message length must not be greater than 123 bytes.' in output
    assert 'To know more about close codes, please refer to the RFC' in output
    assert output.count('> close') == 3
    assert 'Bye!' in output


async def test_should_print_text_help_and_exit(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('help text'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Sends a TEXT frame with given data.' in output
    assert 'Example usage:' in output
    assert 'Sends "hello world" in a TEXT frame.' in output
    assert '# foo.txt' in output
    assert 'Hello from Cameroon!' in output
    assert 'Notice the pattern file@ which a necessary prefix to send content from a file.' in output
    assert output.count('> text') == 2
    assert 'Bye!' in output


async def test_should_print_byte_help_and_exit(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('help byte'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Sends a BINARY frame with given data.' in output
    assert 'Example usage:' in output
    assert 'Sends "hello world" in a BINARY frame.' in output
    assert '# foo.txt' in output
    assert 'Hello from Cameroon!' in output
    assert 'Notice the pattern file@ which a necessary prefix to send content from a file.' in output
    assert output.count('> byte') == 2
    assert 'Bye!' in output
