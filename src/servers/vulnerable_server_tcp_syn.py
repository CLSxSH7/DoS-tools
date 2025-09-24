#!/usr/bin/env python3
# vulnerable_server_tcp_syn.py
# Version of the server that holds open/active connections to demonstrate TCP flood.
# For lab/local use only.

import socket
import threading
import argparse
import time


def handle_client_hold(conn: socket.socket, addr, worker_sem: threading.Semaphore, read_chunk: int,
                       hold_seconds: int = 3600):
    """
    Read headers until \r\n\r\n is received, then *do not* respond immediately.
    Instead keep the connection open and periodically send small keep-alive payloads
    to hold the thread/socket busy — useful to demonstrate TCP flood effects.
    """
    print(f"[+] Worker start for {addr} (hold)")
    try:
        conn.settimeout(None)
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = conn.recv(read_chunk)
            if not chunk:
                print(f"[-] Connection closed by client {addr}")
                return
            buf += chunk
            if len(buf) > 8192:
                print(f"[!] Excessive headers, aborting for {addr}")
                return

        # DO NOT send the normal HTTP response here — hold the connection and
        # send periodic small payloads to keep the socket and worker occupied.
        try:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass

        payload = b"x" * 512
        start = time.time()
        while time.time() - start < float(hold_seconds):
            try:
                conn.sendall(payload)
            except Exception:
                break
            time.sleep(0.2)

    except Exception as e:
        print(f"[!] Exception handling {addr}: {e}")
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        conn.close()
        worker_sem.release()
        print(f"[+] Worker finished for {addr}")


def server_loop(host: str, port: int, max_workers: int, backlog: int, read_chunk: int, hold_seconds: int):
    worker_sem = threading.Semaphore(max_workers)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(backlog)
        print(f"[+] Vulnerable TCP/SYN server listening on {host}:{port}")
        print(f"[+] max_workers={max_workers}, backlog={backlog}, recv_chunk={read_chunk}, hold_seconds={hold_seconds}")

        try:
            while True:
                conn, addr = s.accept()
                acquired = worker_sem.acquire(blocking=False)
                if not acquired:
                    print(f"[!] No worker available, connection queued: {addr}")
                    worker_sem.acquire()
                t = threading.Thread(
                    target=handle_client_hold,
                    args=(conn, addr, worker_sem, read_chunk, hold_seconds),
                    daemon=True
                )
                t.start()

        except KeyboardInterrupt:
            print("\n[+] Server shutting down (keyboard interrupt).")
        except Exception as e:
            print(f"[!] Server exception: {e}")
        finally:
            print("[+] Server stopped.")


def main():
    parser = argparse.ArgumentParser(description="Vulnerable TCP/SYN Test Server (local only).")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--max-workers", type=int, default=5, help="Maximum concurrent worker threads (default: 5)")
    parser.add_argument("--backlog", type=int, default=50, help="TCP backlog (listen) (default: 50)")
    parser.add_argument("--read-chunk", type=int, default=1,
                        help="Bytes per recv() to simulate slow header parsing (default: 1)")
    parser.add_argument(
        "--hold-seconds",
        type=int,
        default=3600,
        help="How many seconds to keep the connection open after reading headers (default = 3600)"
    )
    args = parser.parse_args()
    server_loop(args.host, args.port, args.max_workers, args.backlog, args.read_chunk, args.hold_seconds)


if __name__ == "__main__":
    main()
