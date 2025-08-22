from __future__ import annotations
import argparse
import sys
from .utils.logging import setup_logging
from .utils.validators import parse_ports, validate_cidr
from .modes import sniper as sniper_mode
from .modes import domain as domain_mode
from .modes import pitchfork as pitchfork_mode


def interactive_menu() -> None:
    print("Select mode:")
    print("  1) sniper   (IP)")
    print("  2) domain   (domain)")
    print("  3) pitchfork(subnet/ports)")
    choice = input("> ").strip()
    if choice == "1":
        sys.argv.append("sniper")
    elif choice == "2":
        sys.argv.append("domain")
    elif choice == "3":
        sys.argv.append("pitchfork")
    else:
        print("Invalid option.")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slowloris – unified tool (sniper, domain, pitchfork)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logs")

    sub = parser.add_subparsers(dest="mode", required=True, help="Operating mode")

    # sniper
    p_sniper = sub.add_parser("sniper", help="Target a single IP")
    p_sniper.add_argument("ip", help="Target IP address")
    p_sniper.add_argument("-p", "--port", default=80, type=int, help="Port (default: 80)")
    p_sniper.add_argument("-s", "--sockets", default=150, type=int, help="Number of sockets (default: 150)")
    p_sniper.add_argument("--https", action="store_true", help="Use HTTPS")
    p_sniper.add_argument("-ua", "--randuseragents", action="store_true", help="Randomize User-Agents")
    p_sniper.add_argument("--sleeptime", default=15, type=int, help="Interval between headers (seconds)")
    p_sniper.add_argument("--socks5", help="SOCKS5 proxy (e.g., 127.0.0.1:9050)")

    # domain
    p_domain = sub.add_parser("domain", help="Target a domain")
    p_domain.add_argument("host", help="Domain (no protocol)")
    p_domain.add_argument("-p", "--port", default=80, type=int, help="Port (default: 80)")
    p_domain.add_argument("-s", "--sockets", default=150, type=int, help="Number of sockets (default: 150)")
    p_domain.add_argument("--https", action="store_true", help="Use HTTPS")
    p_domain.add_argument("-ua", "--randuseragents", action="store_true", help="Randomize User-Agents")
    p_domain.add_argument("--sleeptime", default=15, type=int, help="Interval between headers (seconds)")
    p_domain.add_argument("--socks5", help="SOCKS5 proxy (e.g., 127.0.0.1:9050)")

    # pitchfork
    p_pitch = sub.add_parser("pitchfork", help="Subnet/ports scan")
    p_pitch.add_argument("subnet", help='Subnet in CIDR (e.g., "192.168.0.0/24")')
    p_pitch.add_argument("-P", "--ports", required=True, help="Comma-separated ports, e.g., 80,8080,443")
    p_pitch.add_argument("-s", "--sockets", default=200, type=int, help="Sockets per IP/port (suggested: 200)")
    p_pitch.add_argument("--https", action="store_true", help="Use HTTPS")
    p_pitch.add_argument("-ua", "--randuseragents", action="store_true", help="Randomize User-Agents")
    p_pitch.add_argument("-t", "--threads", default=50, type=int, help="Max threads")
    p_pitch.add_argument("-d", "--duration", default=120, type=int, help="Test duration (seconds)")

    return parser


def main() -> None:
    # No args → show menu
    if len(sys.argv) == 1:
        interactive_menu()

    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.mode == "sniper":
        strategy = sniper_mode.build(
            ip=args.ip,
            port=args.port,
            sockets=args.sockets,
            https=args.https,
            randua=args.randuseragents,
            sleeptime=args.sleeptime,
            socks5=args.socks5,
        )
        strategy.execute()

    elif args.mode == "domain":
        strategy = domain_mode.build(
            host=args.host,
            port=args.port,
            sockets=args.sockets,
            https=args.https,
            randua=args.randuseragents,
            sleeptime=args.sleeptime,
            socks5=args.socks5,
        )
        strategy.execute()

    elif args.mode == "pitchfork":
        cidr = validate_cidr(args.subnet)
        ports = parse_ports(args.ports)
        if not ports:
            raise SystemExit("Provide valid ports in -P/--ports (e.g., 80,8080,443)")
        strategy = pitchfork_mode.build(
            subnet=cidr,
            ports=ports,
            sockets=args.sockets,
            https=args.https,
            randua=args.randuseragents,
            duration=args.duration,
            threads=args.threads,
        )
        strategy.execute()


if __name__ == "__main__":
    main()
