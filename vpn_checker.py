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

# ==================== Конфигурация ====================
SOURCE_URL = "https://raw.githubusercontent.com/MrZidez/free-sub/refs/heads/main/source"
USER_AGENT = "happ"
PING_THRESHOLD_MS = 90
MAX_KEYS_PER_GROUP = 20
OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.json"

COUNTRY_KEYWORDS = [
    "россия","russia","ru","сша","usa","us","америка","america",
    "германия","germany","de","нидерланды","netherlands","nl","голландия","holland",
    "франция","france","fr","великобритания","uk","united kingdom","gb",
    "канада","canada","ca","австралия","australia","au","япония","japan","jp",
    "сингапур","singapore","sg","гонконг","hong kong","hk","тайвань","taiwan","tw",
    "индия","india","in","бразилия","brazil","br","южная корея","south korea","kr",
    "италия","italy","it","испания","spain","es","швеция","sweden","se",
    "норвегия","norway","no","дания","denmark","dk","финляндия","finland","fi",
    "польша","poland","pl","украина","ukraine","ua","казахстан","kazakhstan","kz",
    "беларусь","belarus","by","турция","turkey","tr","египет","egypt","eg",
    "оаэ","uae","ae","саудовская аравия","saudi","sa","израиль","israel","il",
]

# ==================== Вспомогательные функции ====================
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
    if re.search(r'(vless|trojan|hysteria2|ss|naive)\://', line, re.I):
        return False
    if line.startswith(("{","[")):
        return False
    for i in range(len(line)-1):
        if is_flag_emoji(line[i:i+2]):
            return True
    if is_url_encoded_flag(line):
        return True
    lower = line.lower()
    return any(kw in lower for kw in COUNTRY_KEYWORDS)

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

# ==================== Загрузка подписок ====================
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

# ==================== Парсеры ссылок ====================
def parse_vless(link: str) -> dict:
    if not link.startswith("vless://"):
        return {}
    link = link[8:]
    remarks = ""
    if '#' in link:
        link, remarks = link.split('#', 1)
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
    return {"protocol":"naive","user":user,"password":password,"address":host,"port":port,"params":params,"remarks":remarks}

# ==================== Построители outbound ====================
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

# ==================== Проверка пинга ====================
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

# ==================== Парсинг содержимого ====================
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
                if current_group and current_group in groups:
                    groups[current_group]["items"].append(link)
                else:
                    if "Unknown" not in groups:
                        groups["Unknown"] = {"remarks":"Unknown","dns":None,"routing":None,"inbounds":None,"items":[]}
                    groups["Unknown"]["items"].append(link)
    return groups

# ==================== Обработка групп ====================
def process_groups(groups: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    final = []
    # Если есть только группа "Unknown", переименуем в "авто сервер"
    if len(groups) == 1 and "Unknown" in groups:
        groups["авто сервер"] = groups.pop("Unknown")
        groups["авто сервер"]["remarks"] = "авто сервер"

    for gname, gdata in groups.items():
        items = gdata["items"]
        if not items:
            continue
        links = []
        ready = []
        for item in items:
            if isinstance(item, str):
                links.append(item)
            elif isinstance(item, dict):
                ready.append(item)
        good_links = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_link = {executor.submit(check_ping, link): link for link in links}
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    if future.result() is not None:
                        good_links.append(link)
                except:
                    pass
        all_outbounds = ready.copy()
        for link in good_links:
            ob = build_outbound_from_link(link)
            if ob:
                all_outbounds.append(ob)
        if not all_outbounds:
            continue
        total = len(all_outbounds)
        num_sub = (total + MAX_KEYS_PER_GROUP - 1) // MAX_KEYS_PER_GROUP
        for i in range(num_sub):
            start = i * MAX_KEYS_PER_GROUP
            end = min((i+1)*MAX_KEYS_PER_GROUP, total)
            sub_obs = all_outbounds[start:end]
            sub_remarks = gname if i == 0 else f"{gname} {i+1}"
            dns = gdata.get("dns") or {"servers":["1.1.1.1","1.0.0.1"],"queryStrategy":"UseIP"}
            routing = gdata.get("routing") or {"rules":[{"type":"field","protocol":["bittorrent"],"outboundTag":"direct"}],"domainMatcher":"hybrid","domainStrategy":"IPIfNonMatch"}
            inbounds = gdata.get("inbounds") or [
                {"tag":"socks","port":10808,"listen":"127.0.0.1","protocol":"socks","settings":{"udp":True,"auth":"noauth"},"sniffing":{"enabled":True,"routeOnly":False,"destOverride":["http","tls","quic"]}},
                {"tag":"http","port":10809,"listen":"127.0.0.1","protocol":"http","settings":{"allowTransparent":False},"sniffing":{"enabled":True,"routeOnly":False,"destOverride":["http","tls","quic"]}}
            ]
            if not any(ob.get("tag")=="direct" for ob in sub_obs):
                sub_obs.append({"tag":"direct","protocol":"freedom"})
            if not any(ob.get("tag")=="block" for ob in sub_obs):
                sub_obs.append({"tag":"block","protocol":"blackhole"})
            counter = 1
            for ob in sub_obs:
                if ob.get("tag") == "proxy":
                    ob["tag"] = f"proxy-{counter}"
                    counter += 1
            final.append({"remarks":sub_remarks,"dns":dns,"routing":routing,"inbounds":inbounds,"outbounds":sub_obs})
    return final

# ==================== MAIN ====================
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
    result = process_groups(all_groups)
    print(f"После фильтрации: {len(result)} групп", file=sys.stderr)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Сохранено в {OUTPUT_FILE}", file=sys.stderr)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Критическая ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
