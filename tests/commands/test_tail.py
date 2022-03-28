from __future__ import annotations

import pathlib
import signal

import pytest
import trio

from tests.helpers import killer
from ws.commands.tail import main
from ws.main import cli


def test_should_print_error_when_argument_is_not_given(runner):
    result = runner.invoke(cli, ['tail'])

    assert result.exit_code == 2
    assert "Missing argument 'FILENAME'" in result.output


def test_should_print_error_when_argument_is_not_a_file(runner):
    result = runner.invoke(cli, ['tail', 'foo'])

    assert result.exit_code == 2
    assert "File 'foo' does not exist" in result.output


def test_should_print_error_when_lines_option_does_not_have_the_correct_type(runner):
    result = runner.invoke(cli, ['tail', '-n', 'foo'])

    assert result.exit_code == 2
    assert "'foo' is not a valid integer range" in result.output


def test_should_print_error_when_lines_option_value_is_out_of_range(runner):
    result = runner.invoke(cli, ['tail', '-n', 0])

    assert result.exit_code == 2
    assert '0 is not in the range x>=1'


def test_should_print_the_last_default_lines_of_given_file(runner, file_to_read):
    result = runner.invoke(cli, ['tail', f'{file_to_read}'])

    assert result.exit_code == 0
    assert 'I like async concurrency!\n' * 9 + '\n' == result.output


def test_should_print_the_last_given_number_of_lines_of_a_file(runner, file_to_read):
    count = 15
    result = runner.invoke(cli, ['tail', f'{file_to_read}', '-n', 15])

    assert result.exit_code == 0
    assert 'I like async concurrency!\n' * (count - 1) + '\n' == result.output


@pytest.mark.skip()
async def test_should_follow_given_file(capsys, file_to_read, autojump_clock, signal_message):
    # TODO: understand why this test does not work as expected
    async def update_file(file_path: pathlib.Path) -> None:
        async with await trio.open_file(file_path, 'a') as f:
            await trio.sleep(1)
            await f.write('hello\n')
            await trio.sleep(1)
            await f.write('world\n')

    async with trio.open_nursery() as nursery:
        nursery.start_soon(main, file_to_read, 10, True)
        nursery.start_soon(update_file, file_to_read)
        nursery.start_soon(killer)

    expected = 'I like async concurrency\n' * 9 + f'\nhello\nworld\n{signal_message(signal.SIGINT)}'
    assert capsys.readouterr().out == expected
