import contextlib
import ssl
from typing import Optional

import certifi
import pydantic
from trio_websocket import (
    ConnectionRejected,
    ConnectionTimeout,
    DisconnectionTimeout,
    WebSocketConnection,
    open_websocket_url,
)

from ws.console import console
from ws.settings import get_settings


def get_client_ssl_context(
    ca_file: str = None, certificate: str = None, keyfile: str = None, password: str = None
) -> Optional[ssl.SSLContext]:
    context = None
    if ca_file:
        try:
            # noinspection PyTypeChecker
            # PyPy is stricter than CPython here if we don't convert Path object to string, we will get an error
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(ca_file))
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
            additional_arguments['keyfile'] = str(keyfile)
        if password:
            additional_arguments['password'] = password
        try:
            context.load_cert_chain(str(certificate), **additional_arguments)
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
