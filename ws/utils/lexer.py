from pygments.lexer import RegexLexer, bygroups, include
from pygments.token import Keyword, Name, Number, Operator, Punctuation, String, Text


# Honestly I don't understand how to write a lexer. I just copy the BashLexer class
# add what appears necessary for the "basic" property and removes stuff unnecessary
# in the same property
class WSLexer(RegexLexer):
    tokens = {
        'root': [
            include('basic'),
            (r'`', String.Backtick, 'backticks'),
            include('data'),
            include('interp'),
        ],
        'interp': [
            (r'\$\(\(', Keyword, 'math'),
            (r'\$\(', Keyword, 'paren'),
            (r'\$\{#?', String.Interpol, 'curly'),
            (r'\$[a-zA-Z_]\w*', Name.Variable),  # user variable
            (r'\$(?:\d+|[#$?!_*@-])', Name.Variable),  # builtin
            (r'\$', Text),
        ],
        'basic': [(r'\b(help|ping|pong|text|byte|close|quit)(\s*)\b', bygroups(Keyword, Text))],
        'data': [
            (r'(?s)\$?"(\\.|[^"\\$])*"', String.Double),
            (r'"', String.Double, 'string'),
            (r"(?s)\$'(\\\\|\\[0-7]+|\\.|[^'\\])*'", String.Single),
            (r"(?s)'.*?'", String.Single),
            (r';', Punctuation),
            (r'&', Punctuation),
            (r'\|', Punctuation),
            (r'\s+', Text),
            (r'\d+\b', Number),
            (r'[^=\s\[\]{}()$"\'`\\<&|;]+', Text),
            (r'<', Text),
        ],
        'string': [
            (r'"', String.Double, '#pop'),
            (r'(?s)(\\\\|\\[0-7]+|\\.|[^"\\$])+', String.Double),
            include('interp'),
        ],
        'curly': [
            (r'\}', String.Interpol, '#pop'),
            (r':-', Keyword),
            (r'\w+', Name.Variable),
            (r'[^}:"\'`$\\]+', Punctuation),
            (r':', Punctuation),
            include('root'),
        ],
        'paren': [
            (r'\)', Keyword, '#pop'),
            include('root'),
        ],
        'math': [
            (r'\)\)', Keyword, '#pop'),
            (r'[-+*/%^|&]|\*\*|\|\|', Operator),
            (r'\d+#\d+', Number),
            (r'\d+#(?! )', Number),
            (r'\d+', Number),
            include('root'),
        ],
        'backticks': [
            (r'`', String.Backtick, '#pop'),
            include('root'),
        ],
    }
