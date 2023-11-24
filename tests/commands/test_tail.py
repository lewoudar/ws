from __future__ import annotations

import pathlib
import platform
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


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason="I don't know why it doesn't work on pypy")
async def test_should_follow_given_file(capsys, file_to_read, signal_message):
    async def update_file(file_path: pathlib.Path) -> None:
        async with await trio.open_file(file_path, 'a') as f:
            await trio.sleep(0.2)
            await f.write('hello\n')
            await trio.sleep(0.3)
            await f.write('world\n')

    async with trio.open_nursery() as nursery:
        nursery.start_soon(main, file_to_read, 10, True)
        nursery.start_soon(killer, 1)
        await update_file(file_to_read)

    expected = 'I like async concurrency!\n' * 9 + f'\nhello\nworld\n{signal_message(signal.SIGINT)}'
    # Windows magic!
    if platform.system() == 'Windows':
        expected = expected.replace('I like async concurrency!\n', 'I like async concurrency!\r\n')

    assert capsys.readouterr().out == expected


@pytest.mark.parametrize('follow_option', ['-f', '--follow'])
def test_should_check_trio_run_is_correctly_called_with_arguments(runner, mocker, file_to_read, follow_option):
    run_mock = mocker.patch('trio.run')
    result = runner.invoke(cli, ['tail', f'{file_to_read}', '-n', '12', follow_option])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, f'{file_to_read}', 12, True)
