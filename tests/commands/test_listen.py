import json

import pytest
import trio
from trio_websocket import ConnectionClosed, WebSocketRequest, serve_websocket

from ws.commands.listen import main, print_json, print_message, trace_rule
from ws.main import cli


class TestTraceRule:
    """Tests function trace_rule."""

    @pytest.mark.parametrize(('is_bytes', 'message_type'), [(False, 'TEXT'), (True, 'BINARY')])
    def test_should_print_rule_and_message(self, test_console, mocker, is_bytes, message_type):
        mocker.patch('trio.current_time', return_value=1_649_959_800)
        trace_rule(test_console, is_bytes=is_bytes)

        assert f'─ {message_type} message at 2022-04-14 20:10:00 ─' in test_console.file.getvalue()


class TestPrintMessage:
    """Tests function print_message."""

    @pytest.mark.parametrize(
        ('is_bytes', 'message', 'expected'), [(True, b'hello', "b'hello'\n"), (False, 'hello', 'hello\n')]
    )
    def test_should_print_message_for_any_string(self, test_console, is_bytes, message, expected):
        print_message(test_console, message, is_bytes)

        assert expected == test_console.file.getvalue()


class TestPrintJson:
    """Tests function print_json."""

    @pytest.mark.parametrize(
        ('is_bytes', 'message', 'expected'),
        [
            (True, b'{"hello": "world"}', '{\n  "hello": "world"\n}\n'),
            (True, b"{'hello': 'world'}", "{'hello': 'world'}\n"),
            (True, b'\x81', "b'\\x81'\n"),
            (False, '{"hello": "world"}', '{\n  "hello": "world"\n}\n'),
        ],
    )
    def test_should_print_input_for_any_string(self, test_console, is_bytes, message, expected):
        print_json(test_console, message, is_bytes)

        assert expected == test_console.file.getvalue()


# command tests


async def handler(request: WebSocketRequest) -> None:
    ws = await request.accept()
    message = json.dumps({'hello': 'world'})
    while True:
        try:
            await ws.send_message(message)
            await ws.send_message(message.encode())
            await trio.sleep(0.1)
        except ConnectionClosed:
            break


def test_should_print_error_when_url_argument_is_not_given(runner):
    result = runner.invoke(cli, ['listen'])

    assert result.exit_code == 2
    assert "Missing argument 'URL'" in result.output


async def test_should_read_incoming_messages_with_json_flag(nursery, capsys):
    await nursery.start(serve_websocket, handler, 'localhost', 1234, None)
    with trio.move_on_after(1):
        await main('ws://localhost:1234', True)

    output = capsys.readouterr().out
    assert output.count('─ TEXT message at') == 10
    assert output.count('─ BINARY message at') == 10
    assert output.count('{\n  "hello": "world"\n}\n') == 20


async def test_should_read_incoming_messages_without_json_flag(nursery, capsys):
    await nursery.start(serve_websocket, handler, 'localhost', 1234, None)
    with trio.move_on_after(1):
        await main('ws://localhost:1234', False)

    output = capsys.readouterr().out
    assert output.count('─ TEXT message at') == 10
    assert output.count('{"hello": "world"}\n') == 10
    assert output.count('─ BINARY message at') == 10
    assert output.count('b\'{"hello": "world"}\'\n') == 10


def test_should_check_trio_is_correctly_called_without_options(runner, mocker):
    run_mock = mocker.patch('trio.run')
    result = runner.invoke(cli, ['listen', 'ws://localhost:1234'])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, 'ws://localhost:1234', False)


@pytest.mark.parametrize('json_option', ['-j', '--json'])
def test_should_check_trio_is_correctly_called_with_options(runner, mocker, json_option):
    run_mock = mocker.patch('trio.run')
    result = runner.invoke(cli, ['listen', 'ws://localhost:1234', json_option])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, 'ws://localhost:1234', True)
