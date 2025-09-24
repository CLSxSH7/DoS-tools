#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from src.slowloris_tool.cli import main as cli_main


def ask(prompt: str, default: str = None) -> str:
    """Prompt helper: shows default when provided and returns the typed or default value."""
    if default is None:
        return input(f"{prompt}: ").strip()
    val = input(f"{prompt} [{default}]: ").strip()
    return val or default


def interactive_menu():
    """
    Build arguments via interactive prompts and return a list of args (excluding argv[0]).
    Includes the new modes: tcpflood and synflood.
    """
    print("Slowloris — choose a mode:")
    print("1) sniper   (single IP)")
    print("2) domain   (domain)")
    print("3) pitchfork(subnet/ports)")
    print("4) tcpflood (TCP flood, ramp-up)")
    print("5) synflood (SYN flood, ramp-up)")
    choice = input("> ").strip()

    args = []

    if choice == "1":
        args.append("sniper")
        ip = ask("Target IP")
        if not ip:
            print("IP is required.")
            return None
        args += ["-p", ask("Port", "80")]
        socks = ask("SOCKS5 (host:port) or empty", "")
        if socks:
            args += ["--socks5", socks]
        args += ["-s", ask("Number of sockets", "150")]
        if ask("Use HTTPS? (y/n)", "n").lower().startswith("y"):
            args += ["--https"]
        if ask("Randomize User-Agent? (y/n)", "n").lower().startswith("y"):
            args += ["-ua"]
        args += ["--sleeptime", ask("Header interval (s)", "15")]
        args.append(ip)

    elif choice == "2":
        args.append("domain")
        host = ask("Domain (no protocol)")
        if not host:
            print("Domain is required.")
            return None
        args += ["-p", ask("Port", "80")]
        socks = ask("SOCKS5 (host:port) or empty", "")
        if socks:
            args += ["--socks5", socks]
        args += ["-s", ask("Number of sockets", "150")]
        if ask("Use HTTPS? (y/n)", "n").lower().startswith("y"):
            args += ["--https"]
        if ask("Randomize User-Agent? (y/n)", "n").lower().startswith("y"):
            args += ["-ua"]
        args += ["--sleeptime", ask("Header interval (s)", "15")]
        args.append(host)

    elif choice == "3":
        args.append("pitchfork")
        subnet = ask("Subnet CIDR (e.g., 192.168.0.0/24)")
        if not subnet:
            print("Subnet is required.")
            return None
        args.append(subnet)
        args += ["-P", ask("Ports (CSV)", "80,443,8080")]
        args += ["-s", ask("Sockets per IP/port", "200")]
        if ask("Use HTTPS? (y/n)", "n").lower().startswith("y"):
            args += ["--https"]
        if ask("Randomize User-Agent? (y/n)", "n").lower().startswith("y"):
            args += ["-ua"]

    elif choice == "4":
        # NEW: tcpflood
        args.append("tcpflood")
        host = ask("Target host (IP or hostname)")
        if not host:
            print("Host is required.")
            return None
        args += ["-p", ask("Port", "80")]
        args += ["--start", ask("Initial sockets", "10")]
        args += ["--step", ask("Add sockets per step", "10")]
        args += ["--max", ask("Max sockets", "200")]
        args += ["--step-duration", ask("Seconds per step", "10")]
        args += ["--payload-size", ask("Payload bytes per send", "256")]
        args += ["--send-interval", ask("Send interval per socket (s)", "1.0")]
        args += ["--impact-latency", ask("Latency threshold to stop (s)", "1.0")]
        args.append(host)

    elif choice == "5":
        # NEW: synflood
        args.append("synflood")
        host = ask("Target host (IP or hostname)")
        if not host:
            print("Host is required.")
            return None
        args += ["-p", ask("Port", "80")]
        args += ["--start", ask("Initial pps", "50")]
        args += ["--step", ask("Increase pps per step", "50")]
        args += ["--max", ask("Max pps", "1000")]
        args += ["--step-duration", ask("Seconds per step", "10")]
        args += ["--impact-latency", ask("Latency threshold to stop (s)", "1.0")]
        args.append(host)

    else:
        print("Invalid option.")
        return None

    return args


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    built_args = interactive_menu()
    if not built_args:
        sys.exit(1)

    sys.argv = [sys.argv[0]] + built_args
    cli_main()
