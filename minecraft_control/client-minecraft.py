import pyautogui
import requests
import socket
import ipaddress
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_local_network() -> str:
    """Détecte automatiquement le réseau local."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    parts = local_ip.rsplit(".", 1)
    return f"{parts[0]}.0/24"


def check_port(ip: str, port: int, timeout: float) -> bool:
    """Vérifie si le port TCP est ouvert sur l'adresse IP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((ip, port)) == 0


def check_http(ip: str, port: int, timeout: float) -> bool:
    """Envoie une requête HTTP et vérifie si la réponse contient le numéro de port."""
    token = str(port)
    for scheme in ("http", "https"):
        url = f"{scheme}://{ip}:{port}/"
        try:
            resp = requests.get(url, timeout=timeout, verify=False)
            if token in resp.text:
                return True
        except requests.RequestException:
            continue
    return False


def scan_host(ip: str, port: int, sock_timeout: float, http_timeout: float):
    """Scanne un hôte. Retourne l'IP sous forme de string si trouvé, sinon None."""
    if not check_port(ip, port, sock_timeout):
        return None
    if check_http(ip, port, http_timeout):
        return ip
    return None


def find_host(port: int, network: str = None, threads: int = 100,
              sock_timeout: float = 0.5, http_timeout: float = 3.0):
    """
    Scanne le réseau local à la recherche du premier hôte dont le port est ouvert
    et dont la réponse HTTP contient le numéro de port.

    Args:
        port:         Nombre à 4 chiffres (1000-9999) — port à scanner et token attendu en réponse.
        network:      Réseau CIDR à scanner (ex: "192.168.1.0/24"). Auto-détecté si None.
        threads:      Nombre de threads parallèles (défaut: 100).
        sock_timeout: Timeout TCP en secondes (défaut: 0.5).
        http_timeout: Timeout HTTP en secondes (défaut: 3.0).

    Returns:
        La première adresse IP trouvée sous forme de string, ou None si aucune.
    """
    if not (1000 <= port <= 9999):
        raise ValueError(f"Le port doit être un nombre à 4 chiffres (1000-9999), reçu : {port}")

    network = network or get_local_network()
    hosts = [ipaddress.ip_address("127.0.0.1")] + list(ipaddress.ip_network(network, strict=False).hosts())

    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Réseau ciblé    : {network}")
    print(f"  Port ciblé      : {port}")
    print(f"  Token attendu   : '{port}'")
    print(f"  Hôtes à scanner : {len(hosts)}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    scanned = 0

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {
            executor.submit(scan_host, str(ip), port, sock_timeout, http_timeout): str(ip)
            for ip in hosts
        }

        for future in as_completed(futures):
            scanned += 1
            print(f"\r  Progression : {scanned}/{len(hosts)}", end="", flush=True)

            result = future.result()
            if result:
                print(f"\n\n  ✅ Hôte trouvé → {result}:{port}\n")
                executor.shutdown(wait=False, cancel_futures=True)
                return result

    print(f"\n\n  ❌ Aucun hôte trouvé avec la réponse '{port}'.\n")
    return None

team = int(input("Enter your team number: "))

url = find_host( team, None, 100, 0.5, 3.0 )

COLOR_CHECK = (959, 875)

actions = {
    "nothing": (254, 254, 254),
    "ccw": (84, 254, 84),
    "cw": (84, 254, 254),
    "front": (254, 254, 84),
    "back": (254, 84, 254),
    "left": (68, 57, 58),
    "right": (254, 84, 84),
}

# You can setup this by loading the minecraft bedrock world and going to positions 536 74 154 in the minecraft world
# You may have to resetup the colors of each actions, as well as the position of the pixel to check

while True:
    try:
        color = pyautogui.pixel(*COLOR_CHECK)
        for action, c in actions.items():
            if color == c:
                print(action)
                requests.get(f"{url}/action/{action}", timeout=0.5)
                break
    except Exception as e:
        print(e)