import pytest
import trio

from ws.settings import get_settings
from ws.utils.decorators import catch_pydantic_error, catch_too_slow_error


class TestCatchSlowError:
    """Tests function catch_slow_error."""

    async def test_should_raise_system_error_when_program_raises_timeout_error(self, capsys, autojump_clock):
        @catch_too_slow_error
        async def main():
            with trio.fail_after(2):
                await trio.sleep(3)

        with pytest.raises(SystemExit):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(main)

        assert capsys.readouterr().out == 'Unable to get response on time\n'

    async def test_should_not_raise_or_print_error_when_program_runs_normally(self, capsys, autojump_clock):
        @catch_too_slow_error
        async def main():
            with trio.fail_after(2):
                await trio.sleep(1)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(main)

        assert capsys.readouterr().out == ''


class TestCatchPydanticError:
    """Tests function catch_pydantic_error"""

    async def test_should_raise_system_error_when_program_raise_pydantic_error(self, monkeypatch, capsys):
        @catch_pydantic_error
        async def main():
            monkeypatch.setenv('WS_CONNECT_TIMEOUT', 'foo')
            print(get_settings())

        with pytest.raises(SystemExit):
            async with trio.open_nursery() as nursery:
                nursery.start_soon(main)

        output = capsys.readouterr().out
        assert 'connect_timeout' in output
        assert 'not a valid float' in output

    async def test_should_not_raise_error_when_program_runs_correctly(self, capsys):
        @catch_pydantic_error
        async def main():
            print(get_settings())

        async with trio.open_nursery() as nursery:
            nursery.start_soon(main)

        assert 'not a valid float' not in capsys.readouterr().out
