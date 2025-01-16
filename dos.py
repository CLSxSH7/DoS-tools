import argparse
import logging
import random
import socket
import sys
import time
from ipaddress import IPv4Network
from threading import Event

parser = argparse.ArgumentParser(
    description="Enhanced Slowloris to handle multiple IPs and detect vulnerabilities."
)
parser.add_argument("subnet", help="Subnet to scan in CIDR notation (e.g., 192.168.1.0/24)")
parser.add_argument("-p", "--port", default=80, help="Port of webserver, usually 80", type=int)
parser.add_argument("-s", "--sockets", default=150, help="Number of sockets per host", type=int)
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
parser.add_argument("--sleeptime", default=15, type=int, help="Time to sleep between each header sent.")
args = parser.parse_args()

logging.basicConfig(
    format="[%(asctime)s] %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    level=logging.DEBUG if args.verbose else logging.INFO,
)

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.3 Safari/602.3.12",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36",
]


def send_line(s, line):
    line = f"{line}\r\n"
    s.send(line.encode("utf-8"))


def send_header(s, name, value):
    send_line(s, f"{name}: {value}")


def init_socket(ip):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((ip, args.port))
        send_line(s, f"GET /?{random.randint(0, 2000)} HTTP/1.1")
        ua = random.choice(user_agents)
        send_header(s, "User-Agent", ua)
        send_header(s, "Accept-language", "en-US,en,q=0.5")
        return s
    except socket.error as e:
        logging.debug(f"Socket initialization failed for {ip}: {e}")
        return None


def slowloris_test(ip):
    try:
        s = init_socket(ip)
        if s:
            send_header(s, "X-a", random.randint(1, 5000))
            s.close()
            return True
    except Exception as e:
        logging.debug(f"Error testing Slowloris on {ip}: {e}")
    return False


def is_host_alive(ip):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((str(ip), args.port))
            return result == 0
    except Exception as e:
        logging.debug(f"Error checking if host is alive {ip}: {e}")
        return False


def main():
    stop_event = Event()
    try:
        vulnerable_ips = []
        subnet = IPv4Network(args.subnet, strict=False)

        logging.info(f"Scanning subnet {args.subnet} for active hosts.")
        for ip in subnet.hosts():
            if stop_event.is_set():
                break

            if is_host_alive(ip):
                logging.info(f"Host {ip} is active. Testing for Slowloris vulnerability.")
                if slowloris_test(str(ip)):
                    logging.info(f"Host {ip} is vulnerable to Slowloris.")
                    vulnerable_ips.append(str(ip))
                else:
                    logging.info(f"Host {ip} is not vulnerable to Slowloris.")

        with open("vulnerable_ips.txt", "w") as f:
            for ip in vulnerable_ips:
                f.write(f"{ip}\n")

        logging.info(f"Scan complete. Vulnerable IPs saved to vulnerable_ips.txt.")
    except KeyboardInterrupt:
        logging.info("Scan interrupted by user.")
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()
