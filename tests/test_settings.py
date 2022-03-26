from ws.settings import Settings, get_config_from_toml, get_settings


def test_should_check_default_setting_values():
    settings = Settings()
    assert settings.connect_timeout == 5.0
    assert settings.disconnect_timeout == 5.0
    assert settings.response_timeout == 5.0
    assert settings.max_message_size == 1024 * 1024
    assert settings.message_queue_size == 1
    assert settings.receive_buffer == 4 * 1024
    assert settings.extra_headers is None


def test_should_read_values_from_environment(monkeypatch):
    monkeypatch.setenv('WS_CONNECT_TIMEOUT', '1')
    monkeypatch.setenv('WS_EXTRA_HEADERS', '{"X-Foo": "bar"}')
    monkeypatch.setenv('ws_disconnect_timeout', '3')
    monkeypatch.setenv('WS_message_queue_size', '10')
    settings = Settings()

    assert settings.connect_timeout == 1.0
    assert settings.disconnect_timeout == 3.0
    assert settings.response_timeout == 5.0
    assert settings.message_queue_size == 10
    assert settings.extra_headers == {'X-Foo': 'bar'}


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

    def test_should_return_default_settings_when_config_file_does_not_contain_ws_config(self, tmp_path, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        content = 'hello = "world"\n'
        config_file = tmp_path / 'pyproject.toml'
        config_file.write_text(content)
        settings = get_settings()

        assert settings == Settings()

    def test_should_return_settings_with_values_pulled_from_config_file(self, tmp_path, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        content = '[tool.ws]\n' 'connect_timeout=3.0\n' 'response_timeout=4.0\n' 'fake_setting=2\n'
        config_file = tmp_path / 'pyproject.toml'
        config_file.write_text(content)
        settings = get_settings()

        assert settings.connect_timeout == 3.0
        assert settings.disconnect_timeout == 5.0
        assert settings.response_timeout == 4.0

    def test_should_check_function_prioritizes_config_file_over_environment(self, tmp_path, monkeypatch, mocker):
        mocker.patch('pathlib.Path.cwd', return_value=tmp_path)
        monkeypatch.setenv('WS_CONNECT_TIMEOUT', '2')
        content = '[tool.ws]\n' 'connect_timeout=3.0\n' 'response_timeout=4.0\n' 'fake_setting=2\n'
        config_file = tmp_path / 'pyproject.toml'
        config_file.write_text(content)
        settings = get_settings()

        # connect_timeout must be 3 and not 2
        assert settings.connect_timeout == 3.0
        assert settings.disconnect_timeout == 5.0
        assert settings.response_timeout == 4.0
