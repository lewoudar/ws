import asyncclick as click
import pytest

from ws.parameters import WsUrlParamType


class TestWsUrlParamType:
    """Tests parameter WsUrlParamType"""

    @pytest.mark.parametrize('url', ['ws://websocket', 'https://websocket.com'])
    def test_should_raise_error_when_given_value_is_not_a_websocket_url(self, url):
        with pytest.raises(click.BadParameter) as exc_info:
            param = WsUrlParamType()
            param.convert(url, None, None)

        assert f'{url} is not a valid websocket url' == str(exc_info.value)

    @pytest.mark.parametrize('url', ['ws://websocket.com', 'wss://websocket.com'])
    def test_should_return_websocket_url(self, url):
        param = WsUrlParamType()
        assert param.convert(url, None, None) == url
