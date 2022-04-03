import click
from rich.traceback import install

from .commands.echo_server import echo_server
from .commands.ping import ping
from .commands.pong import pong
from .commands.tail import tail

install(show_locals=True)


@click.version_option('0.1.0', message='%(prog)s version %(version)s')
@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    """
    A convenient websocket cli.
    """


for command in [tail, ping, pong, echo_server]:
    cli.add_command(command)
