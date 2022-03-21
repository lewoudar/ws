from typing import Optional

import asyncclick as click
from pydantic import AnyUrl, BaseModel, ValidationError


class WsUrl(AnyUrl):
    allowed_schemes = {'ws', 'wss'}
    tld_required = True


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


WS_URL = WsUrlParamType()
