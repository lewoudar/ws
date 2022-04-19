import ipaddress
import re
from typing import AnyStr, Optional, Union

import click
from pydantic import AnyUrl, BaseModel, ValidationError
from typing_extensions import Literal


class WsUrl(AnyUrl):
    allowed_schemes = {'ws', 'wss'}


class WsUrlModel(BaseModel):
    url: WsUrl


class HostModel(BaseModel):
    host: Union[Literal['localhost'], ipaddress.IPv6Address, ipaddress.IPv4Address]


class WsUrlParamType(click.ParamType):
    name = 'websocket url'

    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> str:
        if re.match(r':\d+$', value):
            value = f'ws://localhost{value}'
        try:
            WsUrlModel(url=value)
            return value
        except ValidationError:
            self.fail(f'{value} is not a valid websocket url', param, ctx)


def get_normalized_message(message: str, is_bytes: bool) -> AnyStr:
    if message.startswith('file@'):
        file = message[5:]
        mode = 'rb' if is_bytes else 'r'
        try:
            with open(file, mode) as f:
                return f.read()
        except FileNotFoundError:
            raise click.BadParameter(f'file {file} does not exist')
        except OSError:
            raise click.BadParameter(f'file {file} cannot be opened')
    else:
        return message.encode() if is_bytes else message


class ByteParamType(click.ParamType):
    name = 'bytes'

    def __init__(self, max_length: int = None):
        self._max_length = max_length

    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> bytes:
        original_value = value
        value = get_normalized_message(value, is_bytes=True)
        if self._max_length is not None:
            if value and len(value) > self._max_length:
                self.fail(f'{original_value} is longer than {self._max_length} bytes')

        return value


class TextParamType(click.ParamType):
    name = 'text'

    def __init__(self, max_length: int = None):
        self._max_length = max_length

    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> str:
        original_value = value
        value = get_normalized_message(value, is_bytes=False)
        if self._max_length is not None:
            if value and len(value) > self._max_length:
                self.fail(f'{original_value} is longer than {self._max_length} characters')

        return value


class HostParamType(click.ParamType):
    name = 'host'

    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> str:
        try:
            HostModel(host=value)
            return value
        except ValidationError:
            self.fail(f'{value} is neither "localhost" nor a valid ip address')


WS_URL = WsUrlParamType()
HOST = HostParamType()
