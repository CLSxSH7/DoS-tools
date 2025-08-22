from __future__ import annotations
import logging
import random
import socket
import ssl
from typing import Optional, List

DEFAULT_TIMEOUT = 4
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
]


def wrap_ssl_if_needed(sock: socket.socket, https: bool, server_hostname: Optional[str]):
    if not https:
        return sock
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx.wrap_socket(sock, server_hostname=server_hostname)


def send_line(sock: socket.socket, line: str) -> None:
    sock.send(f"{line}\r\n".encode("utf-8"))


def send_header(sock: socket.socket, name: str, value) -> None:
    send_line(sock, f"{name}: {value}")


def init_socket(
        ip: str,
        port: int,
        https: bool,
        rand_user_agents: bool,
        host_header: Optional[str] = None,
        sni_name: Optional[str] = None,
) -> Optional[socket.socket]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(DEFAULT_TIMEOUT)
        s = wrap_ssl_if_needed(s, https, sni_name)
        s.connect((ip, port))

        send_line(s, f"GET /?{random.randint(0, 9999)} HTTP/1.1")
        if host_header:
            send_header(s, "Host", host_header)

        ua = random.choice(USER_AGENTS) if rand_user_agents else USER_AGENTS[0]
        send_header(s, "User-Agent", ua)
        send_header(s, "Accept-language", "en-US,en,q=0.5")
        return s
    except Exception as e:
        logging.debug(f"Failed to create socket: {e}")
        return None


def iteration_keepalive(
        sockets: List[socket.socket],
        desired_count: int,
        ip: str,
        port: int,
        https: bool,
        rand_user_agents: bool,
        host_header: Optional[str],
        sni_name: Optional[str],
) -> None:
    # Send a bogus header and recreate missing sockets
    for s in list(sockets):
        try:
            send_header(s, "X-a", random.randint(1, 5000))
        except socket.error:
            try:
                s.close()
            except Exception:
                pass
            sockets.remove(s)

    missing = desired_count - len(sockets)
    if missing > 0:
        logging.info(f"Creating {missing} new sockets...")
        for _ in range(missing):
            s_new = init_socket(ip, port, https, rand_user_agents, host_header, sni_name)
            if s_new:
                sockets.append(s_new)


def is_ip_reachable(ip: str, port: int = 80) -> bool:
    """Lightweight reachability check (TCP connect)."""
    try:
        socket.setdefaulttimeout(3)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False


def is_port_open(ip: str, port: int) -> bool:
    """Check if a port is open and responds to a simple HTTP probe."""
    try:
        socket.setdefaulttimeout(3)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.send(b"GET / HTTP/1.1\r\nHost: test\r\n\r\n")
        _ = s.recv(1024)
        s.close()
        return True
    except Exception:
        return False
