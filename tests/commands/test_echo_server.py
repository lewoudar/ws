import pytest
import trio
from trio_websocket import open_websocket_url

from ws.commands.echo_server import main
from ws.main import cli


def test_should_print_error_when_host_is_not_correct(runner):
    result = runner.invoke(cli, ['echo-server', '-H', 'foo'])

    assert result.exit_code == 2
    assert 'foo is neither "localhost" nor a valid ip address' in result.output


def test_should_print_error_when_port_is_not_a_number(runner):
    result = runner.invoke(cli, ['echo-server', '-p', 'foo'])

    assert result.exit_code == 2
    assert 'not a valid integer range' in result.output


def test_should_print_error_when_given_cert_file_does_not_exit(runner):
    result = runner.invoke(cli, ['echo-server', '-c', 'foo.pem'])

    assert result.exit_code == 2
    assert "File 'foo.pem' does not exist" in result.output


def test_should_print_error_when_given_cert_file_is_not_a_file(runner, tmp_path):
    result = runner.invoke(cli, ['echo-server', '-c', f'{tmp_path}'])

    assert result.exit_code == 2
    assert 'is a directory' in result.output


def test_should_print_error_when_given_key_file_does_not_exist(runner):
    result = runner.invoke(cli, ['echo-server', '-k', 'key.pem'])

    assert result.exit_code == 2
    assert "File 'key.pem' does not exist" in result.output


def test_should_print_error_when_given_key_file_is_not_a_file(runner, tmp_path):
    result = runner.invoke(cli, ['echo-server', '-k', f'{tmp_path}'])

    assert result.exit_code == 2
    assert 'is a directory' in result.output


def test_should_print_error_when_key_file_is_given_without_cert_file(runner, tmp_path):
    fake_key = tmp_path / 'key.pem'
    fake_key.touch()
    result = runner.invoke(cli, ['echo-server', '-k', f'{fake_key}'])

    assert result.exit_code == 2
    assert 'You cannot provide a private key file without the certificate' in result.output


def test_should_print_error_when_key_file_is_not_linked_to_certificate(runner, tmp_path, certificate):
    fake_key = tmp_path / 'key.pem'
    fake_key.write_text('Hello world')
    result = runner.invoke(cli, ['echo-server', '-c', f'{certificate}', '-k', f'{fake_key}'])

    assert result.exit_code == 1
    assert 'Unable to set up TLS. Please check the files you provided are correct.\n' == result.output


async def test_should_run_server_without_tls(nursery):
    nursery.start_soon(main, 'localhost', 1234)
    await trio.sleep(1)
    async with open_websocket_url('ws://localhost:1234/foo') as ws:
        await ws.send_message('hello world')
        assert 'hello world' == await ws.get_message()


async def test_should_run_server_with_tls_certificate(capsys, nursery, certificate, client_context):
    nursery.start_soon(main, 'localhost', 1234, f'{certificate}')
    await trio.sleep(1)
    async with open_websocket_url('wss://localhost:1234/foo', ssl_context=client_context) as ws:
        await ws.send_message('hello world')
        assert 'hello world' == await ws.get_message()

    assert capsys.readouterr().out == 'Running server on localhost:1234 💫\n'


async def test_should_run_server_with_tls_certificate_and_key_file(nursery, certificate, private_key, client_context):
    nursery.start_soon(main, 'localhost', 1234, f'{certificate}', f'{private_key}')
    await trio.sleep(1)
    async with open_websocket_url('wss://localhost:1234/foo', ssl_context=client_context) as ws:
        await ws.send_message('hello world')
        assert 'hello world' == await ws.get_message()


def test_should_check_trio_run_is_correctly_called_without_arguments(runner, mocker):
    run_mock = mocker.patch('trio.run')
    result = runner.invoke(cli, ['echo-server'])

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, 'localhost', 80, None, None)


@pytest.mark.parametrize(
    ('host_option', 'port_option', 'cert_option', 'key_option'),
    [('-H', '-p', '-c', '-k'), ('--host', '--port', '--cert-file', '--key-file')],
)
def test_should_check_trio_run_is_correctly_called_with_arguments(
    runner, mocker, certificate, private_key, host_option, port_option, cert_option, key_option
):
    run_mock = mocker.patch('trio.run')
    result = runner.invoke(
        cli,
        [
            'echo-server',
            host_option,
            '::1',
            port_option,
            '1234',
            cert_option,
            f'{certificate}',
            key_option,
            f'{private_key}',
        ],
    )

    assert result.exit_code == 0
    run_mock.assert_called_once_with(main, '::1', 1234, f'{certificate}', f'{private_key}')
