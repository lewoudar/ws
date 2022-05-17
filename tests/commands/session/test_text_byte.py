import pytest
from trio_websocket import serve_websocket

from tests.helpers import get_fake_input, server_handler
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
    capsys, mocker, nursery, input_data, message
):
    mocker.patch('ws.console.console.input', get_fake_input(input_data))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert message in output
    assert 'Bye!' in output


@pytest.mark.parametrize('command', ['text', 'byte'])
async def test_should_print_error_message_when_no_data_is_passed_to_sub_command(capsys, mocker, nursery, command):
    mocker.patch('ws.console.console.input', get_fake_input(command))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'The message is mandatory.\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('command', ['text', 'byte'])
async def test_should_print_error_when_given_file_does_not_exist(capsys, mocker, nursery, command):
    mocker.patch('ws.console.console.input', get_fake_input(f'{command} file@foo.txt'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'file foo.txt does not exist\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('command', ['text', 'byte'])
async def test_should_send_raw_message_and_print_its_length(capsys, mocker, nursery, command):
    mocker.patch('ws.console.console.input', get_fake_input(f'{command} "hello world"'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Sent 11.0 B of data over the wire.\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('command', ['text', 'byte'])
async def test_should_send_message_in_file_and_print_its_length(capsys, tmp_path, mocker, nursery, command):
    file_path = tmp_path / 'file.txt'
    file_path.write_text('hello world')
    mocker.patch('ws.console.console.input', get_fake_input(f'{command} file@{file_path}'))

    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Sent 11.0 B of data over the wire.\n' in output
    assert 'Bye!' in output
