# echo-server

This command lets you spawn a simple websocket server which replies to all incoming messages by sending them back.

```shell
ws echo-server -h
Usage: ws echo-server [OPTIONS]

  Runs an echo websocket server. The server will return the data sent by the
  client.

Options:
  -H, --host HOST           Host to bind the server.  [default: localhost]
  -p, --port INTEGER RANGE  Port to bind the server.  [default: 80;
                            0<=x<=65535]
  -c, --cert-file FILE      Server certificate.
  -k, --key-file FILE       Private key bound to the certificate.
  -h, --help                Show this message and exit.
```

Example usage:

Listens only ipv6 addresses on port 8000.

```shell
$ ws echo-server -H ::1 -p 8000
Running server on ::1:8000 💫
# To stop the server, you can just tap Ctrl+C
^CProgram was interrupted by Ctrl+C, good bye! 👋
```

Serves with a custom certificate and key file.

```shell
$ ws echo-server --cert-file cert.pem --key-file key.pem
```

!!! note
    You can close the server by sending a `SIGTERM` signal to the process on linux/unix systems.
