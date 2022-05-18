import subprocess  # nosec
from pathlib import Path

import click
import shellingham

from ws.console import console

SHELLS = ['bash', 'zsh', 'fish']


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
