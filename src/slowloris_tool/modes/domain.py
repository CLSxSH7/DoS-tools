from __future__ import annotations
import socket
from dataclasses import dataclass
from typing import Optional
from ..core.strategy import BaseOptions, DomainStrategy


def _enable_socks5_if_needed(socks5: Optional[str]) -> None:
    """
    Enable a global SOCKS5 proxy (monkeypatch) if provided.
    Requires PySocks: pip install PySocks
    """
    if not socks5:
        return
    try:
        import socks  # type: ignore
        import socket as pysocket
        host, port = socks5.split(":")
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, host, int(port))
        pysocket.socket = socks.socksocket  # type: ignore[attr-defined]
    except Exception as e:
        raise SystemExit(
            f"Failed to configure SOCKS5 '{socks5}'. "
            f"Install PySocks (pip install PySocks). Error: {e}"
        )


@dataclass
class DomainArgs:
    host: str
    port: int
    sockets: int
    https: bool
    randuseragents: bool
    sleeptime: int
    socks5: Optional[str] = None


def build(
        host: str,
        port: int,
        sockets: int,
        https: bool,
        randua: bool,
        sleeptime: int,
        socks5: Optional[str] = None,
) -> DomainStrategy:
    _enable_socks5_if_needed(socks5)
    try:
        resolved_ip = socket.gethostbyname(host)
    except socket.gaierror:
        raise SystemExit(f"DNS error resolving {host}")
    opts = BaseOptions(sockets=sockets, https=https, randua=randua, sleeptime=sleeptime)
    return DomainStrategy(host=host, ip=resolved_ip, port=port, opts=opts)
