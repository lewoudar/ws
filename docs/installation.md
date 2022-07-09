# Installation

You can install the cli with `pip`:

```shell
$ pip install websockets-cli
```

or use a better package manager like [poetry](https://python-poetry.org/docs/):

```shell
# you probably want to add this dependency as a dev one, this is why I put -D into square brackets
$ poetry add [-D] websockets-cli
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


To confirm the installation works, you can type the command name in the terminal.

```shell
$ ws
Usage: ws [OPTIONS] COMMAND [ARGS]...

  A convenient websocket cli.

  Example usage:

  # listens incoming messages from endpoint ws://localhost:8000/path
  $ ws listen ws://localhost:8000/path

  # sends text "hello world" in a text frame
  $ ws text wss://ws.postman-echo.com/raw "hello world"

  # sends the content from json file "hello.json" in a binary frame
  $ ws byte wss://ws.postman-echo.com/raw file@hello.json

Options:
  --version   Show the version and exit.
  -h, --help  Show this message and exit.

Commands:
  byte                Sends binary message to URL endpoint.
  echo-server         Runs an echo websocket server.
  install-completion  Install completion script for bash, zsh and fish...
  listen              Listens messages on a given URL.
  ping                Pings a websocket server located at URL.
  pong                Sends a pong to websocket server located at URL.
  session             Opens an interactive session to communicate with...
  tail                An emulator of the tail unix command that output...
  text                Sends text message on URL endpoint.
```
