from typing import Callable, TypeVar

import pydantic
import trio

from ws.console import console

# Create a generic type helps to preserve type annotations done by static analyzing tools
FuncCallable = TypeVar('FuncCallable', bound=Callable)


def catch_too_slow_error(func: FuncCallable) -> FuncCallable:
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except trio.TooSlowError:
            console.print('[error]Unable to get response on time')
            raise SystemExit(1)

    return wrapper


def catch_pydantic_error(func: FuncCallable) -> FuncCallable:
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except pydantic.ValidationError as e:
            console.print(f'[error]{e}')
            raise SystemExit(1)

    return wrapper
