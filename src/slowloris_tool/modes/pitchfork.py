from __future__ import annotations
from dataclasses import dataclass
from ipaddress import IPv4Network
from typing import List
from ..core.strategy import BaseOptions, PitchforkStrategy


@dataclass
class PitchforkArgs:
    subnet: IPv4Network
    ports: List[int]
    sockets: int
    https: bool
    randuseragents: bool
    duration: int
    threads: int


def build(subnet: IPv4Network, ports: List[int], sockets: int, https: bool, randua: bool, duration: int,
          threads: int) -> PitchforkStrategy:
    opts = BaseOptions(sockets=sockets, https=https, randua=randua)
    return PitchforkStrategy(subnet=subnet, ports=ports, opts=opts, duration_s=duration, max_threads=threads)
