"""Some utility functions for commands"""
import contextlib
import io
import signal
from typing import Any, AsyncIterator, Callable, TypeVar

import anyio
import asyncclick as click
import trio
from trio_websocket import (
    ConnectionRejected,
    ConnectionTimeout,
    DisconnectionTimeout,
    WebSocketConnection,
    open_websocket_url,
)

from ws.console import console
from ws.settings import get_settings


async def signal_handler(scope: anyio.CancelScope) -> None:
    with anyio.open_signal_receiver(signal.SIGINT, signal.SIGTERM) as signals:
        async for signum in signals:
            key = 'Ctrl+C' if signum == signal.SIGINT else 'SIGTERM'
            console.print(f'[info]Program was interrupted by {key}, good bye! :waving_hand:')

            # noinspection PyAsyncCall
            scope.cancel()
            return


async def function_runner(scope: anyio.CancelScope, function: Callable, *args: Any) -> None:
    await function(*args)
    # noinspection PyAsyncCall
    scope.cancel()


# it is a good idea to read the file in byte mode, more information can be found
# in the answers of this post: https://stackoverflow.com/a/23646049/7181806
async def reverse_read_lines(file: str) -> AsyncIterator[bytes]:
    async with await anyio.open_file(file, 'rb') as f:
        await f.seek(0, whence=io.SEEK_END)
        pointer = await f.tell()
        buffer = bytearray()

        while pointer >= 0:
            await f.seek(pointer)
            # we read character by character
            pointer -= 1
            char = await f.read(1)

            # if we reach '\n' this means we have read one line and can return it
            if char == b'\n':
                yield buffer[::-1]
                buffer.clear()
            else:
                buffer += char

        # if the buffer is not empty, it is the first line, so we return it
        if buffer:
            yield buffer[::-1]


@contextlib.asynccontextmanager
async def websocket_client(url: str) -> WebSocketConnection:
    settings = get_settings()
    arguments = {
        'connect_timeout': settings.connect_timeout,
        'disconnect_timeout': settings.disconnect_timeout,
        'message_queue_size': settings.message_queue_size,
        'max_message_size': settings.max_message_size,
        'extra_headers': settings.extra_headers,
    }
    try:
        async with open_websocket_url(url, **arguments) as ws:
            yield ws
    except ConnectionTimeout:
        console.print(f'[error]Unable to connect to {url}')
        raise click.Abort()
    except DisconnectionTimeout:
        console.print(f'[error]Unable to disconnect on time from {url}')
        raise click.Abort()
    except ConnectionRejected as e:
        console.print(f'[error]Connection was rejected by {url}')
        console.print(f'[label]status code[/] = [info]{e.status_code}[/]')
        headers = [(key.decode(), value.decode()) for key, value in e.headers] if e.headers is not None else []
        console.print(f'[label]headers[/] = {headers}')
        console.print(f'[label]body[/] = [info]{e.body.decode()}[/]')

        raise click.Abort()


# Create a generic type helps to preserve type annotations done by static analyzing tools
FuncCallable = TypeVar('FuncCallable', bound=Callable)


def catch_too_slow_error(func: FuncCallable) -> FuncCallable:
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except trio.TooSlowError:
            console.print('[error]Unable to get response on time')
            raise click.Abort()

    return wrapper
