import json

import pytest
import trio
from freezegun import freeze_time
from trio_websocket import ConnectionClosed, WebSocketRequest, serve_websocket

from ws.commands.listen import main, print_json, print_message, trace_rule
from ws.main import cli


class TestTraceRule:
    """Tests function trace_rule."""

    @freeze_time('2022-04-14 20:10:00')
    @pytest.mark.parametrize(('is_bytes', 'message_type'), [(False, 'TEXT'), (True, 'BINARY')])
    def test_should_print_rule_and_message(self, test_console, is_bytes, message_type):
        trace_rule(test_console, is_bytes=is_bytes)

        assert f'─ {message_type} message on 2022-04-14 20:10:00 ─' in test_console.file.getvalue()


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


def test_should_print_error_when_duration_is_not_a_float(runner):
    result = runner.invoke(cli, ['listen', 'ws://localhost:1234', '-d', 'foo'])

    assert result.exit_code == 2
    assert 'not a valid float range' in result.output


def test_should_print_error_when_duration_is_not_in_the_valid_range(runner):
    result = runner.invoke(cli, ['listen', 'ws://localhost:1234', '-d', '0'])

    assert result.exit_code == 2
    assert 'is not in the range x>0' in result.output


def test_should_print_error_when_filename_is_not_a_file(tmp_path, runner):
    result = runner.invoke(cli, ['listen', 'ws://localhost:1234', '-f', f'{tmp_path}'])

    assert result.exit_code == 2
    assert 'is a directory' in result.output


async def test_should_read_incoming_messages_with_json_flag(nursery, capsys):
    await nursery.start(serve_websocket, handler, 'localhost', 1234, None)
    with trio.move_on_after(1):
        await main('ws://localhost:1234', True)

    # Depending on the OS where the tests are run, the numbers varies a lot, what I used here is based on the
    # results I have in GitHub actions
    output = capsys.readouterr().out
    assert output.count('─ TEXT message on') in tuple(range(5, 11))
    assert output.count('─ BINARY message on') in tuple(range(5, 11))
    assert output.count('{\n  "hello": "world"\n}\n') in tuple(range(10, 21))


async def test_should_read_incoming_messages_without_json_flag(nursery, capsys):
    await nursery.start(serve_websocket, handler, 'localhost', 1234, None)
    with trio.move_on_after(1):
        await main('ws://localhost:1234', False)

    output = capsys.readouterr().out
    interval = tuple(range(5, 11))

    assert output.count('─ TEXT message on') in interval
    assert output.count('{"hello": "world"}\n') in interval
    assert output.count('─ BINARY message on') in interval
    assert output.count('b\'{"hello": "world"}\'\n') in interval


async def test_should_read_messages_for_a_given_amount_of_time(nursery, capsys):
    await nursery.start(serve_websocket, handler, 'localhost', 1234, None)
    await main('ws://localhost:1234', False, duration=0.5)

    output = capsys.readouterr().out
    interval = tuple(range(3, 6))

    assert output.count('─ TEXT message on') in interval
    assert output.count('{"hello": "world"}\n') in interval
    assert output.count('─ BINARY message on') in interval
    assert output.count('b\'{"hello": "world"}\'\n') in interval


@pytest.mark.parametrize('filename', ['file.txt', 'file.html', 'file.svg'])
@pytest.mark.usefixtures('reset_console')
async def test_should_read_messages_and_save_them_in_a_file(tmp_path, nursery, capsys, filename):
    file_path = tmp_path / filename
    message_interval = tuple(range(3, 6))
    hello_world_interval = tuple(range(6, 11))
    await nursery.start(serve_websocket, handler, 'localhost', 1234, None)
    await main('ws://localhost:1234', False, duration=0.5, filename=f'{file_path}')

    terminal_output = capsys.readouterr().out
    assert terminal_output.count('─ TEXT message on') in message_interval
    assert file_path.exists()

    file_output = file_path.read_text()
    if file_path.suffix == '.svg':
        assert file_output.count('TEXT&#160;message&#160;on') in message_interval
        assert 2 <= file_output.count('BINARY&#160;message&#160;on') in message_interval
    else:
        assert file_output.count('TEXT message on') in message_interval
        assert 2 <= file_output.count('BINARY message on') in message_interval
    assert file_output.count('hello') in hello_world_interval
    assert file_output.count('world') in hello_world_interval


def test_should_check_trio_run_is_correctly_called_without_options(runner, mocker):
    run_mock = mocker.patch('trio.run')
    result = runner.invoke(cli, ['listen', 'ws://localhost:1234'])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, 'ws://localhost:1234', False, None, None)


@pytest.mark.parametrize(
    ('json_option', 'duration_option', 'filename_option'), [('-j', '-d', '-f'), ('--json', '--duration', '--file')]
)
def test_should_check_trio_run_is_correctly_called_with_options(
    runner, mocker, json_option, duration_option, filename_option
):
    run_mock = mocker.patch('trio.run')
    result = runner.invoke(
        cli, ['listen', 'ws://localhost:1234', json_option, duration_option, '2', filename_option, 'record.txt']
    )

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, 'ws://localhost:1234', True, 2.0, 'record.txt')
