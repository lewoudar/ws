import pytest

from ws.console import Console, configure_console_recording, custom_theme, save_output
from ws.settings import get_settings


class TestConfigureConsoleRecording:
    """Tests function configure_console_recording"""

    @pytest.mark.parametrize(('filename', 'record'), [(None, False), ('file.txt', True)])
    def test_should_correctly_configure_terminal_record_property_given_correct_input(self, filename, record):
        console = Console()
        settings = get_settings()
        configure_console_recording(console, settings, filename)

        assert console.record is record
        assert console.width != settings.svg_width

    def test_should_correctly_configure_terminal_width_and_record_properties_given_correct_input(self):
        filename = 'foo.svg'
        console = Console()
        settings = get_settings()
        configure_console_recording(console, settings, filename)

        assert console.record is True
        assert console.width == settings.svg_width

    def test_should_check_svg_width_is_taken_from_environnement_variable(self, monkeypatch):
        monkeypatch.setenv('WS_SVG_WIDTH', '120')
        filename = 'foo.svg'
        console = Console()
        settings = get_settings()
        configure_console_recording(console, settings, filename)

        assert console.record is True
        assert console.width == 120


class TestSaveOutput:
    """Tests function save_output"""

    @pytest.mark.parametrize('filename', ['file.html', 'file.svg', 'file.txt'])
    def test_should_save_output_given_correct_input(self, tmp_path, filename):
        file_path = tmp_path / filename
        console = Console(theme=custom_theme)
        settings = get_settings()
        configure_console_recording(console, settings, f'{file_path}')
        console.print('hello world')

        assert not file_path.exists()
        save_output(console, f'{file_path}')

        assert file_path.exists()
        output = file_path.read_text()
        assert 'hello world' in output
        # we check the title of the svg file
        if file_path.suffix == '.svg':
            assert file_path.name in output
