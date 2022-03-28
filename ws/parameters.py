from typing import AnyStr, Optional

import click
from pydantic import AnyUrl, BaseModel, ValidationError


class WsUrl(AnyUrl):
    allowed_schemes = {'ws', 'wss'}


class WsUrlModel(BaseModel):
    url: WsUrl


class WsUrlParamType(click.ParamType):
    name = 'websocket url'

    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> str:
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


WS_URL = WsUrlParamType()
