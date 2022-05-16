import pytest
from trio_websocket import serve_websocket

from tests.helpers import get_fake_input, server_handler
from ws.commands.session import main


@pytest.mark.parametrize(
    ('input_data', 'message'),
    [('pong foo bar', 'Unknown argument: bar\n'), ('pong foo bar tar', 'Unknown arguments: bar tar\n')],
)
async def test_should_print_unknown_arguments_when_they_are_passed_to_pong_sub_command(
    capsys, mocker, nursery, input_data, message
):
    mocker.patch('ws.console.console.input', get_fake_input(input_data))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert message in output
    assert 'Bye!' in output


async def test_should_print_error_message_when_payload_length_exceeds_125(capsys, mocker, nursery):
    payload = 'a' * 126
    mocker.patch('ws.console.console.input', get_fake_input(f'pong {payload}'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'The message of a PONG must not exceed a length of 125 bytes but you provided' in output
    assert '126' in output
    assert 'Bye!' in output


@pytest.mark.parametrize(
    ('input_data', 'length'), [('pong', 0), ('pong "hello world"', 11), ("pong 'hello world'", 11)]
)
async def test_should_print_success_message_when_pong_is_sent(capsys, mocker, nursery, input_data, length):
    url = 'ws://localhost:1234'
    mocker.patch('ws.console.console.input', get_fake_input(input_data))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main(url)
    output = capsys.readouterr().out
    plural = 's' if length > 1 else ''

    assert f'PONG {url} with {length} byte{plural} of data\n' in output
    assert 'Took' in output
    assert 's to send the PONG.\n\n' in output
    assert 'Bye!' in output
