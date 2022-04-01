import click
import pytest

from ws.parameters import ByteParamType, HostParamType, WsUrlParamType, get_normalized_message


class TestWsUrlParamType:
    """Tests parameter WsUrlParamType"""

    @pytest.mark.parametrize('url', ['ws:/websocket', 'https://websocket.com', ':8000f'])
    def test_should_raise_error_when_given_value_is_not_a_websocket_url(self, url):
        param = WsUrlParamType()

        with pytest.raises(click.BadParameter) as exc_info:
            param.convert(url, None, None)

        assert f'{url} is not a valid websocket url' == str(exc_info.value)

    @pytest.mark.parametrize(
        ('given_url', 'expected_url'),
        [
            ('ws://websocket.com', 'ws://websocket.com'),
            ('wss://websocket.com', 'wss://websocket.com'),
            (':8000', 'ws://localhost:8000'),
        ],
    )
    def test_should_return_websocket_url(self, given_url, expected_url):
        param = WsUrlParamType()
        assert param.convert(given_url, None, None) == expected_url


class TestGetNormalizedMessage:
    """Tests function get_normalized_message"""

    @pytest.mark.parametrize(('value', 'is_bytes', 'expected'), [('hello', False, 'hello'), ('hello', True, b'hello')])
    def test_should_return_given_string(self, value, is_bytes, expected):
        assert get_normalized_message(value, is_bytes) == expected

    @pytest.mark.parametrize('is_bytes', [True, False])
    def test_should_raise_error_when_file_does_not_exist(self, is_bytes):
        with pytest.raises(click.BadParameter) as exc_info:
            get_normalized_message('file@foo.txt', is_bytes)

        assert 'file foo.txt does not exist' == str(exc_info.value)

    @pytest.mark.parametrize('is_bytes', [True, False])
    def test_should_raise_error_when_file_cannot_be_opened(self, tmp_path, is_bytes):
        dummy_file = tmp_path / 'file.txt'
        dummy_file.write_text('Hello world')
        dummy_file.chmod(0o333)

        with pytest.raises(click.BadParameter) as exc_info:
            get_normalized_message(f'file@{dummy_file}', is_bytes)

        assert f'file {dummy_file} cannot be opened' == str(exc_info.value)

    @pytest.mark.parametrize(
        ('is_bytes', 'expected'),
        [(False, 'We have the best food in Cameroon'), (True, b'We have the best food in Cameroon')],
    )
    def test_should_return_file_content_given_correct_input(self, tmp_path, expected, is_bytes):
        dummy_file = tmp_path / 'file.txt'
        dummy_file.write_text('We have the best food in Cameroon')

        assert get_normalized_message(f'file@{dummy_file}', is_bytes) == expected


class TestByteParamType:
    """Tests parameter ByteParamType"""

    def test_should_raise_error_when_value_length_is_greater_than_given_max_length(self):
        value = 'a' * 101
        param = ByteParamType(max_length=100)

        with pytest.raises(click.BadParameter) as exc_info:
            param.convert(value, None, None)

        assert f'{value} is longer than 100 bytes' == str(exc_info.value)

    def test_should_return_bytes_given_string_as_input(self):
        param = ByteParamType()
        assert param.convert('hello', None, None) == b'hello'

    def test_should_return_bytes_given_file_as_input(self, tmp_path):
        value = 'Cameroon is a great country!'
        dummy_file = tmp_path / 'file.txt'
        dummy_file.write_text(value)
        param = ByteParamType()

        assert param.convert(f'file@{dummy_file}', None, None) == value.encode()


class TestHostParamType:
    """Tests parameter HostParamType"""

    @pytest.mark.parametrize('value', ['Localhost', '123.2.2', 'hello'])
    def test_should_raise_error_when_value_is_not_a_valid_host(self, value):
        param = HostParamType()

        with pytest.raises(click.BadParameter) as exc_info:
            param.convert(value, None, None)

        assert f'{value} is neither "localhost" nor a valid ip address' == str(exc_info.value)

    @pytest.mark.parametrize('value', ['localhost', '192.168.1.1', '::1'])
    def test_should_return_value_when_it_is_correct(self, value):
        param = HostParamType()
        assert param.convert(value, None, None) == value
