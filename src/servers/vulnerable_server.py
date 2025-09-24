#!/usr/bin/env python3
# vulnerable_server.py
# Deliberately "vulnerable" HTTP server for local Slowloris testing.
# Use only in a local test/lab environment!

import socket
import threading
import argparse
import time
import sys


def handle_client(conn: socket.socket, addr, worker_sem: threading.Semaphore, read_chunk: int):
    """
    Read headers until \r\n\r\n is received. If the client sends bytes very slowly,
    this thread will remain occupied — simulating a server vulnerable to Slowloris.
    """
    print(f"[+] Worker start for {addr}")
    try:
        conn.settimeout(None)
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = conn.recv(read_chunk)
            if not chunk:
                print(f"[-] Connection closed by client {addr}")
                return
            buf += chunk
            if len(buf) > 4096:
                # prevent infinite consumption if headers never finish
                print(f"[!] Excessive headers from {addr}, aborting")
                return

        time.sleep(0.2)

        response_body = b"Hello from vulnerable server!\n"
        response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Length: " + str(len(response_body)).encode() + b"\r\n"
                                                                         b"Connection: close\r\n"
                                                                         b"\r\n" + response_body
        )
        conn.sendall(response)
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


def server_loop(host: str, port: int, max_workers: int, backlog: int, read_chunk: int):
    worker_sem = threading.Semaphore(max_workers)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(backlog)
        print(f"[+] Vulnerable server listening on {host}:{port}")
        print(f"[+] max_workers={max_workers}, backlog={backlog}, recv_chunk={read_chunk}")

        try:
            while True:
                conn, addr = s.accept()
                acquired = worker_sem.acquire(blocking=False)
                if not acquired:
                    print(f"[!] No worker available, connection queued: {addr}")
                    # block until a worker slot frees up (keeps the queue occupied)
                    worker_sem.acquire()
                t = threading.Thread(
                    target=handle_client,
                    args=(conn, addr, worker_sem, read_chunk),
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
    parser = argparse.ArgumentParser(description="Vulnerable Slowloris Test Server (local only).")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--max-workers", type=int, default=5,
                        help="Maximum concurrent worker threads (default: 5)")
    parser.add_argument("--backlog", type=int, default=50, help="TCP backlog (listen) (default: 50)")
    parser.add_argument("--read-chunk", type=int, default=1,
                        help="Bytes per recv() to simulate slow header parsing (default: 1)")
    args = parser.parse_args()

    server_loop(args.host, args.port, args.max_workers, args.backlog, args.read_chunk)


if __name__ == "__main__":
    main()
