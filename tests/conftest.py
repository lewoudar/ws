import signal
from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner


@pytest.fixture()
def runner():
    """CLI test runner"""
    return CliRunner()


@pytest.fixture()
def file_to_read(tmp_path) -> Path:
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
