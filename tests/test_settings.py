import math
import os

import pydantic
import pytest

from ws.settings import ENV_FILE, Settings, get_config_from_toml, get_settings


def test_should_check_default_setting_values():
    settings = Settings()
    assert settings.connect_timeout == 5.0
    assert settings.disconnect_timeout == 5.0
    assert settings.response_timeout == 5.0
    assert settings.max_message_size == 1024 * 1024
    assert settings.message_queue_size == 1
    assert settings.receive_buffer == 4 * 1024
    assert settings.svg_width == 150
    assert settings.extra_headers is None
    assert settings.tls_ca_file is None
    assert settings.tls_certificate_file is None
    assert settings.tls_key_file is None
    assert settings.tls_password is None


def test_should_read_values_from_environment(monkeypatch, tmp_path):
    ca = tmp_path / 'ca.pem'
    ca.write_text('fake ca')
    monkeypatch.setenv('WS_CONNECT_TIMEOUT', '1')
    monkeypatch.setenv('WS_RESPONSE_TIMEOUT', 'inf')
    monkeypatch.setenv('WS_EXTRA_HEADERS', '{"X-Foo": "bar"}')
    monkeypatch.setenv('ws_disconnect_timeout', '3')
    monkeypatch.setenv('WS_message_queue_size', '10')
    monkeypatch.setenv('ws_tls_ca_file', f'{ca}')
    settings = Settings()

    assert settings.connect_timeout == 1.0
    assert settings.disconnect_timeout == 3.0
    assert settings.response_timeout is math.inf
    assert settings.message_queue_size == 10
    assert settings.extra_headers == {'X-Foo': 'bar'}
    assert settings.tls_ca_file == ca
    assert settings.max_message_size == 1024 * 1024  # default value not changed


@pytest.mark.parametrize(
    'field',
    [
        'connect_timeout',
        'disconnect_timeout',
        'response_timeout',
        'message_queue_size',
        'max_message_size',
        'receive_buffer',
    ],
)
def test_should_raise_error_when_given_value_is_incorrect(monkeypatch, field):
    if field == 'message_queue_size':
        wrong_value = '-1'
        message = 'greater than or equal to 0'
    else:
        wrong_value = '0'
        message = 'greater than 0'
    monkeypatch.setenv(f'ws_{field}', wrong_value)

    with pytest.raises(pydantic.ValidationError) as exc_info:
        Settings()

    assert message in str(exc_info.value)


@pytest.fixture()
def clean_environment():
    """Helps to have a clean environment for tests."""
    for item in ['WS_CONNECT_TIMEOUT', 'WS_TLS_CERTIFICATE_FILE', 'ws_disconnect_timeout']:
        if item in os.environ:
            del os.environ[item]

    yield


class FakeEnviron:
    def __init__(self, monkeypatch):
        self._items = {}
        self._monkeypatch = monkeypatch

    def __getitem__(self, item):
        return self._items[item]

    def __setitem__(self, key, value):
        self._items[key] = value
        self._monkeypatch.setenv(key, value)


class TestGetConfigFromToml:
    """Tests function get_config_from_toml"""

    def test_should_return_none_when_ws_config_is_not_present(self, tmp_path):
        content = '[tool.isort]\n' 'profile = "black"\n'
        toml_file = tmp_path / 'pyproject.toml'
        toml_file.write_text(content)

        assert get_config_from_toml(toml_file) is None

    def test_should_return_none_if_file_is_not_a_valid_toml_file(self, tmp_path):
        file = tmp_path / 'pyproject.toml'
        file.write_text('Cameroon is a beautiful country!')

        assert get_config_from_toml(file) is None

    def test_should_return_data_when_ws_config_is_present(self, tmp_path):
        content = (
            '[tool.isort]\n' 'profile = "black"\n' '[tool.ws]\n' 'connect_timeout=4.0\n' 'disconnect_timeout=3.0\n'
        )
        toml_file = tmp_path / 'pyproject.toml'
        toml_file.write_text(content)

        assert get_config_from_toml(toml_file) == {'connect_timeout': 4.0, 'disconnect_timeout': 3.0}


