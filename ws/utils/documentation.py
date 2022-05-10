"""This module contains documentation related to the session command"""

INTRODUCTION = """Welcome to the interactive websocket session! :glowing_star:
For more information about commands, type the [info]help[/] command.
When you see [bold]<>[/] around a word, it means this argument is optional.
To know more about a particular command type [info]help[/] <command>.
To close the session, you can type [bold]Ctrl+D[/] or the [info]quit[/] command.
"""

HELP = """The session program lets you interact with a websocket endpoint with the following commands:

• [info]ping[/] <message>: Sends a ping with an optional message.
• [info]pong[/] <message>: Sends a pong with an optional message.
• [info]text[/] [green]message[/]: Sends text message.
• [info]byte[/] [green]message[/]: Sends byte message.
• [info]close[/] <code> <reason>: Closes the websocket connection with an optional code and message.
• [info]quit[/]: equivalent to [bold]close 1000[/].
"""


PING_HELP = """The ping command sends a PING control frame with an optional message.

Example usage:

A random 32 bytes of data will be sent to the server as ping payload.
```shell
> ping
```

Sends a ping with the message "hello world". The message length **must not** be greater than `125`.
```shell
> ping "hello world"
```
"""

PONG_HELP = """The pong command sends a PONG control frame with an optional message.

Example usage:

An empty pong will be sent on the wire.
```shell
> pong
```

Sends a pong with the message "hello world". The message length **must not** be greater than `125` bytes.
```shell
> pong "hello world"
```
"""

CLOSE_HELP = """Closes the session given a code and an optional reason.

Example usage:

If no code is given, 1000 is considered as default meaning a normal closure. Thus, it is equivalent to the **quit**
command.
```shell
> close
```

Closes the connection with a code 1001 and no message.
```shell
> close 1001
```

Closes the connection with a code 1003 and a message "received unknown data".

The message length **must not** be greater than `123` bytes.
```shell
> close 1003 'received unknown data'
```

To know more about close codes, please refer to the [RFC](https://datatracker.ietf.org/doc/html/rfc6455#section-7.4.1).
"""

QUIT_HELP = """Exits the session program.

Technically it is the equivalent of the following command:

```shell
> close 1000
```
"""

TEXT_HELP = """Sends a TEXT frame with given data.

Example usage:

Sends "hello world" in a TEXT frame.
```shell
> text 'hello world'
```

Sends the content of *foo.txt* as a TEXT frame.
```txt
# foo.txt
Hello from Cameroon!
```

Notice the pattern **file@** which a necessary prefix to send content from a file.
```shell
> text file@foo.txt
```
"""

BYTE_HELP = """Sends a BINARY frame with given data.

Example usage:

Sends "hello world" in a BINARY frame.
```shell
> byte 'hello world'
```

Sends the content of *foo.txt* as a BINARY frame.
```txt
# foo.txt
Hello from Cameroon!
```

Notice the pattern **file@** which a necessary prefix to send content from a file.
```shell
> byte file@foo.txt
```
"""
