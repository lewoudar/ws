from pygments.lexer import RegexLexer

from ws.utils.lexer import WSLexer


def test_should_check_ws_lexer_inherits_regex_lexer():
    assert issubclass(WSLexer, RegexLexer)


def test_should_check_basic_property_contains_all_ws_session_commands():
    assert WSLexer.tokens['basic'][0][0] == r'\b(help|ping|pong|text|byte|close|quit)(\s*)\b'
