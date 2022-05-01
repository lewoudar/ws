"""Some utility functions for commands"""
import contextlib
import io
import pathlib
import signal
import ssl
from typing import Any, AsyncIterator, Callable, Optional, TypeVar

import anyio
import certifi
import pydantic
import trio
from rich.console import Console
from trio_websocket import (
    ConnectionRejected,
    ConnectionTimeout,
    DisconnectionTimeout,
    WebSocketConnection,
    open_websocket_url,
)

from ws.console import console
from ws.settings import Settings, get_settings

# Create a generic type helps to preserve type annotations done by static analyzing tools
FuncCallable = TypeVar('FuncCallable', bound=Callable)


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


def get_client_ssl_context(
    ca_file: str = None, certificate: str = None, keyfile: str = None, password: str = None
) -> Optional[ssl.SSLContext]:
    context = None
    if ca_file:
        try:
            # noinspection PyTypeChecker
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_file)
        except ssl.SSLError:
            console.print(f'[error]Unable to load certificate(s) located in the (tls_ca_file) file {ca_file}')
            raise SystemExit(1)

    # TODO: If someone one day is unhappy by the fact that I load a CA bundle certificate from certifi
    #  It is a good idea to look httpx default context implementation. It creates a context that can work
    #  for both verified and unverified connections
    if certificate:
        if context is None:
            # noinspection PyTypeChecker
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=certifi.where())
        additional_arguments = {}
        if keyfile:
            additional_arguments['keyfile'] = keyfile
        if password:
            additional_arguments['password'] = password
        try:
            context.load_cert_chain(certificate, **additional_arguments)
        except ssl.SSLError:
            message = (
                'Unable to load the certificate with the provided information.\n'
                'Please check tls_certificate_file and eventually tls_key_file and tls_password'
            )
            console.print(f'[error]{message}')
            raise SystemExit(1)
        return context

    if keyfile:
        console.print('[error]You provided tls_key_file without tls_certificate_file')
        raise SystemExit(1)

    if password:
        console.print('[error]You provided tls_password without tls_key_file and tls_certificate_file')
        raise SystemExit(1)

    return context


@contextlib.asynccontextmanager
async def websocket_client(url: str) -> WebSocketConnection:
    try:
        settings = get_settings()
    except pydantic.ValidationError as e:
        console.print(f'[error]{e}')
        raise SystemExit(1)

    arguments = {
        'connect_timeout': settings.connect_timeout,
        'disconnect_timeout': settings.disconnect_timeout,
        'message_queue_size': settings.message_queue_size,
        'max_message_size': settings.max_message_size,
        'extra_headers': settings.extra_headers,
    }
    ssl_context = get_client_ssl_context(
        ca_file=settings.tls_ca_file,
        certificate=settings.tls_certificate_file,
        keyfile=settings.tls_key_file,
        password=settings.tls_password,
    )

    try:
        async with open_websocket_url(url, ssl_context=ssl_context, **arguments) as ws:
            yield ws
    except ConnectionTimeout:
        console.print(f'[error]Unable to connect to {url}')
        raise SystemExit(1)
    except DisconnectionTimeout:
        console.print(f'[error]Unable to disconnect on time from {url}')
        raise SystemExit(1)
    except ConnectionRejected as e:
        console.print(f'[error]Connection was rejected by {url}')
        console.print(f'[label]status code[/] = [info]{e.status_code}[/]')
        headers = [(key.decode(), value.decode()) for key, value in e.headers] if e.headers is not None else []
        console.print(f'[label]headers[/] = {headers}')
        console.print(f'[label]body[/] = [info]{e.body.decode()}[/]')

        raise SystemExit(1)


async def sleep_until(cancel_scope: trio.CancelScope, duration: float = None) -> None:
    if duration is None:
        await trio.sleep_forever()
    else:
        await trio.sleep(duration)
        cancel_scope.cancel()


def configure_console_recording(terminal: Console, settings: Settings, filename: str = None) -> None:
    if filename is not None:
        terminal.record = True
        if filename.endswith('.svg'):
            terminal.width = settings.svg_width


def save_output(terminal: Console, filename: str) -> None:
    file_path = pathlib.Path(filename)
    if file_path.suffix == '.html':
        terminal.save_html(filename)
    elif file_path.suffix == '.svg':
        terminal.save_svg(filename, title=file_path.name)
    else:
        terminal.save_text(filename)


def catch_too_slow_error(func: FuncCallable) -> FuncCallable:
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except trio.TooSlowError:
            console.print('[error]Unable to get response on time')
            raise SystemExit(1)

    return wrapper


def catch_pydantic_error(func: FuncCallable) -> FuncCallable:
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except pydantic.ValidationError as e:
            console.print(f'[error]{e}')
            raise SystemExit(1)

    return wrapper
