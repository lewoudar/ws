import io
import pathlib
import signal
import ssl
from typing import Callable

import pytest
import trustme
from click.testing import CliRunner
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import PipeInput, create_pipe_input
from prompt_toolkit.output import DummyOutput
from rich.console import Console

from ws.console import console, custom_theme


@pytest.fixture()
def runner():
    """CLI test runner"""
    return CliRunner()


@pytest.fixture()
def file_to_read(tmp_path) -> pathlib.Path:
    """A Path representing a file with dummy content to read."""
    data = ['I like async concurrency!'] * 20
    file_path = tmp_path / 'file.txt'
    file_path.write_text('\n'.join(data) + '\n')
    return file_path


@pytest.fixture(scope='session')
def signal_message() -> Callable[[int], str]:
    """Factory function that return the signal message sent when a user interrupts a program."""

    def _signal_message(signum: int) -> str:
        method = 'Ctrl+C' if signum == signal.SIGINT else 'SIGTERM'
        return f'Program was interrupted by {method}, good bye! 👋\n'

    yield _signal_message


@pytest.fixture(scope='session')
def ca():
    """trustme.CA object."""
    return trustme.CA()


@pytest.fixture(scope='session')
def client_context(ca):
    """Client SSLContext used in tests."""
    # noinspection PyTypeChecker
    client_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ca.configure_trust(client_context)
    return client_context


@pytest.fixture(scope='session')
def server_cert(ca) -> trustme.LeafCert:
    """trustme.LeafCert object used to derive certificate and private key."""
    return ca.issue_cert('localhost')


@pytest.fixture(scope='session')
def server_context(server_cert):
    """Server SSLContext used in tests."""
    # noinspection PyTypeChecker
    server_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_cert.configure_cert(server_context)
    return server_context


@pytest.fixture()
def certificate(tmp_path, server_cert) -> pathlib.Path:
    """Path to a certificate file used in tests."""
    cert_path = tmp_path / 'cert.pem'
    server_cert.private_key_and_cert_chain_pem.write_to_path(cert_path)
    return cert_path


@pytest.fixture()
def private_key(tmp_path, server_cert) -> pathlib.Path:
    """Path to the private key used in tests."""
    key_path = tmp_path / 'key.pem'
    server_cert.private_key_pem.write_to_path(key_path)
    return key_path


@pytest.fixture()
def test_console() -> Console:
    """A console designed for tests."""
    return Console(theme=custom_theme, file=io.StringIO())


@pytest.fixture()
def reset_console():
    """Fixture useful in tests where we changed some console attributes."""
    width = console.width
    yield
    console.record = False
    console.width = width


@pytest.fixture()
def mock_input() -> PipeInput:
    """Mock input to interact with prompt_toolkit session."""
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input
