import click
from click_didyoumean import DYMGroup
from rich.traceback import install

from .commands.completion import install_completion
from .commands.echo_server import echo_server
from .commands.listen import listen
from .commands.ping import ping
from .commands.pong import pong
from .commands.session import session
from .commands.tail import tail
from .commands.text_byte import byte, text

install(show_locals=True)


@click.version_option('0.1.0', message='%(prog)s version %(version)s')
@click.group(cls=DYMGroup, context_settings={'help_option_names': ['-h', '--help']})
def cli():
    """
    A convenient websocket cli.
    """


for command in [tail, ping, pong, echo_server, listen, byte, text, session, install_completion]:
    cli.add_command(command)
