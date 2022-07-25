from __future__ import annotations

import os
import subprocess  # nosec
from pathlib import Path

import click
import shellingham
from click.shell_completion import ShellComplete, add_completion_class
from typing_extensions import Literal

from ws.console import console

SHELLS = ['bash', 'zsh', 'fish', 'powershell', 'pwsh']

# Windows support code is heavily inspired by the typer project
POWERSHELL_COMPLETION_SCRIPT = """
Import-Module PSReadLine
Set-PSReadLineKeyHandler -Chord Tab -Function MenuComplete
$scriptblock = {
    param($wordToComplete, $commandAst, $cursorPosition)
    $Env:%(complete_var)s = "complete_powershell"
    $Env:_CLICK_COMPLETE_ARGS = $commandAst.ToString()
    $Env:_CLICK_COMPLETE_WORD_TO_COMPLETE = $wordToComplete
    %(prog_name)s | ForEach-Object {
        $commandArray = $_ -Split ":::"
        $command = $commandArray[0]
        $helpString = $commandArray[1]
        [System.Management.Automation.CompletionResult]::new(
            $command, $command, 'ParameterValue', $helpString)
    }
    $Env:%(complete_var)s = ""
    $Env:_CLICK_COMPLETE_ARGS = ""
    $Env:_CLICK_COMPLETE_WORD_TO_COMPLETE = ""
}
Register-ArgumentCompleter -Native -CommandName %(prog_name)s -ScriptBlock $scriptblock
"""


class PowerShellComplete(ShellComplete):
    name = 'powershell'
    source_template = POWERSHELL_COMPLETION_SCRIPT

    def get_completion_args(self) -> tuple[list[str], str]:  # pragma: nocover
        completion_args = os.getenv('_CLICK_COMPLETE_ARGS', '')
        incomplete = os.getenv('_CLICK_COMPLETE_WORD_TO_COMPLETE', '')
        cwords = click.parser.split_arg_string(completion_args)
        args = cwords[1:]
        return args, incomplete

    def format_completion(self, item: click.shell_completion.CompletionItem) -> str:  # pragma: nocover
        return f'{item.value}:::{item.help or " "}'


class PowerCoreComplete(PowerShellComplete):
    name = 'pwsh'


add_completion_class(PowerShellComplete)
add_completion_class(PowerCoreComplete)


def install_powershell(shell: Literal['powershell', 'pwsh']):
    # Ok I will explain what I have understood from the algorith I took my inspiration from
    # we try to set an execution policy suitable for the current user
    subprocess.run([shell, '-Command', 'Set-ExecutionPolicy', 'Unrestricted', '-Scope', 'CurrentUser'])  # nosec

    # we get the powershell user profile file where we will store the completion script
    try:
        result = subprocess.run(  # nosec
            [shell, '-NoProfile', '-Command', 'echo', '$profile'], check=True, capture_output=True
        )
    except subprocess.CalledProcessError:
        console.print('[error]Unable to get PowerShell user profile')
        raise SystemExit(1)

    user_profile = result.stdout.decode()
    user_profile_path = Path(user_profile.strip())
    parent_path = user_profile_path.parent
    # we make sure parents directories exist
    parent_path.mkdir(parents=True, exist_ok=True)
    completion_script = POWERSHELL_COMPLETION_SCRIPT % {'prog_name': 'ws', 'complete_var': '_WS_COMPLETE'}
    with open(user_profile_path, 'a') as f:
        f.write(f'{completion_script.strip()}\n')


def install_bash_zsh(bash: bool = True) -> None:
    home = Path.home()
    completion_dir = home / '.cli_completions'
    if bash:
        shell = 'bash'
        shell_config_file = home / '.bashrc'
    else:
        shell = 'zsh'
        shell_config_file = home / '.zshrc'

    if not completion_dir.exists():
        completion_dir.mkdir()

    try:
        command = f'_WS_COMPLETE={shell}_source ws'
        # bandit complains about shell injection, but we are not using untrusted string here, so it is fine.
        result = subprocess.run(command, shell=True, capture_output=True, check=True)  # nosec
    except subprocess.CalledProcessError:
        console.print('[error]Unable to get completion script for ws cli.')
        raise SystemExit(1)

    completion_script = completion_dir / f'ws-complete.{shell}'
    completion_script.write_text(result.stdout.decode())

    with shell_config_file.open('a') as f:
        f.write(f'\n. {completion_script.absolute()}\n')


def install_fish() -> None:
    home = Path.home()
    completion_dir = home / '.config/fish/completions'
    if not completion_dir.exists():
        completion_dir.mkdir(parents=True)

    try:
        command = '_WS_COMPLETE=fish_source ws'
        # bandit complains about shell injection, but we are not using untrusted string here, so it is fine.
        result = subprocess.run(command, shell=True, capture_output=True, check=True)  # nosec
    except subprocess.CalledProcessError:
        console.print('[error]Unable to get completion script for ws cli.')
        raise SystemExit(1)

    completion_script = completion_dir / 'ws.fish'
    completion_script.write_text(result.stdout.decode())


def _install_completion(shell: str) -> None:
    if shell == 'bash':
        install_bash_zsh()
    elif shell == 'zsh':
        install_bash_zsh(bash=False)
    elif shell in ('powershell', 'pwsh'):
        install_powershell(shell)  # type: ignore
    else:
        install_fish()


@click.command('install-completion')
def install_completion():
    """
    Install completion script for bash, zsh and fish shells.
    You will need to restart the shell for the changes to be loaded.
    """
    try:
        shell, _ = shellingham.detect_shell()
    except shellingham.ShellDetectionFailure:
        console.print('[error]Unable to detect the current shell.')
        raise SystemExit(1)
    except RuntimeError as e:
        click.echo(f'[error]{e}')
        raise SystemExit(1)

    if shell not in SHELLS:
        console.print(f'[error]Your shell is not supported. Shells supported are: {", ".join(SHELLS)}')
        raise SystemExit(1)

    _install_completion(shell)
    console.print('[success]Successfully installed completion script!')
