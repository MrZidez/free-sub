#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import json
import base64
import socket
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

import requests
try:
    from ping3 import ping
except ImportError:
    ping = None

# ==================== КОНФИГУРАЦИЯ ====================
SOURCE_URL = "https://raw.githubusercontent.com/MrZidez/free-sub/refs/heads/main/source"
USER_AGENT = "happ"
PING_THRESHOLD_MS = 90
MAX_KEYS_PER_GROUP = 20
MAX_GROUPS_PER_COUNTRY = 5          # <-- новое ограничение
OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.json"

# Словарь стран (включая все популярные)
COUNTRY_MAP = {
    "russia": ("🇷🇺", "Россия"), "россия": ("🇷🇺", "Россия"), "ru": ("🇷🇺", "Россия"),
    "usa": ("🇺🇸", "США"), "us": ("🇺🇸", "США"), "сша": ("🇺🇸", "США"),
    "america": ("🇺🇸", "США"), "америка": ("🇺🇸", "США"),
    "germany": ("🇩🇪", "Германия"), "de": ("🇩🇪", "Германия"),
    "германия": ("🇩🇪", "Германия"), "deutschland": ("🇩🇪", "Германия"), "deu": ("🇩🇪", "Германия"),
    "netherlands": ("🇳🇱", "Нидерланды"), "nl": ("🇳🇱", "Нидерланды"),
    "нидерланды": ("🇳🇱", "Нидерланды"), "holland": ("🇳🇱", "Нидерланды"),
    "голландия": ("🇳🇱", "Нидерланды"), "nld": ("🇳🇱", "Нидерланды"),
    "france": ("🇫🇷", "Франция"), "fr": ("🇫🇷", "Франция"),
    "франция": ("🇫🇷", "Франция"), "fra": ("🇫🇷", "Франция"),
    "uk": ("🇬🇧", "Великобритания"), "great britain": ("🇬🇧", "Великобритания"),
    "united kingdom": ("🇬🇧", "Великобритания"), "великобритания": ("🇬🇧", "Великобритания"),
    "gbr": ("🇬🇧", "Великобритания"),
    "canada": ("🇨🇦", "Канада"), "ca": ("🇨🇦", "Канада"),
    "канада": ("🇨🇦", "Канада"), "can": ("🇨🇦", "Канада"),
    "australia": ("🇦🇺", "Австралия"), "au": ("🇦🇺", "Австралия"),
    "австралия": ("🇦🇺", "Австралия"), "avstralia": ("🇦🇺", "Австралия"),
    "aus": ("🇦🇺", "Австралия"),
    "japan": ("🇯🇵", "Япония"), "jp": ("🇯🇵", "Япония"),
    "япония": ("🇯🇵", "Япония"), "jpn": ("🇯🇵", "Япония"),
    "singapore": ("🇸🇬", "Сингапур"), "sg": ("🇸🇬", "Сингапур"),
    "сингапур": ("🇸🇬", "Сингапур"), "sgp": ("🇸🇬", "Сингапур"),
    "hong kong": ("🇭🇰", "Гонконг"), "hk": ("🇭🇰", "Гонконг"),
    "гонконг": ("🇭🇰", "Гонконг"), "hkg": ("🇭🇰", "Гонконг"),
    "taiwan": ("🇹🇼", "Тайвань"), "tw": ("🇹🇼", "Тайвань"),
    "тайвань": ("🇹🇼", "Тайвань"), "twn": ("🇹🇼", "Тайвань"),
    "india": ("🇮🇳", "Индия"), "in": ("🇮🇳", "Индия"),
    "индия": ("🇮🇳", "Индия"), "ind": ("🇮🇳", "Индия"),
    "brazil": ("🇧🇷", "Бразилия"), "br": ("🇧🇷", "Бразилия"),
    "бразилия": ("🇧🇷", "Бразилия"), "bra": ("🇧🇷", "Бразилия"),
    "south korea": ("🇰🇷", "Южная Корея"), "kr": ("🇰🇷", "Южная Корея"),
    "южная корея": ("🇰🇷", "Южная Корея"), "kor": ("🇰🇷", "Южная Корея"),
    "italy": ("🇮🇹", "Италия"), "it": ("🇮🇹", "Италия"),
    "италия": ("🇮🇹", "Италия"), "ita": ("🇮🇹", "Италия"),
    "spain": ("🇪🇸", "Испания"), "es": ("🇪🇸", "Испания"),
    "испания": ("🇪🇸", "Испания"), "esp": ("🇪🇸", "Испания"),
    "sweden": ("🇸🇪", "Швеция"), "se": ("🇸🇪", "Швеция"),
    "швеция": ("🇸🇪", "Швеция"), "swe": ("🇸🇪", "Швеция"),
    "norway": ("🇳🇴", "Норвегия"), "no": ("🇳🇴", "Норвегия"),
    "норвегия": ("🇳🇴", "Норвегия"), "norwegia": ("🇳🇴", "Норвегия"),
    "nor": ("🇳🇴", "Норвегия"),
    "denmark": ("🇩🇰", "Дания"), "dk": ("🇩🇰", "Дания"),
    "дания": ("🇩🇰", "Дания"), "dnk": ("🇩🇰", "Дания"),
    "finland": ("🇫🇮", "Финляндия"), "fi": ("🇫🇮", "Финляндия"),
    "финляндия": ("🇫🇮", "Финляндия"), "fin": ("🇫🇮", "Финляндия"),
    "poland": ("🇵🇱", "Польша"), "pl": ("🇵🇱", "Польша"),
    "польша": ("🇵🇱", "Польша"), "pol": ("🇵🇱", "Польша"),
    "ukraine": ("🇺🇦", "Украина"), "ua": ("🇺🇦", "Украина"),
    "украина": ("🇺🇦", "Украина"), "ukr": ("🇺🇦", "Украина"),
    "kazakhstan": ("🇰🇿", "Казахстан"), "kz": ("🇰🇿", "Казахстан"),
    "казахстан": ("🇰🇿", "Казахстан"), "kaz": ("🇰🇿", "Казахстан"),
    "belarus": ("🇧🇾", "Беларусь"), "by": ("🇧🇾", "Беларусь"),
    "беларусь": ("🇧🇾", "Беларусь"), "blr": ("🇧🇾", "Беларусь"),
    "turkey": ("🇹🇷", "Турция"), "tr": ("🇹🇷", "Турция"),
    "турция": ("🇹🇷", "Турция"), "tur": ("🇹🇷", "Турция"),
    "egypt": ("🇪🇬", "Египет"), "eg": ("🇪🇬", "Египет"),
    "египет": ("🇪🇬", "Египет"), "egy": ("🇪🇬", "Египет"),
    "uae": ("🇦🇪", "ОАЭ"), "ae": ("🇦🇪", "ОАЭ"),
    "оаэ": ("🇦🇪", "ОАЭ"), "are": ("🇦🇪", "ОАЭ"),
    "saudi arabia": ("🇸🇦", "Саудовская Аравия"), "saudi": ("🇸🇦", "Саудовская Аравия"),
    "sa": ("🇸🇦", "Саудовская Аравия"), "саудовская аравия": ("🇸🇦", "Саудовская Аравия"),
    "sau": ("🇸🇦", "Саудовская Аравия"),
    "israel": ("🇮🇱", "Израиль"), "il": ("🇮🇱", "Израиль"),
    "израиль": ("🇮🇱", "Израиль"), "isr": ("🇮🇱", "Израиль"),
}
COUNTRY_KEYS = list(COUNTRY_MAP.keys())

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def is_flag_emoji(s: str) -> bool:
    return len(s) == 2 and 0x1F1E6 <= ord(s[0]) <= 0x1F1FF and 0x1F1E6 <= ord(s[1]) <= 0x1F1FF

