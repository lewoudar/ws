from trio_websocket import serve_websocket

from tests.helpers import server_handler
from ws.commands.session import interact


async def test_should_print_documentation_and_exit_program(capsys, mocker, nursery):
    mocker.patch('ws.console.console.input', lambda prompt: 'quit')
    await nursery.start(serve_websocket, server_handler, 'localhost', 1234, None)
    await interact('ws://localhost:1234')

    output = capsys.readouterr().out
    assert 'Welcome to the interactive websocket session! 🌟\n' in output
    assert 'For more information about commands, type the help command.\n' in output
    assert 'When you see <> around a word, it means this argument is optional.\n' in output
    assert 'To know more about a particular command type help <command>.\n' in output
    assert 'To close the session, you can type Ctrl+D or the quit command.\n' in output
    assert 'Bye! 👋\n' in output
