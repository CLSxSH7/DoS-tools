from ipaddress import IPv4Network
from typing import List


def parse_ports(ports_csv: str) -> List[int]:
    ports: List[int] = []
    for x in ports_csv.split(","):
        x = x.strip()
        if not x:
            continue
        if x.isdigit():
            ports.append(int(x))
    return ports


def validate_cidr(cidr: str) -> IPv4Network:
    return IPv4Network(cidr)
