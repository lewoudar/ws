# ws

[![Pypi version](https://img.shields.io/pypi/v/ws.svg)](https://pypi.org/project/ws/)
![](https://github.com/lewoudar/ws/workflows/CI/badge.svg)
[![Coverage Status](https://codecov.io/gh/lewoudar/ws/branch/main/graphs/badge.svg?branch=main)](https://codecov.io/gh/lewoudar/ws)
[![Documentation Status](https://readthedocs.org/projects/pyws/badge/?version=latest)](https://pyws.readthedocs.io/en/latest/?badge=latest)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/wntrblm/nox)
[![License Apache 2](https://img.shields.io/hexpm/l/plug.svg)](http://www.apache.org/licenses/LICENSE-2.0)

A simple yet powerful websocket cli.

## Why?

Each time I work on a web project involving websockets, I found myself wanting a simple (cli) tool to test what I have
coded. What I often do is to write a python script using [websockets](https://websockets.readthedocs.io/en/stable/).
There are graphical tools like [Postman](https://www.postman.com/), but I'm not confortable with.
So I decided to write a cli tool for this purpose.

## Installation

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

## Usage

The usage is straightforward and the cli is well documented.

```shell
$ ws
Usage: ws [OPTIONS] COMMAND [ARGS]...

  A convenient websocket cli.

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

The first command to use is `install-completion` to have auto-completion for commands and options using the `TAB` key.
Auto-completion is available on `bash`, `fish` and `zsh`. For Windows users, I don't forget you (I'm also a Windows
user), support is planned for `Powershell` ;)

```shell
$ ws install-completion
# when the command succeeded, you should see the following message
Successfully installed completion script!
```

To play with the api you can use the websocket server kindly provided by the
[Postman](https://blog.postman.com/introducing-postman-websocket-echo-service/) team at wss://ws.postman-echo.com/raw or
spawn a new one with the following command:

```shell
# it will listen incoming messages on port 8000, to stop it, just type Ctrl+C
$ ws echo-server -p 8000
Running server on localhost:8000 💫
```

To *ping* the server, you can do this:

```shell
# :8000 is a
$ ws ping :8000
PING ws://localhost:8000 with 32 bytes of data
sequence=1, time=0.00s
```

To send a message, you can type this:

```shell
# Sends a text frame
$ ws text :8000 "hello world"  # on Windows it is probably better to use single quotes 'hello world'
Sent 11.0 B of data over the wire.

# Sends a binary frame
$ ws byte :8000 "hello world"
Sent 11.0 B of data over the wire.
```

If you know that you will have a long interaction with the server, it is probably better to use the `session` subcommand.

```shell
$ ws session wss://ws.postman-echo.com/raw
Welcome to the interactive websocket session! 🌟
For more information about commands, type the help command.
When you see <> around a word, it means this argument is optional.
To know more about a particular command type help <command>.
To close the session, you can type Ctrl+D or the quit command.

> ping "with payload"
PING wss://ws.postman-echo.com/raw with 12 bytes of data
Took 0.16s to receive a PONG.

> quit
Bye! 👋
```
## Documentation

The full documentation can be found at https://pyws.readthedocs.io

## Limitations

The cli does not support [RFC 7692](https://datatracker.ietf.org/doc/html/rfc7692) and
[RFC 8441](https://datatracker.ietf.org/doc/html/rfc8441) because `trio_websocket` the underlying library used for
websockets does not support it.
