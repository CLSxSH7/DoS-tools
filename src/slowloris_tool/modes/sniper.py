from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from ..core.strategy import BaseOptions, SniperStrategy


def _enable_socks5_if_needed(socks5: Optional[str]) -> None:
    """
    Ativa proxy SOCKS5 globalmente (monkeypatch) se informado.
    Requer PySocks: pip install PySocks
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
            f"Falha ao configurar SOCKS5 '{socks5}'. "
            f"Instale PySocks (pip install PySocks). Erro: {e}"
        )


@dataclass
class SniperArgs:
    ip: str
    port: int
    sockets: int
    https: bool
    randuseragents: bool
    sleeptime: int
    socks5: Optional[str] = None


def build(
        ip: str,
        port: int,
        sockets: int,
        https: bool,
        randua: bool,
        sleeptime: int,
        socks5: Optional[str] = None,
) -> SniperStrategy:
    _enable_socks5_if_needed(socks5)
    opts = BaseOptions(sockets=sockets, https=https, randua=randua, sleeptime=sleeptime)
    return SniperStrategy(ip=ip, port=port, opts=opts)
