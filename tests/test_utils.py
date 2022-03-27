import signal

import asyncclick as click
import mock
import pytest
import trio
from trio_websocket import ConnectionClosed, DisconnectionTimeout, serve_websocket

from tests.helpers import killer, server_handler
from ws.utils import catch_too_slow_error, function_runner, reverse_read_lines, signal_handler, websocket_client


async def test_should_read_file_in_reverse_order(file_to_read):
    data = [line.decode() async for line in reverse_read_lines(f'{file_to_read}')][::-1]
    assert '\n'.join(data) == file_to_read.read_text()


async def test_should_run_and_kill_given_function_task(autojump_clock, capsys, signal_message):
    records = []

    async def worker():
        while True:
            records.append('echo')
            await trio.sleep(1)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, worker)
        nursery.start_soon(signal_handler, nursery.cancel_scope)
        nursery.start_soon(killer)

    # the first test proves that function_runner runs the function passed as second argument
    assert records == ['echo'] * 6
    assert capsys.readouterr().out == signal_message(signal.SIGINT)


class TestClient:
    """Tests client function."""

    @staticmethod
    async def worker(url):
        async with websocket_client(url) as client:
            await client.send_message('foo')

    async def test_should_print_error_when_unable_to_connect_to_server(self, monkeypatch, capsys, autojump_clock):
        monkeypatch.setenv('ws_connect_timeout', '2')
        url = 'ws://localhost:1234'

        async def echo_handler(request):
            await trio.sleep(3)
            ws = await request.accept()
            while True:
                try:
                    message = await ws.get_message()
                    await ws.send_message(message)
                except ConnectionClosed:
                    break

        with pytest.raises(click.Abort):
            async with trio.open_nursery() as nursery:
                await nursery.start(serve_websocket, echo_handler, '127.0.0.1', 1234, None)
                nursery.start_soon(self.worker, url)

        assert capsys.readouterr().out == f'Unable to connect to {url}\n'

    async def test_should_print_error_when_unable_to_close_connection_on_time(self, mocker, capsys):
        func_mock = mocker.patch('trio_websocket.WebSocketConnection.send_message', new=mock.AsyncMock())
        func_mock.side_effect = DisconnectionTimeout
        url = 'ws://localhost:1234'

        with pytest.raises(click.Abort):
            async with trio.open_nursery() as nursery:
                await nursery.start(serve_websocket, server_handler, '127.0.0.1', 1234, None)
                nursery.start_soon(self.worker, url)

        assert capsys.readouterr().out == f'Unable to disconnect on time from {url}\n'

    async def test_should_print_error_when_connection_is_rejected_by_server(self, capsys):
        url = 'ws://localhost:1234'
        status_code = 400
        headers = [('X-Foo', 'bar')]
        expected_headers = [('x-foo', 'bar'), ('content-length', '9')]
        body = b'You loss!'

        async def reject_handler(request):
            await request.reject(status_code, extra_headers=headers, body=body)

        with pytest.raises(click.Abort):
            async with trio.open_nursery() as nursery:
                await nursery.start(serve_websocket, reject_handler, 'localhost', 1234, None)
                nursery.start_soon(self.worker, url)

        expected = (
            f"Connection was rejected by {url}\n"
            f"status code = {status_code}\n"
            f"headers = {expected_headers}\n"
            f"body = {body.decode()}\n"
        )

        assert capsys.readouterr().out == expected


class TestCatchSlowError:
    """Tests function catch_slow_error."""

    async def test_should_raise_print_error_when_program_raises_timeout_error(self, capsys, autojump_clock):
        @catch_too_slow_error
        async def main():
            with trio.fail_after(2):
                await trio.sleep(3)

        with pytest.raises(click.Abort):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(main)

        assert capsys.readouterr().out == 'Unable to get response on time\n'

    async def test_should_not_print_error_when_program_runs_normally(self, capsys, autojump_clock):
        @catch_too_slow_error
        async def main():
            with trio.fail_after(2):
                await trio.sleep(1)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(main)

        assert capsys.readouterr().out == ''
