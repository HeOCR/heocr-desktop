"""The app works offline, and this makes sure of it.

``enforce()`` is called first thing at start-up. From then on any attempt by Python code in the app to
open a network connection to another machine raises ``OfflineError``. Connections to this machine
(loopback, and local sockets) still work, since the window's toolkit may use them. The interface itself
loads no remote content: its page is inline, under a content security policy that allows nothing from
outside.
"""
from __future__ import annotations

import ipaddress
import socket


class OfflineError(OSError):
    pass


_LOCAL_NAMES = {"localhost", "localhost.localdomain", ""}


def _is_local(address) -> bool:
    if not isinstance(address, tuple) or not address:
        return True  # AF_UNIX paths and the like
    host = address[0]
    if isinstance(host, bytes):
        host = host.decode(errors="replace")
    if str(host).lower() in _LOCAL_NAMES:
        return True
    try:
        return ipaddress.ip_address(str(host).split("%", 1)[0]).is_loopback
    except ValueError:
        return False  # a name: resolving it would already be a network call


_enforced = False


def enforce() -> None:
    global _enforced
    if _enforced:
        return
    original_connect, original_connect_ex = socket.socket.connect, socket.socket.connect_ex

    def connect(self, address):
        if not _is_local(address):
            raise OfflineError(f"HeOCR works offline: no network connection to {address[0]!r}")
        return original_connect(self, address)

    def connect_ex(self, address):
        if not _is_local(address):
            raise OfflineError(f"HeOCR works offline: no network connection to {address[0]!r}")
        return original_connect_ex(self, address)

    def getaddrinfo(host, *args, **kwargs):
        if not _is_local((host,)):
            raise OfflineError(f"HeOCR works offline: no name lookup of {host!r}")
        return _getaddrinfo(host, *args, **kwargs)

    _getaddrinfo = socket.getaddrinfo
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.getaddrinfo = getaddrinfo
    _enforced = True
