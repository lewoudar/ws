"""Helper functions for testing purpose"""
import platform
import signal
import threading

import cffi
import trio
import trio_websocket

# This snippet code is taken from the trio project, more information can be found here:
# https://github.com/python-trio/trio/blob/39d01b268b1f354aa0f2290cdddd88fa8c6f6b73/trio/_util.py#L19-L65

if platform.system() == 'Windows':
    _ffi = cffi.FFI()
    _ffi.cdef('int raise(int);')
    _lib = _ffi.dlopen('api-ms-win-crt-runtime-l1-1-0.dll')
    signal_raise = getattr(_lib, 'raise')
else:

    def signal_raise(signum: int) -> None:
        signal.pthread_kill(threading.get_ident(), signum)


async def killer(seconds: int) -> None:
    await trio.sleep(seconds)
    signal_raise(signal.SIGINT)


async def server_handler(request) -> None:
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            await ws.send_message(message)
        except trio_websocket.ConnectionClosed:
            break
