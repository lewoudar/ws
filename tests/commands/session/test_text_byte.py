import platform

import pytest
from trio_websocket import serve_websocket

from tests.helpers import server_handler
from ws.commands.session import main


@pytest.mark.parametrize(
    ('input_data', 'message'),
    [
        ('text foo bar', 'Unknown argument: bar\n'),
        ('text foo bar tar', 'Unknown arguments: bar tar\n'),
        ('byte foo bar', 'Unknown argument: bar\n'),
        ('byte foo bar tar', 'Unknown arguments: bar tar\n'),
    ],
)
async def test_should_print_unknown_arguments_when_they_are_passed_to_sub_command(
    capsys, nursery, mock_input, input_data, message
):
    mock_input.send_text(f'{input_data}\nquit\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert message in output
    assert 'Bye!' in output


@pytest.mark.parametrize('command', ['text', 'byte'])
async def test_should_print_error_message_when_no_data_is_passed_to_sub_command(capsys, nursery, mock_input, command):
    mock_input.send_text(f'{command}\nquit\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'The message is mandatory.\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('command', ['text', 'byte'])
async def test_should_print_error_when_given_file_does_not_exist(capsys, nursery, mock_input, command):
    mock_input.send_text(f'{command} file@foo.txt\nquit\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'file foo.txt does not exist\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('command', ['text', 'byte'])
async def test_should_send_raw_message_and_print_its_length(capsys, nursery, mock_input, command):
    mock_input.send_text(f'{command} "hello world"\nquit\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Sent 11.0 B of data over the wire.\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('command', ['text', 'byte'])
@pytest.mark.skipif(
    platform.system() == 'Windows',
    reason='for an unknown reason, the temporary file is not created as expected on windows runner',
)
async def test_should_send_message_in_file_and_print_its_length(capsys, tmp_path, nursery, mock_input, command):
    file_path = tmp_path / 'file.txt'
    file_path.write_text('hello world')
    mock_input.send_text(f'{command} file@{file_path}\nquit\n')

    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Sent 11.0 B of data over the wire.\n' in output
    assert 'Bye!' in output
