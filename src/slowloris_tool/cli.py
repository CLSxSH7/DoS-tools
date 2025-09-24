# src/slowloris_tool/cli.py
# -*- coding: utf-8 -*-
"""
CLI entrypoint for slowloris-tool.
Provides subcommands:
  - sniper
  - domain
  - pitchfork
  - tcpflood
  - synflood

This file is defensive: it will try to import mode implementations from
src/slowloris_tool/modes/... if they exist. If not, it prints helpful errors.
"""

from __future__ import annotations

import argparse
import sys
import os
from typing import Optional

# Attacks module (must exist as src/slowloris_tool/attacks.py)
try:
    from .attacks import tcp_flood_ramp, syn_flood_ramp
except Exception:
    tcp_flood_ramp = None
    syn_flood_ramp = None


def _try_import_mode(module_name: str, fn_name: str = "main"):
    """
    Safe attempt to import a mode implementation from src.slowloris_tool.modes.<module_name>.
    Returns the function if available, otherwise None.
    """
    try:
        mod = __import__(f"{__package__}.modes.{module_name}", fromlist=[fn_name])
        fn = getattr(mod, fn_name)
        return fn
    except Exception:
        return None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="slowloris-tool", description="Slowloris unified testing tool")
    sub = p.add_subparsers(dest="command", required=True, help="mode to run")

    # -------------------------
    # sniper (single IP)
    # -------------------------
    p_sniper = sub.add_parser("sniper", help="Target a single IP")
    p_sniper.add_argument("ip", help="Target IP or host")
    p_sniper.add_argument("-p", "--port", type=int, default=80, help="Target port")
    p_sniper.add_argument("-s", "--sockets", type=int, default=150, help="Number of sockets to open")
    p_sniper.add_argument("--https", action="store_true", help="Use HTTPS / TLS")
    p_sniper.add_argument("-ua", "--randomize-ua", action="store_true", help="Randomize User-Agent header")
    p_sniper.add_argument("--sleeptime", type=int, default=15, help="Header interval in seconds")
    p_sniper.add_argument("--socks5", type=str, default=None, help="Optional SOCKS5 proxy (host:port)")

    # -------------------------
    # domain (domain name)
    # -------------------------
    p_domain = sub.add_parser("domain", help="Target a domain (resolves and uses domain name)")
    p_domain.add_argument("domain", help="Domain (no protocol)")
    p_domain.add_argument("-p", "--port", type=int, default=80)
    p_domain.add_argument("-s", "--sockets", type=int, default=150)
    p_domain.add_argument("--https", action="store_true")
    p_domain.add_argument("-ua", "--randomize-ua", action="store_true")
    p_domain.add_argument("--sleeptime", type=int, default=15)
    p_domain.add_argument("--socks5", type=str, default=None)

    # -------------------------
    # pitchfork (subnet/ports)
    # -------------------------
    p_pf = sub.add_parser("pitchfork", help="Scan a subnet with multiple ports")
    p_pf.add_argument("subnet", help="Subnet in CIDR (e.g. 192.168.0.0/24)")
    p_pf.add_argument("-P", "--ports", type=str, default="80", help="Comma-separated ports (e.g. 80,443)")
    p_pf.add_argument("-s", "--sockets", type=int, default=200, help="Sockets per target/port")
    p_pf.add_argument("--https", action="store_true")
    p_pf.add_argument("-ua", "--randomize-ua", action="store_true")
    p_pf.add_argument("--sleeptime", type=int, default=15)

    # -------------------------
    # tcpflood
    # -------------------------
    p_tcp = sub.add_parser("tcpflood", help="TCP flood with ramp-up and monitoring (test-lab only)")
    p_tcp.add_argument("host", help="Target host (IP or hostname)")
    p_tcp.add_argument("-p", "--port", type=int, default=80)
    p_tcp.add_argument("--start", type=int, default=10, help="Initial number of sockets")
    p_tcp.add_argument("--step", type=int, default=10, help="Sockets to add each step")
    p_tcp.add_argument("--max", type=int, default=200, help="Max sockets")
    p_tcp.add_argument("--step-duration", type=int, default=10, help="Seconds per ramp step")
    p_tcp.add_argument("--payload-size", type=int, default=256, help="Bytes sent per socket send")
    p_tcp.add_argument("--send-interval", type=float, default=1.0, help="Interval between sends per socket (s)")
    p_tcp.add_argument("--monitor-interval", type=float, default=2.0, help="Monitor check interval (s)")
    p_tcp.add_argument("--monitor-timeout", type=float, default=2.0, help="Monitor connect timeout (s)")
    p_tcp.add_argument("--impact-latency", type=float, default=1.0, help="Latency threshold (s) to stop ramp-up")
    p_tcp.add_argument("--duration", type=float, default=None,
                       help="Steady-state duration in seconds (omit to run until Ctrl+C)")

    # -------------------------
    # synflood
    # -------------------------
    p_syn = sub.add_parser("synflood",
                           help="SYN flood with ramp-up and monitoring (requires scapy/root, test-lab only)")
    p_syn.add_argument("host", help="Target host (IP or hostname)")
    p_syn.add_argument("-p", "--port", type=int, default=80)
    p_syn.add_argument("--start", type=int, default=50, help="Initial packets-per-second")
    p_syn.add_argument("--step", type=int, default=50, help="pps increase each step")
    p_syn.add_argument("--max", type=int, default=1000, help="Max pps")
    p_syn.add_argument("--step-duration", type=int, default=10, help="Seconds per ramp step")
    p_syn.add_argument("--monitor-interval", type=float, default=2.0)
    p_syn.add_argument("--monitor-timeout", type=float, default=2.0)
    p_syn.add_argument("--impact-latency", type=float, default=1.0)
    p_syn.add_argument("--duration", type=float, default=None,
                       help="Steady-state duration in seconds (omit to run until Ctrl+C)")

    return p


