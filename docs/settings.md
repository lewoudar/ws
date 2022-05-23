# Settings

There are a number of settings you can configure to run `ws`. We will explore the different methods to do that.

## pyproject.toml

Like I said in the introduction, I created this project to test features I implement in various web projects. So the
first obvious place for me to configure it is in the `pyproject.toml` file which is becoming more and more popular
to configure the behaviour of a cli tool. Some well-known projects like
[pytest](https://docs.pytest.org/en/latest/reference/customize.html#pyproject-toml) and
[black](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html#configuration-via-a-file)
use it for their configuration.

The following parameters can be configured. Note that they all have default values if no one is provided.

- `connect_timeout`: The time in seconds to connect to the websocket server. Defaults to 5s.
- `disconnect_timeout`: The time in seconds to disconnect from the websocket server. Defaults to 5s.
- `response_timeout`: The time in seconds to get a **ping** response (aka a **pong**). Defaults to 5s. You can pass
  the string value `inf` to mean that you don't want a limit for this value.
- `message_queue_size`: The number of incoming messages to store in an internal buffer before treating them.
  Defaults to 1. **Change this parameter with cautious**.
- `max_message_size`: The maximum size allowed for an individual message. Defaults to 1 KB. Again, you should know what
  you do if you want to change this parameter.
- `extra_headers`: A list of HTTP headers. The first step to establish a connection to a websocket server is to make
  an HTTP upgrade request. During this process, you may need to provide additional information like *cookies* or an
  *authorization* header. For example `extra_headers = [["X-Foo", "bar"], ["Authorization", "Bearer token"]]` defines
  two headers `X-Foo` and `Authorization` respectively with values `bar` and `Bearer token`. This setting defaults to
  `None` meaning there are no extra headers.
- `terminal_width`: You can configure the size of the output displayed in the terminal. It is especially useful when
  you want to export terminal output in a file like you can do with `listen` or `session` commands. It defaults to
  whatever [rich](https://rich.readthedocs.io/en/latest/) considers the default.
- `tls_ca_file`: Path to a certificate authority file containing certificates to authenticate the communication
  between client and server. Defaults to `None`. If TLS is involved in the connection, and you don't provide this
  setting then the CA file will default to the one used by the [ssl](https://docs.python.org/3/library/ssl.html) module.
- `tls_certificate_file`: Path to a custom certificate to use to authenticate to a server. Defaults to `None`.
- `tls_key_file`: Path to the private key related to the `tls_certificate_file`. You can't provide this setting without
  the former.
- `tls_password`: Password related to the `tls_key_file` file. You can't provide this setting without the former.


!!! info
    For more information about size parameters like `message_queue_size` you can look this
    [section](https://trio-websocket.readthedocs.io/en/stable/backpressure.html) of `trio_websoocket` documentation.


## Environment files

The other way to configure `ws` is via environment files. If no `pyproject.toml` is found, the program will look for
the presence of `.ws.env` file in the current working directory and as a last resort in the home directory.
The different settings available for configuration are the same from the previous section except that they are prefixed
by `ws_`. Here is an example of an environment file:

```shell
# .ws.env

WS_CONNECT_TIMEOUT=3
# the string "inf" means we don't want a timeout for the ping response
WS_RESPONSE_TIMEOUT=inf
# the value here is in json
WS_EXTRA_HEADERS='[["X-Foo", "bar"], ["Authorization", "Bearer token"]]'
# note that we can use variables like in bash
RELATIVE_PATH=Documents/tls/file.pem
WS_TLS_CA_FILE=${HOME}/${RELATIVE_PATH}
```

Notes:

- For the `extra_headers` setting, the value **must be** a json string representing the array of headers.
- We can use **variables** like we usually do in a **shell** script.

!!! info
    You can directly define environment variables if you prefer not to use an environment file.

## Precedence

In case we have multiple configuration files, only one will be chosen. The behaviour of `ws` is to search for the files
in this order from the highest priority to the lowest:

- `pyproject.toml`
- `.ws.env` in the current working directory
- `.ws.env` in the home directory

Note:

- This means that `pyproject.toml` has precedence over **environment variables**.
