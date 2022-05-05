import ssl

import click
import trio
from trio_websocket import ConnectionClosed, WebSocketRequest, serve_websocket

from ws.console import console
from ws.parameters import HOST
from ws.settings import get_settings
from ws.utils.io import function_runner, signal_handler

SETTINGS = get_settings()


async def request_handler(request: WebSocketRequest) -> None:
    ws = await request.accept()
    while True:
        try:
            with trio.fail_after(SETTINGS.response_timeout):
                message = await ws.get_message()
            await ws.send_message(message)
        except (ConnectionClosed, trio.TooSlowError):
            break


async def run_server(host: str, port: int, cert_file: str = None, key_file: str = None) -> None:
    if key_file is not None and cert_file is None:
        raise click.UsageError('You cannot provide a private key file without the certificate.')

    ssl_context = None
    if cert_file is not None:
        # noinspection PyTypeChecker
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        try:
            ssl_context.load_cert_chain(cert_file, keyfile=key_file)
        except ssl.SSLError:
            console.print('[error]Unable to set up TLS. Please check the files you provided are correct.')
            raise SystemExit(1)

    console.print(f'[info]Running server on {host}:{port} :dizzy:')
    await serve_websocket(
        request_handler,
        host,
        port,
        ssl_context,
        message_queue_size=SETTINGS.message_queue_size,
        max_message_size=SETTINGS.max_message_size,
        connect_timeout=SETTINGS.connect_timeout,
        disconnect_timeout=SETTINGS.disconnect_timeout,
    )


async def main(host: str, port: int, cert_file: str = None, key_file: str = None) -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(function_runner, nursery.cancel_scope, run_server, host, port, cert_file, key_file)
        nursery.start_soon(signal_handler, nursery.cancel_scope)


@click.command('echo-server')
@click.option('-H', '--host', type=HOST, help='Host to bind the server.', default='localhost', show_default=True)
@click.option(
    '-p',
    '--port',
    type=click.IntRange(min=0, max=65535),
    help='Port to bind the server.',
    default=80,
    show_default=True,
)
@click.option('-c', '--cert-file', type=click.Path(exists=True, dir_okay=False), help='Server certificate.')
@click.option(
    '-k', '--key-file', type=click.Path(exists=True, dir_okay=False), help='Private key bound to the certificate.'
)
def echo_server(host: str, port: int, cert_file: str = None, key_file: str = None):
    """
    Runs an echo websocket server.
    The server will return the data sent by the client.
    """
    trio.run(main, host, port, cert_file, key_file)