def is_url_encoded_flag(text: str) -> bool:
    return "%F0%9F%87" in text

def decode_url_encoded_flags(text: str) -> str:
    try:
        return urllib.parse.unquote(text)
    except:
        return text

def is_header_line(line: str) -> bool:
    line = line.strip()
    if not line:
        return False
    if line.startswith("#"):
        return False
    if re.search(r'(vless|trojan|hysteria2|ss|naive)\://', line, re.I):
        return False
    if line.startswith(("{","[")):
        return False
    if re.match(r'^[\d\s]*ms$', line, re.I) or re.match(r'^n/a$', line, re.I):
        return False
    if re.match(r'^[\d\s;]+$', line):
        return False
    for i in range(len(line)-1):
        if is_flag_emoji(line[i:i+2]):
            return True
    if is_url_encoded_flag(line):
        return True
    lower = line.lower()
    return any(kw in lower for kw in COUNTRY_KEYS)

def normalize_header(header: str) -> str:
    header = decode_url_encoded_flags(header.strip())
    return re.sub(r'\s+', ' ', header)

def is_base64_encoded(text: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9+/=]+$', text.strip()))

def decode_base64_if_needed(text: str) -> str:
    if is_base64_encoded(text.strip()):
        try:
            return base64.b64decode(text.strip(), validate=True).decode('utf-8')
        except:
            pass
    return text

