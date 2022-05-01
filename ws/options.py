"""Groups options common to several commands."""
from typing import Callable

import click

from ws.parameters import WS_URL, ByteParamType


def validate_number(message: str) -> Callable[[click.Context, click.Parameter, int], int]:
    def _validate_number(ctx: click.Context, param: click.Parameter, value: int) -> int:
        if value == 0:
            raise click.BadParameter(message)
        return value

    return _validate_number


url_argument = click.argument('url', type=WS_URL)


def message_option(message: str) -> Callable:
    # we choose a length of 125 for the following reasons:
    # - A control frame like ping or pong should not be fragmented
    # - The maximum length to feat the size in one octet in the resulting websocket packet is 125, and it seems a
    # reasonable value to avoid error messages related to message size on the server side
    return click.option(
        '-m',
        '--message',
        type=ByteParamType(max_length=125),
        help=message,
    )


def number_option(message: str, callback: Callable[[click.Context, click.Parameter, int], int]) -> Callable:
    return click.option(
        '-n',
        '--number',
        type=int,
        default=1,
        show_default=True,
        callback=callback,
        help=message,
    )


def interval_option(message: str) -> Callable:
    return click.option(
        '-i',
        '--interval',
        type=click.FloatRange(min=0, min_open=True),
        default=1.0,
        show_default=True,
        help=message,
    )


duration_option = click.option(
    '-d', '--duration', type=click.FloatRange(min=0, min_open=True), help='Time to run the program in seconds.'
)

filename_option = click.option(
    '-f',
    '--file',
    'filename',
    type=click.Path(dir_okay=False, writable=True),
    help=(
        'File to store the output. The file extension determines the type of file will be created. '
        'A file ending with ".html" will be an html file, a file ending with ".svg" will be an SVG file and other '
        'extensions will be considered as text files.'
    ),
)
