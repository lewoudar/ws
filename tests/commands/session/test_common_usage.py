import pytest
from trio_websocket import serve_websocket

from tests.helpers import get_fake_input, server_handler
from ws.commands.session import main
from ws.main import cli


def test_should_print_error_when_url_is_not_given(runner):
    result = runner.invoke(cli, ['session'])

    assert result.exit_code == 2
    assert "Missing argument 'URL'" in result.output


def test_should_print_error_when_filename_is_not_a_file(tmp_path, runner):
    result = runner.invoke(cli, ['session', ':1234', '-f', f'{tmp_path}'])

    assert result.exit_code == 2
    assert 'is a directory' in result.output


async def test_should_exit_program_when_user_makes_a_ctrl_d(capsys, mocker, nursery):
    # Ctrl+D raises an EOFError, so to simulate it, we will raise this error on console.input method
    mocker.patch('ws.console.console.input', side_effect=EOFError)
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234')
    output = capsys.readouterr().out

    assert 'Welcome to the interactive websocket session! 🌟\n' in output
    assert 'For more information about commands, type the help command.\n' in output
    assert 'When you see <> around a word, it means this argument is optional.\n' in output
    assert 'To know more about a particular command type help <command>.\n' in output
    assert 'To close the session, you can type Ctrl+D or the quit command.\n' in output
    assert 'Bye! 👋\n' in output


@pytest.mark.parametrize('filename', ['file.txt', 'file.html', 'file.svg'])
@pytest.mark.usefixtures('reset_console')
async def test_should_print_input_and_save_it_in_a_file(capsys, tmp_path, mocker, nursery, filename):
    file_path = tmp_path / filename
    mocker.patch('ws.console.console.input', get_fake_input('help'))
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234', filename=f'{file_path}')
    terminal_output = capsys.readouterr().out

    assert 'Welcome to the interactive websocket session! 🌟\n' in terminal_output
    assert 'The session program lets you interact with a websocket endpoint' in terminal_output
    assert 'Bye! 👋\n' in terminal_output

    file_output = file_path.read_text()
    assert 'Welcome to the interactive websocket session! 🌟' in file_output
    assert 'The session program lets you interact with a websocket endpoint' in file_output
    assert 'Bye! 👋' in file_output


def test_should_check_trio_run_is_correctly_called_without_options(runner, mocker):
    run_mock = mocker.patch('trio.run')
    url = 'ws://localhost:1234'
    result = runner.invoke(cli, ['session', url])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, url, None)


@pytest.mark.parametrize('filename_option', ['-f', '--file'])
def test_should_check_trio_run_is_correctly_called_with_options(tmp_path, runner, mocker, filename_option):
    run_mock = mocker.patch('trio.run')
    file_path = tmp_path / 'file.txt'
    result = runner.invoke(cli, ['session', ':1234', filename_option, f'{file_path}'])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, 'ws://localhost:1234', f'{file_path}')
