import functools
import platform

import pytest
import trio
from trio_websocket import ConnectionRejected, WebSocketRequest, serve_websocket

from ws.commands.text_byte import main
from ws.main import cli


async def handler(request: WebSocketRequest, messages: set) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            messages.add(message)
        except ConnectionRejected:
            break


@pytest.mark.parametrize('message', [b'hello', 'hello'])
@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason="I don't know why it does not work on pypy")
async def test_should_send_given_message(capsys, nursery, message):
    messages = set()
    await nursery.start(serve_websocket, functools.partial(handler, messages=messages), 'localhost', 1234, None)
    with trio.move_on_after(0.1):
        await main('ws://localhost:1234', message)

    assert messages == {message}
    assert capsys.readouterr().out == 'Sent 5.0 B of data over the wire.\n'


@pytest.mark.parametrize(('command', 'expected'), [('byte', b'hello'), ('text', 'hello')])
def test_should_check_trio_run_is_correctly_called_with_given_message(runner, mocker, command, expected):
    run_mock = mocker.patch('trio.run')
    url = 'ws://localhost:1234'
    message = 'hello'
    result = runner.invoke(cli, [command, url, message])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, url, expected)


@pytest.mark.parametrize(('command', 'expected'), [('byte', b'hello'), ('text', 'hello')])
def test_should_check_trio_run_is_correctly_called_with_given_file(tmp_path, runner, mocker, command, expected):
    run_mock = mocker.patch('trio.run')
    url = 'ws://localhost:1234'
    dummy_path = tmp_path / 'dummy.txt'
    dummy_path.write_text('hello')
    result = runner.invoke(cli, [command, url, f'file@{dummy_path}'])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, url, expected)
