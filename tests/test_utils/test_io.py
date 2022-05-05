import signal

import mock
import trio

from tests.helpers import killer
from ws.utils.io import function_runner, reverse_read_lines, signal_handler, sleep_until


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
        nursery.start_soon(killer, 5)

    # the first test proves that function_runner runs the function passed as second argument
    assert records == ['echo'] * 6
    assert capsys.readouterr().out == signal_message(signal.SIGINT)


class TestSleepUntil:
    """Tests function sleep_until"""

    async def test_should_call_sleep_forever_when_duration_is_none(self, nursery, mocker):
        sleep_mock = mocker.patch('trio.sleep_forever', new=mock.AsyncMock())
        await sleep_until(nursery.cancel_scope, None)

        sleep_mock.assert_awaited_once()

    async def test_should_call_sleep_with_given_duration_then_cancels_nursery(self):
        async with trio.open_nursery() as nursery:
            await sleep_until(nursery.cancel_scope, 0.01)