def dispatch_sniper(args: argparse.Namespace) -> int:
    fn = _try_import_mode("sniper", fn_name="run")
    if fn:
        return fn(args.ip, args.port, args.sockets, args.https, args.randomize_ua, args.sleeptime, args.socks5) or 0

    try:
        mod = __import__(f"{__package__}.modes.sniper", fromlist=["main"])
        if hasattr(mod, "main"):
            return mod.main(args.ip, args.port, args.sockets, args.https, args.randomize_ua, args.sleeptime,
                            args.socks5) or 0
    except Exception:
        pass

    print("[!] sniper mode not implemented in this installation.")
    print("    - Ensure you have src/slowloris_tool/modes/sniper.py providing run(...)")
    return 2


def dispatch_domain(args: argparse.Namespace) -> int:
    fn = _try_import_mode("domain", fn_name="run")
    if fn:
        return fn(args.domain, args.port, args.sockets, args.https, args.randomize_ua, args.sleeptime, args.socks5) or 0
    try:
        mod = __import__(f"{__package__}.modes.domain", fromlist=["main"])
        if hasattr(mod, "main"):
            return mod.main(args.domain, args.port, args.sockets, args.https, args.randomize_ua, args.sleeptime,
                            args.socks5) or 0
    except Exception:
        pass
    print("[!] domain mode not implemented in this installation.")
    return 2


def dispatch_pitchfork(args: argparse.Namespace) -> int:
    fn = _try_import_mode("pitchfork", fn_name="run")
    if fn:
        return fn(args.subnet, args.ports, args.sockets, args.https, args.randomize_ua, args.sleeptime) or 0
    try:
        mod = __import__(f"{__package__}.modes.pitchfork", fromlist=["main"])
        if hasattr(mod, "main"):
            return mod.main(args.subnet, args.ports, args.sockets, args.https, args.randomize_ua, args.sleeptime) or 0
    except Exception:
        pass
    print("[!] pitchfork mode not implemented in this installation.")
    return 2


def dispatch_tcpflood(args: argparse.Namespace) -> int:
    if tcp_flood_ramp is None:
        print("[!] tcpflood not available: missing src/slowloris_tool/attacks.py or import error.")
        return 3

    tcp_flood_ramp(
        host=args.host,
        port=args.port,
        start_sockets=args.start,
        step=args.step,
        max_sockets=args.max,
        step_duration=args.step_duration,
        payload_size=args.payload_size,
        send_interval=args.send_interval,
        monitor_check_interval=args.monitor_interval,
        monitor_timeout=args.monitor_timeout,
        impact_latency_threshold=args.impact_latency,
        duration=args.duration,
    )
    return 0


def dispatch_synflood(args: argparse.Namespace) -> int:
    if syn_flood_ramp is None:
        print("[!] synflood not available: missing src/slowloris_tool/attacks.py or import error.")
        print("    - For SYN flood install scapy in your environment (`pip install scapy`) and run as admin/root.")
        return 3

    syn_flood_ramp(
        host=args.host,
        port=args.port,
        start_pps=args.start,
        step_pps=args.step,
        max_pps=args.max,
        step_duration=args.step_duration,
        monitor_check_interval=args.monitor_interval,
        monitor_timeout=args.monitor_timeout,
        impact_latency_threshold=args.impact_latency,
        duration=args.duration,
    )
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "sniper":
        return dispatch_sniper(args)
    elif args.command == "domain":
        return dispatch_domain(args)
    elif args.command == "pitchfork":
        if hasattr(args, "ports") and isinstance(args.ports, str):
            args.ports = [p.strip() for p in args.ports.split(",") if p.strip()]
        return dispatch_pitchfork(args)
    elif args.command == "tcpflood":
        return dispatch_tcpflood(args)
    elif args.command == "synflood":
        return dispatch_synflood(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    raise SystemExit(main())