def fetch_subscription_list(url: str) -> List[str]:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        return [l.strip() for l in resp.text.splitlines() if l.strip() and not l.strip().startswith("#")]
    except Exception as e:
        print(f"[ERROR] fetch list: {e}", file=sys.stderr)
        return []

def fetch_subscription_content(url: str) -> str:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        return decode_base64_if_needed(resp.text)
    except Exception as e:
        print(f"[ERROR] fetch {url}: {e}", file=sys.stderr)
        return ""

# ==================== ПАРСЕРЫ ССЫЛОК (с декодированием) ====================
def parse_vless(link: str) -> dict:
    if not link.startswith("vless://"):
        return {}
    link = link[8:]
    remarks = ""
    if '#' in link:
        link, remarks = link.split('#', 1)
        remarks = urllib.parse.unquote(remarks)
    base, query = link.split('?', 1) if '?' in link else (link, "")
    params = urllib.parse.parse_qs(query)
    for k, v in params.items():
        if isinstance(v, list):
            params[k] = v[0]
    if '@' in base:
        user, host = base.split('@', 1)
        if ':' in host:
            address, port = host.split(':', 1)
            port = int(port)
        else:
            address, port = host, 443
    else:
        user, address, port = "", "", 443
    return {"protocol":"vless","id":user,"address":address,"port":port,"params":params,"remarks":remarks}

def parse_trojan(link: str) -> dict:
    if not link.startswith("trojan://"):
        return {}
    link = link[9:]
    remarks = ""
    if '#' in link:
        link, remarks = link.split('#', 1)
        remarks = urllib.parse.unquote(remarks)
    base, query = link.split('?', 1) if '?' in link else (link, "")
    params = urllib.parse.parse_qs(query)
    for k, v in params.items():
        if isinstance(v, list):
            params[k] = v[0]
    if '@' in base:
        password, host = base.split('@', 1)
        if ':' in host:
            address, port = host.split(':', 1)
            port = int(port)
        else:
            address, port = host, 443
    else:
        password, address, port = "", "", 443
    return {"protocol":"trojan","password":password,"address":address,"port":port,"params":params,"remarks":remarks}

def parse_hysteria2(link: str) -> dict:
    if not link.startswith("hysteria2://"):
        return {}
    link = link[12:]
    remarks = ""
    if '#' in link:
        link, remarks = link.split('#', 1)
        remarks = urllib.parse.unquote(remarks)
    base, query = link.split('?', 1) if '?' in link else (link, "")
    params = urllib.parse.parse_qs(query)
    for k, v in params.items():
        if isinstance(v, list):
            params[k] = v[0]
    if '@' in base:
        auth, host = base.split('@', 1)
        if ':' in host:
            address, port = host.split(':', 1)
            port = int(port)
        else:
            address, port = host, 443
    else:
        auth, address, port = "", "", 443
    return {"protocol":"hysteria2","auth":auth,"address":address,"port":port,"params":params,"remarks":remarks}

