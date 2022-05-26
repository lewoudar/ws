# Installation

You can install the cli with `pip`:

```shell
$ pip install ws
```

or use a better package manager like [poetry](https://python-poetry.org/docs/):

```shell
# you probably want to add this dependency as a dev one, this is why I put -D into square brackets
$ poetry add [-D] ws
```

ws starts working from **python3.7** and also supports **pypy3**. It has the following dependencies:

- [trio](https://trio.readthedocs.io/en/stable/) / [anyio](https://anyio.readthedocs.io/en/stable/) for structured
  (async) concurrency support.
- [trio-websocket](https://trio-websocket.readthedocs.io/en/stable/) the library implementing the websocket protocol.
- [pydantic](https://pydantic-docs.helpmanual.io/) / [python-dotenv](https://pypi.org/project/python-dotenv/) for
  input validation and settings management.
- [certifi](https://pypi.org/project/certifi/) to manage TLS and certificates.
- [click](https://click.palletsprojects.com/en/8.1.x/) to write the cli.
- [click-didyoumean](https://pypi.org/project/click-didyoumean/) for command suggestions in case of typos.
- [rich](https://rich.readthedocs.io/en/latest/) for beautiful output display.
- [shellingham](https://pypi.org/project/shellingham/) to detect the shell used.
