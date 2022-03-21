"""Helper functions for testing purpose"""
import platform
import signal
import threading

import cffi
import trio

# This snippet code is taken from the trio project, more information can be found here:
# https://github.com/python-trio/trio/blob/39d01b268b1f354aa0f2290cdddd88fa8c6f6b73/trio/_util.py#L19-L65
if platform.system() == 'Windows':
    _ffi = cffi.FFI()
    _ffi.cdef('int raise(int);')
    _lib = _ffi.dlopen('api-ms-win-crt-runtime-l1-1-0.dll')
    signal_raise = getattr(_lib, 'raise')
else:

    def signal_raise(signum):
        signal.pthread_kill(threading.get_ident(), signum)


async def killer() -> None:
    await trio.sleep(5)
    signal_raise(signal.SIGINT)
