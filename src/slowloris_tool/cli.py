from __future__ import annotations
import argparse
import sys
from .utils.logging import setup_logging
from .utils.validators import parse_ports, validate_cidr
from .modes import sniper as sniper_mode
from .modes import domain as domain_mode
from .modes import pitchfork as pitchfork_mode


def interactive_menu() -> None:
    print("Selecione o modo:")
    print("  1) sniper   (IP)")
    print("  2) domain   (domínio)")
    print("  3) pitchfork(sub-rede/portas)")
    choice = input("> ").strip()
    if choice == "1":
        sys.argv.append("sniper")
    elif choice == "2":
        sys.argv.append("domain")
    elif choice == "3":
        sys.argv.append("pitchfork")
    else:
        print("Opção inválida.")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slowloris – ferramenta unificada (sniper, domain, pitchfork)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Ativa logs detalhados")

    sub = parser.add_subparsers(dest="mode", required=True, help="Modo de operação")

    # sniper
    p_sniper = sub.add_parser("sniper", help="Ataque direcionado por IP")
    p_sniper.add_argument("ip", help="Endereço IP de destino")
    p_sniper.add_argument("-p", "--port", default=80, type=int, help="Porta (padrão: 80)")
    p_sniper.add_argument("-s", "--sockets", default=200, type=int, help="Nº de sockets (padrão: 200)")
    p_sniper.add_argument("--https", action="store_true", help="Usar HTTPS")
    p_sniper.add_argument("-ua", "--randuseragents", action="store_true", help="Randomizar User-Agents")
    p_sniper.add_argument("--sleeptime", default=15, type=int, help="Intervalo entre headers (s)")
    p_sniper.add_argument("--socks5", help="Proxy SOCKS5 (ex.: 127.0.0.1:9050)")

    # domain
    p_domain = sub.add_parser("domain", help="Ataque direcionado por domínio")
    p_domain.add_argument("host", help="Domínio de destino (sem protocolo)")
    p_domain.add_argument("-p", "--port", default=80, type=int, help="Porta (padrão: 80)")
    p_domain.add_argument("-s", "--sockets", default=200, type=int, help="Nº de sockets (padrão: 200)")
    p_domain.add_argument("--https", action="store_true", help="Usar HTTPS")
    p_domain.add_argument("-ua", "--randuseragents", action="store_true", help="Randomizar User-Agents")
    p_domain.add_argument("--sleeptime", default=15, type=int, help="Intervalo entre headers (s)")
    p_domain.add_argument("--socks5", help="Proxy SOCKS5 (ex.: 127.0.0.1:9050)")

    # pitchfork (sem proxy por padrão)
    p_pitch = sub.add_parser("pitchfork", help="Varredura de sub-rede/portas")
    p_pitch.add_argument("subnet", help='Sub-rede no formato CIDR (ex.: "192.168.0.0/24")')
    p_pitch.add_argument("-P", "--ports", required=True, help="Lista de portas, ex.: 80,8080,443")
    p_pitch.add_argument("-s", "--sockets", default=200, type=int, help="Nº de sockets por IP/porta (sug. 200)")
    p_pitch.add_argument("--https", action="store_true", help="Usar HTTPS")
    p_pitch.add_argument("-ua", "--randuseragents", action="store_true", help="Randomizar User-Agents")
    p_pitch.add_argument("-t", "--threads", default=50, type=int, help="Máximo de threads")
    p_pitch.add_argument("-d", "--duration", default=120, type=int, help="Duração do teste (s)")

    return parser


def main() -> None:
    # Sem args → menu
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
            socks5=args.socks5,  # <- repassa
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
            socks5=args.socks5,  # <- repassa
        )
        strategy.execute()

    elif args.mode == "pitchfork":
        cidr = validate_cidr(args.subnet)
        ports = parse_ports(args.ports)
        if not ports:
            raise SystemExit("Informe portas válidas em -P/--ports (ex.: 80,8080,443)")
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
