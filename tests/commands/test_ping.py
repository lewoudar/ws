import pytest
from trio_websocket import serve_websocket

from tests.helpers import killer, server_handler
from ws.commands.ping import main
from ws.main import cli


def test_should_print_error_when_url_argument_is_not_given(runner):
    result = runner.invoke(cli, ['ping'])

    assert result.exit_code == 2
    assert "Missing argument 'URL'" in result.output


@pytest.mark.parametrize('url', ['ws:/websocket', 'https://websocket.com'])
def test_should_print_error_when_given_url_is_not_a_websocket_url(runner, url):
    result = runner.invoke(cli, ['ping', url])

    assert result.exit_code == 2
    assert f'{url} is not a valid websocket url' in result.output


@pytest.mark.parametrize('number', ['foo', '4.5'])
def test_should_print_error_when_number_of_ping_is_not_a_number(runner, number):
    result = runner.invoke(cli, ['ping', 'ws://websocket.com', '-n', number])

    assert result.exit_code == 2
    assert 'is not a valid integer' in result.output


def test_should_print_error_when_number_of_ping_is_0(runner):
    result = runner.invoke(cli, ['ping', 'ws://websocket.com', '-n', '0'])

    assert result.exit_code == 2
    assert 'The number of pings cannot be 0' in result.output


def test_should_print_error_when_interval_is_not_a_float(runner):
    result = runner.invoke(cli, ['ping', 'ws://websocket.com', '-i', 'foo'])

    assert result.exit_code == 2
    assert 'is not a valid float range' in result.output


@pytest.mark.parametrize('interval', ['-1', '0'])
def test_should_print_error_when_interval_is_not_in_the_valid_range(runner, interval):
    result = runner.invoke(cli, ['ping', 'ws://websocket.com', '-i', interval])

    assert result.exit_code == 2
    assert 'is not in the range x>0' in result.output


async def test_should_make_a_one_ping_with_default_values(capsys, nursery):
    interval = 1.0
    number = 1
    url = 'ws://localhost:1234'

    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main(url, number, interval)

    assert f'PING {url} with 32 bytes of data\nsequence=1, time=' in capsys.readouterr().out


async def test_should_make_five_pings(capsys, nursery):
    interval = 1.0
    number = 5

    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await main('ws://localhost:1234', number, interval)
    data = capsys.readouterr().out

    assert data.count('sequence') == number


async def test_should_make_infinite_number_of_pings(capsys, nursery):
    interval = 1.0
    number = -1

    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    nursery.start_soon(killer, 2)
    await main('ws://localhost:1234', number, interval)
    data = capsys.readouterr().out

    assert data.count('sequence') == 2


def test_should_check_trio_run_is_correctly_called_without_arguments(runner, mocker):
    run_mock = mocker.patch('trio.run')
    url = 'ws://localhost'
    result = runner.invoke(cli, ['ping', url])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, url, 1, 1.0, None)


@pytest.mark.parametrize('interval_option', ['-i', '--interval'])
@pytest.mark.parametrize('number_option', ['-n', '--number'])
@pytest.mark.parametrize('message_option', ['-m', '--message'])
def test_should_check_trio_run_is_correctly_called_with_arguments(
    runner, mocker, interval_option, number_option, message_option
):
    run_mock = mocker.patch('trio.run')
    number = 3
    interval = 2
    message = 'hello'
    result = runner.invoke(
        cli, ['ping', ':8000', interval_option, interval, number_option, number, message_option, message]
    )

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, 'ws://localhost:8000', number, interval, message.encode())
