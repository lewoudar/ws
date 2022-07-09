import pytest
from trio_websocket import serve_websocket

from tests.helpers import server_handler
from ws.commands.session import main


@pytest.mark.parametrize(
    ('input_data', 'message'),
    [
        ('close 1000 reason bar', 'Unknown argument: bar\n'),
        ('close 1000 reason bar tar', 'Unknown arguments: bar tar\n'),
    ],
)
async def test_should_print_unknown_arguments_when_they_are_passed_to_close_sub_command(
    capsys, nursery, mock_input, input_data, message
):
    mock_input.send_text(f'{input_data}\nquit\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert message in output
    assert 'Bye!' in output


async def test_should_print_error_message_when_code_is_not_an_integer(capsys, nursery, mock_input):
    mock_input.send_text('close foo reason\nquit\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'code "foo" is not an integer.\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('code', [-1, 5000])
async def test_should_print_error_message_when_code_is_not_valid_range(capsys, nursery, mock_input, code):
    mock_input.send_text(f'close {code} reason\nquit\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert f'code {code} is not in the range [0, 4999].\n' in output
    assert 'Bye!' in output


async def test_should_print_error_message_when_reason_length_exceeds_123(capsys, nursery, mock_input):
    reason = 'a' * 124
    mock_input.send_text(f'close 1000 {reason}\nquit\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'reason must not exceed a length of 123 bytes but you provided 124 bytes.\n' in output
    assert 'Bye!' in output


@pytest.mark.parametrize('input_data', ['1002', '1002 reason'])
async def test_should_close_client_and_exit(capsys, nursery, mock_input, input_data):
    mock_input.send_text(f'close {input_data}\n')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Bye!' in output