def parse_ss(link: str) -> dict:
    if not link.startswith("ss://"):
        return {}
    link = link[5:]
    remarks = ""
    if '#' in link:
        link, remarks = link.split('#', 1)
        remarks = urllib.parse.unquote(remarks)
    if '@' in link:
        auth, rest = link.split('@', 1)
        if '?' in rest:
            hostport, query = rest.split('?', 1)
            params = urllib.parse.parse_qs(query)
            for k, v in params.items():
                if isinstance(v, list):
                    params[k] = v[0]
        else:
            hostport, query, params = rest, "", {}
        if ':' in auth:
            method, password = auth.split(':', 1)
        else:
            method, password = "", ""
        if ':' in hostport:
            address, port = hostport.split(':', 1)
            port = int(port)
        else:
            address, port = hostport, 443
    else:
        try:
            decoded = base64.b64decode(link, validate=True).decode('utf-8')
            return parse_ss("ss://" + decoded)
        except:
            method, password, address, port, params = "", "", "", 443, {}
    return {"protocol":"ss","method":method,"password":password,"address":address,"port":port,"params":params,"remarks":remarks}

def parse_naive(link: str) -> dict:
    if not link.startswith("naive+"):
        return {}
    link = link[6:]
    parsed = urllib.parse.urlparse(link)
    if parsed.scheme not in ('https','http'):
        return {}
    auth = parsed.netloc.split('@') if '@' in parsed.netloc else None
    if auth and len(auth)==2:
        userpass, hostport = auth
        user, password = userpass.split(':') if ':' in userpass else ('', '')
    else:
        hostport = parsed.netloc
        user, password = '', ''
    host, port = hostport.split(':') if ':' in hostport else (hostport, '443')
    port = int(port) if port else 443
    params = urllib.parse.parse_qs(parsed.query)
    for k, v in params.items():
        if isinstance(v, list):
            params[k] = v[0]
    remarks = parsed.fragment or ''
    remarks = urllib.parse.unquote(remarks)
    return {"protocol":"naive","user":user,"password":password,"address":host,"port":port,"params":params,"remarks":remarks}

# ==================== ПОСТРОЕНИЕ OUTBOUND ====================
def build_outbound_vless(p: dict) -> dict:
    ob = {"tag":"proxy","protocol":"vless","settings":{"vnext":[{"address":p["address"],"port":p["port"],"users":[{"id":p["id"],"flow":p["params"].get("flow",""),"encryption":"none"}]}]},"streamSettings":{"network":p["params"].get("type","tcp"),"security":p["params"].get("security","none")}}
    sec = ob["streamSettings"]["security"]
    if sec == "tls":
        tls = {}
        if "sni" in p["params"]: tls["serverName"] = p["params"]["sni"]
        if "fp" in p["params"]: tls["fingerprint"] = p["params"]["fp"]
        ob["streamSettings"]["tlsSettings"] = tls
    elif sec == "reality":
        reality = {"serverName":p["params"].get("sni",""),"fingerprint":p["params"].get("fp",""),"publicKey":p["params"].get("pbk",""),"shortId":p["params"].get("sid","")}
        ob["streamSettings"]["realitySettings"] = reality
    net = ob["streamSettings"]["network"]
    if net == "ws":
        ob["streamSettings"]["wsSettings"] = {"path":p["params"].get("path","/"),"headers":{"Host":p["params"].get("host","")}}
    elif net == "grpc":
        ob["streamSettings"]["grpcSettings"] = {"serviceName":p["params"].get("serviceName","")}
    return ob

def build_outbound_trojan(p: dict) -> dict:
    ob = {"tag":"proxy","protocol":"trojan","settings":{"servers":[{"address":p["address"],"port":p["port"],"password":p["password"]}]},"streamSettings":{"network":p["params"].get("type","tcp"),"security":p["params"].get("security","none")}}
    if ob["streamSettings"]["security"] == "tls":
        tls = {}
        if "sni" in p["params"]: tls["serverName"] = p["params"]["sni"]
        if "fp" in p["params"]: tls["fingerprint"] = p["params"]["fp"]
        ob["streamSettings"]["tlsSettings"] = tls
    net = ob["streamSettings"]["network"]
    if net == "ws":
        ob["streamSettings"]["wsSettings"] = {"path":p["params"].get("path","/"),"headers":{"Host":p["params"].get("host","")}}
    elif net == "grpc":
        ob["streamSettings"]["grpcSettings"] = {"serviceName":p["params"].get("serviceName","")}
    return ob

