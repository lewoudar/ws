import pytest
from trio_websocket import serve_websocket

from tests.helpers import get_fake_input, server_handler
from ws.commands.session import main


@pytest.mark.parametrize(
    ('input_data', 'message'),
    [('ping foo bar', 'Unknown argument: bar\n'), ('ping foo bar tar', 'Unknown arguments: bar tar\n')],
)
async def test_should_print_unknown_arguments_when_they_are_passed_to_help_sub_command(
    capsys, mocker, nursery, input_data, message
):
    mocker.patch('ws.console.console.input', get_fake_input(input_data))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert message in output
    assert 'Bye!' in output


async def test_should_print_timeout_message_and_exit_program(capsys, monkeypatch, mocker, nursery):
    url = 'ws://localhost:1234'
    mocker.patch('ws.console.console.input', get_fake_input('ping'))
    # we set a very low response timeout and hope for timeout (I don't have a better idea)
    monkeypatch.setenv('ws_response_timeout', '0.0001')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main(url)
    output = capsys.readouterr().out

    assert f'PING {url} with 32 bytes of data\n' in output
    assert 'Unable to receive pong before configured response timeout (0.0001s).\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize(
    ('input_data', 'length'), [('ping', 32), ('ping "hello world"', 11), ("ping 'hello world'", 11)]
)
async def test_should_print_success_message_when_pong_is_received(capsys, mocker, nursery, input_data, length):
    url = 'ws://localhost:1234'
    mocker.patch('ws.console.console.input', get_fake_input(input_data))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main(url)
    output = capsys.readouterr().out

    assert f'PING {url} with {length} bytes of data\n' in output
    assert 'Took' in output
    assert 's to receive a PONG.\n\n' in output
    assert 'Bye!' in output
