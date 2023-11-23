import os
import platform
import subprocess

import pytest
import shellingham

from ws.commands.completion import SHELLS
from ws.main import cli


def test_should_print_error_when_shell_is_not_detected(mocker, runner):
    mocker.patch('shellingham.detect_shell', side_effect=shellingham.ShellDetectionFailure)
    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 1
    assert 'Unable to detect the current shell.\n' == result.output


def test_should_print_error_when_os_name_is_unknown(monkeypatch, runner):
    os_name = 'foo'
    monkeypatch.setattr(os, 'name', os_name)
    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 1
    assert os_name in result.output


def test_should_print_error_if_shell_is_not_supported(mocker, runner):
    mocker.patch('shellingham.detect_shell', return_value=('pwsh', 'C:\\bin\\pwsh'))
    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 1
    shells_string = ', '.join(SHELLS)
    assert f'Your shell is not supported. Shells supported are: {shells_string}\n' == result.output


@pytest.mark.parametrize('shell', [('bash', '/bin/bash'), ('zsh', '/bin/zsh'), ('fish', '/bin/fish')])
def test_should_print_error_when_user_cannot_retrieve_completion_script(tmp_path, mocker, runner, shell):
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('shellingham.detect_shell', return_value=shell)
    mocker.patch('subprocess.run', side_effect=subprocess.CalledProcessError(returncode=1, cmd='ws'))
    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 1
    assert 'Unable to get completion script for ws cli.\n' == result.output


@pytest.mark.skipif(platform.system() in ['Darwin', 'Windows'], reason='bash not supported on these OS')
def test_should_create_completion_file_and_install_it_for_bash_shell(tmp_path, mocker, runner):
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('shellingham.detect_shell', return_value=('bash', '/bin/bash'))
    cli_completion_dir = tmp_path / '.cli_completions'
    completion_file = cli_completion_dir / 'ws-complete.bash'
    bashrc_file = tmp_path / '.bashrc'

    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 0
    assert 'Successfully installed completion script!\n' in result.output

    # completion files check
    assert cli_completion_dir.is_dir()
    assert completion_file.is_file()
    content = completion_file.read_text()

    assert content.startswith('_ws_completion() {')
    assert content.endswith('_ws_completion_setup;\n\n')

    # .bashrc check
    lines = [line for line in bashrc_file.read_text().split('\n') if line]
    expected = [f'. {cli_completion_dir / "ws-complete.bash"}']
    assert lines == expected


@pytest.mark.skipif(platform.system() == 'Windows', reason='zsh not supported on Windows')
def test_should_create_completion_file_and_install_it_for_zsh_shell(tmp_path, mocker, runner):
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('shellingham.detect_shell', return_value=('zsh', '/bin/zsh'))
    cli_completion_dir = tmp_path / '.cli_completions'
    completion_file = cli_completion_dir / 'ws-complete.zsh'
    zshrc_file = tmp_path / '.zshrc'

    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 0
    assert 'Successfully installed completion script!\n' in result.output

    # completion files check
    assert cli_completion_dir.is_dir()
    assert completion_file.is_file()
    content = completion_file.read_text()

    assert content.startswith('#compdef ws')
    assert content.endswith('compdef _ws_completion ws\nfi\n\n')


    # .zshrc check
    lines = [line for line in zshrc_file.read_text().split('\n') if line]
    assert lines == [f'. {cli_completion_dir / "ws-complete.zsh"}']


@pytest.mark.skipif(platform.system() == 'Windows', reason='fish not supported on Windows')
def test_should_create_completion_file_and_install_it_for_fish_shell(tmp_path, mocker, runner):
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('shellingham.detect_shell', return_value=('fish', '/bin/fish'))
    completion_dir = tmp_path / '.config/fish/completions'

    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 0
    assert 'Successfully installed completion script!\n' in result.output
    assert completion_dir.is_dir()

    completion_file = completion_dir / 'ws.fish'
    assert completion_file.is_file()
    content = completion_file.read_text()
    assert content.startswith('function _ws_completion')
    assert content.endswith('"(_ws_completion)";\n\n')
