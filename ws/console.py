from rich.console import Console
from rich.style import Style
from rich.theme import Theme

data = {
    'error': Style(color='red'),
    'warning': Style(color='yellow'),
    'label': Style(color='yellow'),
    'info': Style(color='blue'),
}
custom_theme = Theme(data)

console = Console(theme=custom_theme)
