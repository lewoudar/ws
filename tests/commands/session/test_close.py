import pytest
from trio_websocket import serve_websocket

from tests.helpers import get_fake_input, server_handler
from ws.commands.session import main


@pytest.mark.parametrize(
    ('input_data', 'message'),
    [
        ('close 1000 reason bar', 'Unknown argument: bar\n'),
        ('close 1000 reason bar tar', 'Unknown arguments: bar tar\n'),
    ],
)
async def test_should_print_unknown_arguments_when_they_are_passed_to_close_sub_command(
    capsys, mocker, nursery, input_data, message
):
    mocker.patch('ws.console.console.input', get_fake_input(input_data))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert message in output
    assert 'Bye!' in output


async def test_should_print_error_message_when_code_is_not_an_integer(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', get_fake_input('close foo reason'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'code "foo" is not an integer.\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('code', [-1, 5000])
async def test_should_print_error_message_when_code_is_not_valid_range(capsys, mocker, nursery, code):
    mocker.patch('ws.console.console.input', get_fake_input(f'close {code} reason'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert f'code {code} is not in the range [0, 4999].\n' in output
    assert 'Bye!' in output


async def test_should_print_error_message_when_reason_length_exceeds_123(capsys, mocker, nursery):
    reason = 'a' * 124
    mocker.patch('ws.console.console.input', get_fake_input(f'close 1000 {reason}'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'reason must not exceed a length of 123 bytes but you provided 124 bytes.\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('input_data', ['1002', '1002 reason'])
async def test_should_close_client_and_exit(capsys, mocker, nursery, input_data):
    mocker.patch('ws.console.console.input', get_fake_input(f'close {input_data}'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Bye!' in output
