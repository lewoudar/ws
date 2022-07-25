import os
import platform
import subprocess

import pytest
import shellingham

from ws.commands.completion import SHELLS, install_powershell
from ws.main import cli


class TestInstallPowershell:
    """Tests function install_powershell"""

    @pytest.mark.parametrize('shell', ['powershell', 'pwsh'])
    def test_should_print_error_when_unable_to_get_path_to_completion_script(self, capsys, mocker, shell):
        def fake_subprocess_run(command_args, *_, **_k):
            if command_args[1] != '-NoProfile':
                return
            raise subprocess.CalledProcessError(returncode=1, cmd='pwsh')

        with pytest.raises(SystemExit):
            mocker.patch('subprocess.run', side_effect=fake_subprocess_run)
            install_powershell(shell)  # type: ignore

    @pytest.mark.parametrize('shell', ['powershell', 'pwsh'])
    def test_should_create_or_update_user_profile(self, tmp_path, mocker, shell):
        user_profile_path = tmp_path / 'WindowsPowerShell' / 'Microsoft.PowerShell_profile.ps1'

        def fake_subprocess_run(command_args, *_, **_k):
            if command_args[1] == '-NoProfile':
                return subprocess.CompletedProcess(command_args, 0, bytes(user_profile_path), None)

        mocker.patch(
            'shellingham.detect_shell',
            return_value=(shell, f'C:\\Windows\\System32\\WindowsPowershell\\v1.0\\{shell}.exe'),
        )
        mocker.patch('subprocess.run', side_effect=fake_subprocess_run)
        install_powershell(shell)  # type: ignore

        # check user profile file
        assert user_profile_path.is_file()

        content = user_profile_path.read_text()
        assert content.startswith('Import-Module PSReadLine')
        assert '$Env:_WS_COMPLETE = "complete_powershell"' in content
        assert 'ws | ForEach-Object {' in content
        assert content.endswith('Register-ArgumentCompleter -Native -CommandName ws -ScriptBlock $scriptblock\n')


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
    mocker.patch('shellingham.detect_shell', return_value=('cmd', 'C:\\bin\\cmd.exe'))
    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 1
    shells_string = ', '.join(SHELLS[:-1])
    assert f'Your shell is not supported. Shells supported are: {shells_string}' in result.output
    assert result.output.endswith('pwsh\n')


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
    assert content.endswith('compdef _ws_completion ws;\n\n')

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


@pytest.mark.skipif(platform.system() in ['Darwin', 'Linux'], reason='powershell is not supported on these OS')
@pytest.mark.parametrize('shell', ['powershell', 'pwsh'])
def test_should_create_completion_script_and_add_it_in_powershell_profile(tmp_path, mocker, runner, shell):
    user_profile_path = tmp_path / 'WindowsPowerShell' / 'Microsoft.PowerShell_profile.ps1'

    def fake_subprocess_run(command_args, *_, **_k):
        if command_args[1] == '-NoProfile':
            return subprocess.CompletedProcess(command_args, 0, bytes(user_profile_path), None)

    mocker.patch('subprocess.run', side_effect=fake_subprocess_run)

    result = runner.invoke(cli, ['install-completion'])

    assert result.exit_code == 0
    assert 'Successfully installed completion script!\n' in result.output

    # check user profile file
    assert user_profile_path.is_file()

    content = user_profile_path.read_text()
    assert content.startswith('Import-Module PSReadLine')
    assert content.endswith('Register-ArgumentCompleter -Native -CommandName ws -ScriptBlock $scriptblock\n')
