import ssl
from unittest.mock import call

import mock
import pytest
import trio
from trio_websocket import ConnectionClosed, DisconnectionTimeout, serve_websocket

from tests.helpers import server_handler
from ws.client import get_client_ssl_context, websocket_client


class TestGetClientSSLContext:
    """Tests function get_client_ssl_context."""

    def test_should_return_none_when_ca_and_certificate_are_none(self):
        assert get_client_ssl_context(ca_file=None, certificate=None) is None

    def test_should_print_error_when_there_is_an_issue_with_ca_file(self, tmp_path, capsys):
        ca_file = tmp_path / 'ca.pem'
        ca_file.write_text('fake ca')

        with pytest.raises(SystemExit):
            get_client_ssl_context(ca_file=f'{ca_file}')

        # rich tries to determine the size of the terminal before writing to it. With my experiences
        # I noticed that this means sometimes a '\n' can be inserted in the message displayed, this is why I don't
        # check the whole message at one
        output = capsys.readouterr().out
        assert 'Unable to load certificate(s) located in the (tls_ca_file)' in output
        assert f'{ca_file}\n' in output

    def test_should_return_ssl_context_when_ca_file_is_provided(self, tmp_path, ca):
        ca_file = tmp_path / 'ca.pem'
        ca.cert_pem.write_to_path(f'{ca_file}')
        context = get_client_ssl_context(ca_file=f'{ca_file}')

        assert isinstance(context, ssl.SSLContext)

    def test_should_print_error_when_certificate_is_not_correct(self, tmp_path, capsys):
        cert = tmp_path / 'cert.pem'
        cert.write_text('fake cert')

        with pytest.raises(SystemExit):
            get_client_ssl_context(certificate=f'{cert}')

        output = capsys.readouterr().out
        assert 'Unable to load the certificate with the provided information.\n' in output
        assert 'Please check tls_certificate_file and eventually tls_key_file and tls_password\n' in output

    def test_should_print_error_when_keyfile_is_provided_without_certificate(self, capsys, private_key):
        with pytest.raises(SystemExit):
            get_client_ssl_context(keyfile=f'{private_key}')

        assert capsys.readouterr().out == 'You provided tls_key_file without tls_certificate_file\n'

    def test_should_print_error_when_only_password_is_provided(self, capsys):
        with pytest.raises(SystemExit):
            get_client_ssl_context(password='pass')

        assert capsys.readouterr().out == 'You provided tls_password without tls_key_file and tls_certificate_file\n'

    def test_should_return_ssl_context_when_certificate_is_provided_without_key_file(self, tmp_path, certificate):
        context = get_client_ssl_context(certificate=f'{certificate}')
        assert isinstance(context, ssl.SSLContext)

    def test_should_return_ssl_context_when_certificate_is_provided_with_key_file(
        self, tmp_path, certificate, private_key
    ):
        context = get_client_ssl_context(certificate=f'{certificate}', keyfile=f'{private_key}')
        assert isinstance(context, ssl.SSLContext)

    # I don't want to bother myself with cryptography to create a cert with a password, so I just test
    # the call is correctly done
    def test_should_correctly_call_ssl_function_with_cert_key_and_password(self, mocker, certificate, private_key):
        func_mock = mocker.patch('ssl.create_default_context')
        get_client_ssl_context(certificate=f'{certificate}', keyfile=f'{private_key}', password='pass')

        func_mock.assert_called_once()
        call_list = [call().load_cert_chain(f'{certificate}', keyfile=f'{private_key}', password='pass')]
        func_mock.assert_has_calls(call_list)


class TestClient:
    """Tests client function."""

    @staticmethod
    async def worker(url):
        async with websocket_client(url) as client:
            await client.send_message('foo')
            print(await client.get_message())

    async def test_should_print_error_when_unable_to_connect_to_server(self, monkeypatch, capsys, autojump_clock):
        monkeypatch.setenv('ws_connect_timeout', '2')
        url = 'ws://localhost:1234'

        async def echo_handler(request):
            await trio.sleep(3)
            ws = await request.accept()
            while True:
                try:
                    message = await ws.get_message()
                    await ws.send_message(message)
                except ConnectionClosed:
                    break

        with pytest.raises(SystemExit):
            async with trio.open_nursery() as nursery:
                await nursery.start(serve_websocket, echo_handler, '127.0.0.1', 1234, None)
                nursery.start_soon(self.worker, url)

        assert capsys.readouterr().out == f'Unable to connect to {url}\n'

    async def test_should_print_error_when_unable_to_close_connection_on_time(self, mocker, capsys):
        func_mock = mocker.patch('trio_websocket.WebSocketConnection.send_message', new=mock.AsyncMock())
        func_mock.side_effect = DisconnectionTimeout
        url = 'ws://localhost:1234'

        with pytest.raises(SystemExit):
            async with trio.open_nursery() as nursery:
                await nursery.start(serve_websocket, server_handler, '127.0.0.1', 1234, None)
                nursery.start_soon(self.worker, url)

        assert capsys.readouterr().out == f'Unable to disconnect on time from {url}\n'

    async def test_should_print_error_when_connection_is_rejected_by_server(self, capsys):
        url = 'ws://localhost:1234'
        status_code = 400
        headers = [('X-Foo', 'bar')]
        expected_headers = [('x-foo', 'bar'), ('content-length', '9')]
        body = b'You loss!'

        async def reject_handler(request):
            await request.reject(status_code, extra_headers=headers, body=body)

        with pytest.raises(SystemExit):
            async with trio.open_nursery() as nursery:
                await nursery.start(serve_websocket, reject_handler, 'localhost', 1234, None)
                nursery.start_soon(self.worker, url)

        expected = (
            f"Connection was rejected by {url}\n"
            f"status code = {status_code}\n"
            f"headers = {expected_headers}\n"
            f"body = {body.decode()}\n"
        )

        assert capsys.readouterr().out == expected

    async def test_should_print_error_when_settings_are_badly_configured(self, capsys, monkeypatch):
        monkeypatch.setenv('WS_CONNECT_TIMEOUT', 'foo')
        with pytest.raises(SystemExit):
            async with websocket_client('ws://localhost:1234') as client:
                await client.send_message('foo')

        output = capsys.readouterr().out
        assert 'connect_timeout' in output
        assert 'not a valid float' in output

    async def test_should_connect_and_read_message_from_server_without_tls(self, nursery):
        await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
        async with websocket_client('ws://localhost:1234') as client:
            await client.send_message('foo')
            assert 'foo' == await client.get_message()

    async def test_should_connect_and_read_message_from_server_with_tls_and_ca_file(
        self, monkeypatch, tmp_path, nursery, ca, server_context
    ):
        ca_file = tmp_path / 'ca.pem'
        ca.cert_pem.write_to_path(f'{ca_file}')
        monkeypatch.setenv('WS_TLS_CA_FILE', f'{ca_file}')

        await nursery.start(serve_websocket, server_handler, 'localhost', 1234, server_context)
        async with websocket_client('wss://localhost:1234') as client:
            await client.send_message('foo')
            assert 'foo' == await client.get_message()