class TestGetSettings:
    """Tests function get_settings"""

    def test_should_return_default_settings_when_config_file_does_not_exist(self):
        settings = get_settings()

        assert settings == Settings()

    def test_should_return_default_settings_when_toml_file_does_not_contain_ws_config(self, tmp_path, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        content = 'hello = "world"\n'
        config_file = tmp_path / 'pyproject.toml'
        config_file.write_text(content)
        settings = get_settings()

        assert settings == Settings()

    def test_should_return_default_settings_when_local_env_file_does_not_contain_ws_config(self, tmp_path, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        env_file = tmp_path / ENV_FILE
        env_file.write_text('foo=bar\n')
        settings = get_settings()

        assert settings == Settings()

    def test_should_return_default_settings_when_home_env_file_does_not_contain_ws_config(self, tmp_path, mocker):
        home = tmp_path / 'home'
        home.mkdir()
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        env_file = home / ENV_FILE
        env_file.write_text('foo=bar\n')
        settings = get_settings()

        assert settings == Settings()

    def test_should_return_default_settings_when_no_configuration_file_exist(self, tmp_path, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        mocker.patch('pathlib.Path.home', return_value=tmp_path)

        assert get_settings() == Settings()

    def test_should_return_settings_with_values_pulled_from_toml_file(self, tmp_path, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        content = '[tool.ws]\nconnect_timeout=3.0\nresponse_timeout=4.0\nfake_setting=2\n'
        config_file = tmp_path / 'pyproject.toml'
        config_file.write_text(content)
        settings = get_settings()

        assert settings.connect_timeout == 3.0
        assert settings.disconnect_timeout == 5.0
        assert settings.response_timeout == 4.0

    def test_should_read_values_from_local_env_file(self, tmp_path, monkeypatch, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        content = 'WS_CONNECT_TIMEOUT=1\nws_disconnect_timeout=3\nfoo=bar\n'
        env_file = tmp_path / ENV_FILE
        env_file.write_text(content)
        settings = get_settings()

        assert settings.connect_timeout == 1.0
        assert settings.disconnect_timeout == 3.0

    # the previous test sets environment variables (python-dotenv), this is why we need the following fixture
    # it makes some kind of dependency between tests, but I don't think it is a big deal here
    @pytest.mark.usefixtures('clean_environment')
    def test_should_read_values_from_home_env_file(self, tmp_path, mocker):
        home = tmp_path / 'home'
        home.mkdir()
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        mocker.patch('pathlib.Path.home', return_value=home)
        cert = tmp_path / 'cert.pem'
        cert.touch()
        content = f'WS_CONNECT_TIMEOUT=1\nWS_TLS_CERTIFICATE_FILE={cert}\nws_disconnect_timeout=3\nfoo=bar\n'
        env_file = home / ENV_FILE
        env_file.write_text(content)
        settings = get_settings()

        assert settings.connect_timeout == 1.0
        assert settings.disconnect_timeout == 3.0
        assert settings.tls_certificate_file == cert

    # the previous comment also applies here
    @pytest.mark.usefixtures('clean_environment')
    def test_should_check_function_prioritizes_toml_file_over_environment(self, tmp_path, monkeypatch, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        monkeypatch.setenv('WS_CONNECT_TIMEOUT', '2')
        config_file = tmp_path / 'pyproject.toml'
        config_file.write_text('[tool.ws]\nconnect_timeout=3.0\nresponse_timeout=4.0\nfake_setting=2\n')
        settings = get_settings()

        # connect_timeout must be 3 and not 2 because toml file has priority over environment variables
        assert settings.connect_timeout == 3.0
        assert settings.disconnect_timeout == 5.0
        assert settings.response_timeout == 4.0

    def test_should_check_function_prioritizes_toml_file_over_env_file(self, tmp_path, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        toml_file = tmp_path / 'pyproject.toml'
        toml_file.write_text('[tool.ws]\nconnect_timeout=3.0\nresponse_timeout=4.0\nfake_setting=2\n')
        env_file = tmp_path / ENV_FILE
        env_file.write_text('WS_CONNECT_TIMEOUT=4\nWS_DISCONNECT_TIMEOUT=3\n')

        settings = get_settings()

        assert settings.connect_timeout == 3.0  # note that it is 3 here instead of 4
        assert settings.disconnect_timeout == 5.0  # 5 instead of 3 because env file was never opened

    def test_should_check_function_prioritizes_local_env_file_to_home_env_file(self, tmp_path, mocker):
        home = tmp_path / 'home'
        home.mkdir()
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        mocker.patch('pathlib.Path.home', return_value=home)
        local_env_file = tmp_path / ENV_FILE
        home_env_file = home / ENV_FILE

        local_env_file.write_text('WS_CONNECT_TIMEOUT=4\n')
        home_env_file.write_text('WS_CONNECT_TIMEOUT=2\nWS_DISCONNECT_TIMEOUT=3\n')
        settings = get_settings()

        assert settings.connect_timeout == 4.0  # 4 instead of 2 because local env file has priority
        assert settings.disconnect_timeout == 5.0  # 5 instead of 3 because home env file was never opened
