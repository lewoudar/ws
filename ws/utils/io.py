import io
import signal
from typing import Any, AsyncIterator, Callable

import anyio
import trio

from ws.console import console


async def signal_handler(scope: trio.CancelScope) -> None:
    with trio.open_signal_receiver(signal.SIGINT, signal.SIGTERM) as signals:
        async for signum in signals:
            key = 'Ctrl+C' if signum == signal.SIGINT else 'SIGTERM'
            console.print(f'[info]Program was interrupted by {key}, good bye! :waving_hand:')

            # noinspection PyAsyncCall
            scope.cancel()
            return


async def function_runner(scope: trio.CancelScope, function: Callable, *args: Any) -> None:
    await function(*args)
    # noinspection PyAsyncCall
    scope.cancel()


# it is a good idea to read the file in byte mode, more information can be found
# in the answers of this post: https://stackoverflow.com/a/23646049/7181806
async def reverse_read_lines(file: str) -> AsyncIterator[bytes]:
    async with await anyio.open_file(file, 'rb') as f:
        await f.seek(0, whence=io.SEEK_END)
        pointer = await f.tell()
        buffer = bytearray()

        while pointer >= 0:
            await f.seek(pointer)
            # we read character by character
            pointer -= 1
            char = await f.read(1)

            # if we reach '\n' this means we have read one line and can return it
            if char == b'\n':
                yield buffer[::-1]
                buffer.clear()
            else:
                buffer += char

        # if the buffer is not empty, it is the first line, so we return it
        if buffer:
            yield buffer[::-1]


async def sleep_until(cancel_scope: trio.CancelScope, duration: float = None) -> None:
    if duration is None:
        await trio.sleep_forever()
    else:
        await trio.sleep(duration)
        cancel_scope.cancel()