def build_outbound_hysteria2(p: dict) -> dict:
    ob = {"tag":"proxy","protocol":"hysteria","settings":{"address":p["address"],"port":p["port"],"version":2},"streamSettings":{"network":"hysteria","security":p["params"].get("security","tls"),"hysteriaSettings":{"version":2,"auth":p["auth"]}}}
    if ob["streamSettings"]["security"] == "tls":
        tls = {}
        if "sni" in p["params"]: tls["serverName"] = p["params"]["sni"]
        if "fp" in p["params"]: tls["fingerprint"] = p["params"]["fp"]
        if "allowinsecure" in p["params"]:
            tls["allowInsecure"] = p["params"]["allowinsecure"] == "1"
        ob["streamSettings"]["tlsSettings"] = tls
    return ob

def build_outbound_ss(p: dict) -> dict:
    return {"tag":"proxy","protocol":"shadowsocks","settings":{"servers":[{"address":p["address"],"port":p["port"],"method":p["method"],"password":p["password"],"uot":True}]}}

def build_outbound_naive(p: dict) -> dict:
    return {"tag":"proxy","protocol":"http","settings":{"servers":[{"address":p["address"],"port":p["port"],"user":p["user"],"password":p["password"]}]}}

def build_outbound_from_link(link: str) -> Optional[dict]:
    if link.startswith("vless://"):
        p = parse_vless(link)
        if p:
            return build_outbound_vless(p)
    elif link.startswith("trojan://"):
        p = parse_trojan(link)
        if p:
            return build_outbound_trojan(p)
    elif link.startswith("hysteria2://"):
        p = parse_hysteria2(link)
        if p:
            return build_outbound_hysteria2(p)
    elif link.startswith("ss://"):
        p = parse_ss(link)
        if p and p.get("address"):
            return build_outbound_ss(p)
    elif link.startswith("naive+"):
        p = parse_naive(link)
        if p and p.get("address"):
            return build_outbound_naive(p)
    return None

# ==================== ПРОВЕРКА ПИНГА ====================
def get_host_port_from_link(link: str) -> Tuple[str, int]:
    for proto in ["vless://","trojan://","hysteria2://","ss://","naive+"]:
        if link.startswith(proto):
            rest = link[len(proto):]
            if '#' in rest:
                rest = rest.split('#')[0]
            if '?' in rest:
                rest = rest.split('?')[0]
            if '@' in rest:
                _, host = rest.split('@',1)
            else:
                host = rest
            if ':' in host:
                addr, port = host.split(':',1)
                return addr, int(port) if port else 443
            else:
                return host, 443
    return "", 443

def check_ping_icmp(host: str, timeout: float = 2.0) -> Optional[float]:
    if ping is None:
        return None
    try:
        d = ping(host, timeout=timeout)
        if d is not None and d > 0:
            return d * 1000
    except:
        pass
    return None

def check_ping_tcp(host: str, port: int, timeout: float = 2.0) -> Optional[float]:
    try:
        start = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            return (time.time() - start) * 1000
    except:
        return None

def check_ping(link: str) -> Optional[float]:
    host, port = get_host_port_from_link(link)
    if not host:
        return None
    d = check_ping_icmp(host)
    if d is not None and d < PING_THRESHOLD_MS:
        return d
    d = check_ping_tcp(host, port)
    if d is not None and d < PING_THRESHOLD_MS:
        return d
    return None

