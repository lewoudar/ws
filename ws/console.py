import pathlib

from rich.console import Console
from rich.style import Style
from rich.theme import Theme

from ws.settings import Settings

data = {
    'error': Style(color='red'),
    'warning': Style(color='yellow'),
    'label': Style(color='yellow'),
    'info': Style(color='blue'),
    'success': Style(color='green'),
    'number': Style(color='cyan', bold=True),
    'prompt': Style(color='bright_cyan'),
}
custom_theme = Theme(data)

console = Console(theme=custom_theme)


def configure_console_recording(terminal: Console, settings: Settings, filename: str = None) -> None:
    if filename is not None:
        terminal.record = True
    terminal.width = settings.terminal_width


def save_output(terminal: Console, filename: str) -> None:
    file_path = pathlib.Path(filename)
    if file_path.suffix == '.html':
        terminal.save_html(filename)
    elif file_path.suffix == '.svg':
        terminal.save_svg(filename, title=file_path.name)
    else:
        terminal.save_text(filename)
