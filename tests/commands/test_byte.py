import functools

import trio
from trio_websocket import ConnectionRejected, WebSocketRequest, serve_websocket

from ws.commands.byte import main
from ws.main import cli


async def handler(request: WebSocketRequest, messages: set) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            messages.add(message)
        except ConnectionRejected:
            break


async def test_should_send_given_message(nursery):
    messages = set()
    await nursery.start(serve_websocket, functools.partial(handler, messages=messages), 'localhost', 1234, None)
    with trio.move_on_after(0.5):
        await main('ws://localhost:1234', b'hello')

    assert messages == {b'hello'}


def test_should_check_trio_run_is_correctly_called_with_given_message(runner, mocker):
    run_mock = mocker.patch('trio.run')
    url = 'ws://localhost:1234'
    message = 'hello'
    result = runner.invoke(cli, ['byte', url, message])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, url, message.encode())


def test_should_check_trio_run_is_correctly_called_with_given_file(tmp_path, runner, mocker):
    run_mock = mocker.patch('trio.run')
    url = 'ws://localhost:1234'
    message = b'hello'
    dummy_path = tmp_path / 'dummy.txt'
    dummy_path.write_bytes(message)
    result = runner.invoke(cli, ['byte', url, f'file@{dummy_path}'])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, url, message)