# ==================== ПАРСИНГ СОДЕРЖИМОГО ПОДПИСКИ ====================
def parse_subscription_content(content: str) -> Dict[str, Dict[str, Any]]:
    groups = {}
    current_group = None
    link_pattern = re.compile(r'(vless://[^\s]+|trojan://[^\s]+|hysteria2://[^\s]+|ss://[^\s]+|naive\+https?://[^\s]+)', re.I)
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # JSON
        if line.startswith("{") or line.startswith("["):
            try:
                j = json.loads(line)
                if isinstance(j, dict) and "outbounds" in j:
                    remarks = j.get("remarks", "")
                    remarks = urllib.parse.unquote(remarks) if remarks else ""
                    if remarks:
                        if remarks not in groups:
                            groups[remarks] = {"remarks":remarks,"dns":j.get("dns"),"routing":j.get("routing"),"inbounds":j.get("inbounds"),"items":[]}
                        for ob in j.get("outbounds", []):
                            if ob.get("tag") not in ("direct","block"):
                                groups[remarks]["items"].append(ob)
                    else:
                        if current_group and current_group in groups:
                            for ob in j.get("outbounds", []):
                                if ob.get("tag") not in ("direct","block"):
                                    groups[current_group]["items"].append(ob)
            except:
                pass
            continue
        # Заголовок
        if is_header_line(line):
            h = normalize_header(line)
            if h not in groups:
                groups[h] = {"remarks":h,"dns":None,"routing":None,"inbounds":None,"items":[]}
            current_group = h
            continue
        # Ссылки
        matches = link_pattern.findall(line)
        if matches:
            for link in matches:
                # извлекаем remarks (если есть)
                if current_group and current_group in groups:
                    groups[current_group]["items"].append(link)
                else:
                    if "Unknown" not in groups:
                        groups["Unknown"] = {"remarks":"Unknown","dns":None,"routing":None,"inbounds":None,"items":[]}
                    groups["Unknown"]["items"].append(link)
    return groups

