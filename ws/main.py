import click

from .commands.ping import ping
from .commands.tail import tail


@click.version_option('0.1.0', message='%(prog)s version %(version)s')
@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    """
    A convenient websocket cli.
    """


for command in [tail, ping]:
    cli.add_command(command)  # type: ignore
