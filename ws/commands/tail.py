from __future__ import annotations

import os

import click
import trio

from ws.utils.io import function_runner, reverse_read_lines, signal_handler


async def tail_file(filename: str, lines_count: int, follow: bool) -> None:
    count = 0
    lines: list[bytes] = []

    async for line in reverse_read_lines(filename):
        lines.append(line)
        count += 1
        if count == lines_count:
            break

    for line in lines[::-1]:
        click.echo(line)

    if follow:
        file_size = os.stat(filename).st_size
        while True:
            size = os.stat(filename).st_size
            if file_size < size:
                async with await trio.open_file(filename) as f:
                    await f.seek(file_size)
                    async for line in f:
                        click.echo(line, nl=False)

                file_size = size
            else:
                await trio.sleep(0.1)


async def main(filename: str, lines_count: int, follow: bool) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, tail_file, filename, lines_count, follow)
        nursery.start_soon(signal_handler, nursery.cancel_scope)


@click.command()
@click.argument('filename', type=click.Path(exists=True, dir_okay=False))
@click.option(
    '-n', 'lines_count', type=click.IntRange(min=1), default=10, show_default=True, help='number of lines to print'
)
@click.option('-f', '--follow', is_flag=True)
def tail(filename: str, lines_count: int, follow: bool):
    """
    An emulator of the tail unix command that output the last lines of FILENAME.
    It is a light implementation of the tail command. It only handles one file at a time and only
    supports two options, so for linux/unix users, you should use the builtin command.
    """
    trio.run(main, filename, lines_count, follow)