# ==================== ОСНОВНАЯ ЛОГИКА ====================
def main():
    print("Загрузка списка подписок...", file=sys.stderr)
    urls = fetch_subscription_list(SOURCE_URL)
    if not urls:
        print("Нет подписок", file=sys.stderr)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        sys.exit(0)

    all_groups = {}
    for url in urls:
        print(f"Обработка: {url}", file=sys.stderr)
        content = fetch_subscription_content(url)
        if not content:
            continue
        gs = parse_subscription_content(content)
        for gname, gdata in gs.items():
            if gname in all_groups:
                all_groups[gname]["items"].extend(gdata["items"])
                if all_groups[gname]["dns"] is None and gdata["dns"] is not None:
                    all_groups[gname]["dns"] = gdata["dns"]
            else:
                all_groups[gname] = gdata

    print(f"Собрано групп: {len(all_groups)}", file=sys.stderr)

    # Переименовываем "Unknown" в "авто сервер" (если она есть)
    if "Unknown" in all_groups:
        all_groups["авто сервер"] = all_groups.pop("Unknown")
        all_groups["авто сервер"]["remarks"] = "авто сервер"

    # Собираем все ссылки из всех групп для проверки пинга
    all_links = []
    link_to_group = {}  # для обратной привязки
    for gname, gdata in all_groups.items():
        for item in gdata["items"]:
            if isinstance(item, str) and item.startswith(("vless://","trojan://","hysteria2://","ss://","naive+")):
                all_links.append(item)
                link_to_group[item] = gname

    print(f"Всего ссылок: {len(all_links)}", file=sys.stderr)

    # Проверяем пинг параллельно
    good_links = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        future_to_link = {executor.submit(check_ping, link): link for link in all_links}
        for future in as_completed(future_to_link):
            link = future_to_link[future]
            try:
                if future.result() is not None:
                    good_links.append(link)
            except:
                pass

    print(f"После пинга осталось: {len(good_links)}", file=sys.stderr)

    if not good_links:
        print("Нет рабочих ключей", file=sys.stderr)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        sys.exit(0)

    # Теперь группируем хорошие ссылки по тем же группам (но только те, которые прошли пинг)
    # Создаём словарь групп с отфильтрованными items
    filtered_groups = {}
    for gname, gdata in all_groups.items():
        filtered_items = [link for link in gdata["items"] if link in good_links]
        if filtered_items:
            filtered_groups[gname] = {
                "remarks": gdata["remarks"],
                "dns": gdata["dns"],
                "routing": gdata["routing"],
                "inbounds": gdata["inbounds"],
                "items": filtered_items
            }

    # Теперь обрабатываем группы с учётом ограничения 5 на страну
    final_groups = []
    auto_items = []
    countries = {}

    for gname, gdata in filtered_groups.items():
        items = gdata["items"]
        if not items:
            continue
        # Определяем авто
        if re.search(r'(авто|auto)', gname, re.I):
            auto_items.extend(items)
            continue
        # Определяем страну (если есть флаг в названии)
        has_flag = False
        for i in range(len(gname)-1):
            if is_flag_emoji(gname[i:i+2]):
                has_flag = True
                break
        if has_flag:
            country_name = gname
            if country_name not in countries:
                countries[country_name] = []
            countries[country_name].extend(items)
        else:
            # Пытаемся найти ключевое слово страны в названии
            lower = gname.lower()
            found = False
            for key in COUNTRY_KEYS:
                if key in lower:
                    flag, name_ru = COUNTRY_MAP[key]
                    new_name = f"{flag} {name_ru}"
                    if new_name not in countries:
                        countries[new_name] = []
                    countries[new_name].extend(items)
                    found = True
                    break
            if not found:
                # Неизвестная группа – игнорируем (или можно добавить в авто?)
                # По условию, если нет страны и не авто, то удаляем
                pass

    # Обрабатываем авто
    if auto_items:
        total_auto = len(auto_items)
        num_auto_groups = (total_auto + MAX_KEYS_PER_GROUP - 1) // MAX_KEYS_PER_GROUP
        for i in range(num_auto_groups):
            start = i * MAX_KEYS_PER_GROUP
            end = min((i+1)*MAX_KEYS_PER_GROUP, total_auto)
            group_name = "🇸🇴 Авто выбор локации 🚀" if i == 0 else f"🇸🇴 Авто выбор локации 🚀 {i+1}"
            final_groups.append({
                "remarks": group_name,
                "items": auto_items[start:end]
            })

    # Обрабатываем страны с ограничением 5 групп
    country_names = sorted(countries.keys())
    for country_name in country_names:
        items = countries[country_name]
        total = len(items)
        needed = (total + MAX_KEYS_PER_GROUP - 1) // MAX_KEYS_PER_GROUP
        max_groups = min(needed, MAX_GROUPS_PER_COUNTRY)
        for i in range(max_groups):
            start = i * MAX_KEYS_PER_GROUP
            end = min((i+1)*MAX_KEYS_PER_GROUP, total)
            group_name = country_name if i == 0 else f"{country_name} {i+1}"
            final_groups.append({
                "remarks": group_name,
                "items": items[start:end]
            })
        if needed > MAX_GROUPS_PER_COUNTRY:
            print(f"[WARN] Для страны {country_name} есть ещё {total - MAX_GROUPS_PER_COUNTRY*MAX_KEYS_PER_GROUP} ключей, они не будут включены (макс. {MAX_GROUPS_PER_COUNTRY} групп)", file=sys.stderr)

    # Построение outbound и финального JSON
    output_data = []
    for group in final_groups:
        outbounds = []
        for link in group["items"]:
            ob = build_outbound_from_link(link)
            if ob:
                outbounds.append(ob)
        if not outbounds:
            continue

        if not any(ob.get("tag") == "direct" for ob in outbounds):
            outbounds.append({"tag": "direct", "protocol": "freedom"})
        if not any(ob.get("tag") == "block" for ob in outbounds):
            outbounds.append({"tag": "block", "protocol": "blackhole"})

        counter = 1
        for ob in outbounds:
            if ob.get("tag") == "proxy":
                ob["tag"] = f"proxy-{counter}"
                counter += 1

        dns = {"servers": ["1.1.1.1", "1.0.0.1"], "queryStrategy": "UseIP"}
        routing = {
            "rules": [{"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"}],
            "domainMatcher": "hybrid",
            "domainStrategy": "IPIfNonMatch"
        }
        inbounds = [
            {"tag": "socks", "port": 10808, "listen": "127.0.0.1", "protocol": "socks",
             "settings": {"udp": True, "auth": "noauth"},
             "sniffing": {"enabled": True, "routeOnly": False, "destOverride": ["http", "tls", "quic"]}},
            {"tag": "http", "port": 10809, "listen": "127.0.0.1", "protocol": "http",
             "settings": {"allowTransparent": False},
             "sniffing": {"enabled": True, "routeOnly": False, "destOverride": ["http", "tls", "quic"]}}
        ]

        output_data.append({
            "remarks": group["remarks"],
            "dns": dns,
            "routing": routing,
            "inbounds": inbounds,
            "outbounds": outbounds
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Сохранено в {OUTPUT_FILE}, групп: {len(output_data)}", file=sys.stderr)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
