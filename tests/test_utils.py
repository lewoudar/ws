import signal

import trio

from tests.helpers import killer
from ws.utils import function_runner, reverse_read_lines, signal_handler


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
