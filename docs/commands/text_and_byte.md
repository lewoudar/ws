## text

This command lets you send text data to a websocket server.

```shell
$ ws text -h
Usage: ws text [OPTIONS] URL MESSAGE

  Sends text message on URL endpoint.

Options:
  -h, --help  Show this message and exit.
```

### Example usage

The basic usage is at follows:

```shell
$ ws text wss://ws.postman-echo.com/raw "hello world"
Sent 11.0 B of data over the wire.
```

The previous command sends 11 bytes of data to the websocket server. So yeah the meaning of **B** here is **bytes**.
The following abbreviations are used for different types of unit:

- B => bytes
- KB => kilobytes
- MB => megabytes
- GB => gigabytes (the highest unit)

If you want to pass json data, it should be a json string.

```shell
$ ws text wss://ws.postman-echo.com/raw '{"hello": "world"}'
Sent 18.0 B of data over the wire.
```

If you want to send a lot of data at once, it is not very convenient to pass it as a raw string. You can pass a file
and the command will send its content.

```shell
# long_text.txt
This is a very long message!
```

```shell
$ ws text wss://ws.postman-echo.com/raw file@long_text.txt
Sent 28.0 B of data over the wire.
```

Note that the pattern is **file@** followed by the path to the file to read.

## Byte

This command lets you send **binary** data to a websocket server.

```shell
$ ws byte -h
Usage: ws byte [OPTIONS] URL MESSAGE

  Sends binary message to URL endpoint.

Options:
  -h, --help  Show this message and exit.
```

### Example usage

Basic usage:

```shell
$ ws byte wss://ws.postman-echo.com/raw "hello world"
Sent 11.0 B of data over the wire.
```

The usage is similar to the [text](#text) command, so feel free to look at the examples above.
