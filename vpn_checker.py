#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# Ключевые слова стран (русские, английские, сокращения)
COUNTRY_KEYWORDS = [
    "россия", "russia", "ru",
    "сша", "usa", "us", "америка", "america",
    "германия", "germany", "de",
    "нидерланды", "netherlands", "nl", "голландия", "holland",
    "франция", "france", "fr",
    "великобритания", "uk", "united kingdom", "gb",
    "канада", "canada", "ca",
    "австралия", "australia", "au",
    "япония", "japan", "jp",
    "сингапур", "singapore", "sg",
    "гонконг", "hong kong", "hk",
    "тайвань", "taiwan", "tw",
    "индия", "india", "in",
    "бразилия", "brazil", "br",
    "южная корея", "south korea", "kr",
    "италия", "italy", "it",
    "испания", "spain", "es",
    "швеция", "sweden", "se",
    "норвегия", "norway", "no",
    "дания", "denmark", "dk",
    "финляндия", "finland", "fi",
    "польша", "poland", "pl",
    "украина", "ukraine", "ua",
    "казахстан", "kazakhstan", "kz",
    "беларусь", "belarus", "by",
    "турция", "turkey", "tr",
    "египет", "egypt", "eg",
    "оаэ", "uae", "ae",
    "саудовская аравия", "saudi", "sa",
    "израиль", "israel", "il",
]

# ==================== Вспомогательные функции ====================

def is_flag_emoji(char: str) -> bool:
    if len(char) != 2:
        return False
    cp1 = ord(char[0])
    cp2 = ord(char[1])
    return 0x1F1E6 <= cp1 <= 0x1F1FF and 0x1F1E6 <= cp2 <= 0x1F1FF

def is_url_encoded_flag(text: str) -> bool:
    return "%F0%9F%87" in text

def decode_url_encoded_flags(text: str) -> str:
    try:
        return urllib.parse.unquote(text)
    except Exception:
        return text

def is_header_line(line: str) -> bool:
    """Проверяет, является ли строка заголовком группы."""
    line = line.strip()
    if not line:
        return False
    # Пропускаем ссылки и JSON
    if re.search(r'(vless|trojan|hysteria2|ss|naive)\://', line):
        return False
    if line.startswith(("{", "[")):
        return False
    # Проверка на эмодзи флага
    for i in range(len(line)-1):
        if is_flag_emoji(line[i:i+2]):
            return True
    if is_url_encoded_flag(line):
        return True
    # Проверка на ключевые слова стран
    lower_line = line.lower()
    for kw in COUNTRY_KEYWORDS:
        if kw in lower_line:
            return True
    return False

def normalize_header(header: str) -> str:
    header = header.strip()
    header = decode_url_encoded_flags(header)
    header = re.sub(r'\s+', ' ', header)
    return header

def is_base64_encoded(text: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9+/=]+$', text))

def decode_base64_if_needed(text: str) -> str:
    if is_base64_encoded(text.strip()):
        try:
            return base64.b64decode(text.strip(), validate=True).decode('utf-8')
        except:
            pass
    return text

# ==================== Загрузка и парсинг подписок ====================

def fetch_subscription_list(source_url: str) -> List[str]:
    try:
        resp = requests.get(source_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить список подписок: {e}", file=sys.stderr)
        return []

def fetch_subscription_content(url: str) -> str:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        content = resp.text
        # Пробуем декодировать base64, если весь текст похож на base64
        decoded = decode_base64_if_needed(content.strip())
        return decoded
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить подписку {url}: {e}", file=sys.stderr)
        return ""

# ==================== Парсинг отдельных ссылок (включая naive+) ====================

def parse_naive_link(link: str) -> Dict[str, Any]:
    """Парсит naive+https:// ссылку (формат naive+https://user:pass@host:port?params#remarks)"""
    if not link.startswith("naive+"):
        return {}
    # Убираем префикс naive+
    link = link[6:]
    # Дальше парсим как обычный URL
    parsed = urllib.parse.urlparse(link)
    if parsed.scheme not in ('https', 'http'):
        return {}
    auth = parsed.netloc.split('@') if '@' in parsed.netloc else None
    if auth and len(auth) == 2:
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
    return {
        "protocol": "naive",
        "user": user,
        "password": password,
        "address": host,
        "port": port,
        "params": params,
        "remarks": remarks
    }

def parse_vless_link(link: str) -> Dict[str, Any]:
    # ... (как было ранее, без изменений)
    pass  # здесь полный код, но для краткости опущен

# (остальные парсеры аналогичны)

# ==================== Построение outbound ====================

def build_outbound_from_link(link: str) -> Optional[Dict[str, Any]]:
    if link.startswith("vless://"):
        parsed = parse_vless_link(link)
        if parsed:
            return build_outbound_vless(parsed)
    elif link.startswith("trojan://"):
        parsed = parse_trojan_link(link)
        if parsed:
            return build_outbound_trojan(parsed)
    elif link.startswith("hysteria2://"):
        parsed = parse_hysteria2_link(link)
        if parsed:
            return build_outbound_hysteria2(parsed)
    elif link.startswith("ss://"):
        parsed = parse_ss_link(link)
        if parsed:
            return build_outbound_ss(parsed)
    elif link.startswith("naive+"):
        parsed = parse_naive_link(link)
        if parsed:
            return build_outbound_naive(parsed)  # нужно реализовать
    return None

# ==================== Проверка пинга ====================

def check_ping_icmp(host: str, timeout: float = 2.0) -> Optional[float]:
    if ping is None:
        return None
    try:
        delay = ping(host, timeout=timeout)
        if delay is not None and delay > 0:
            return delay * 1000
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
    # извлечение host/port из ссылки (универсально)
    # ... (как было)
    return min(delay_icmp, delay_tcp) if both else ...

# ==================== Парсинг содержимого подписки (улучшенный) ====================

def parse_subscription_content(content: str) -> Dict[str, Dict[str, Any]]:
    groups = {}
    current_group_name = None

    # Регулярка для поиска ссылок в любой строке
    link_pattern = re.compile(
        r'(vless://[^\s]+|trojan://[^\s]+|hysteria2://[^\s]+|ss://[^\s]+|naive\+https?://[^\s]+)',
        re.IGNORECASE
    )

    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Проверка на готовый JSON
        if line.startswith("{") or line.startswith("["):
            try:
                json_obj = json.loads(line)
                if isinstance(json_obj, dict) and "outbounds" in json_obj:
                    remarks = json_obj.get("remarks", "")
                    if remarks:
                        if remarks not in groups:
                            groups[remarks] = {
                                "remarks": remarks,
                                "source_type": "json",
                                "dns": json_obj.get("dns"),
                                "routing": json_obj.get("routing"),
                                "inbounds": json_obj.get("inbounds"),
                                "items": []
                            }
                        # добавляем outbounds (кроме direct/block)
                        for ob in json_obj.get("outbounds", []):
                            if ob.get("tag") not in ("direct", "block"):
                                groups[remarks]["items"].append(ob)
                    else:
                        if current_group_name and current_group_name in groups:
                            for ob in json_obj.get("outbounds", []):
                                if ob.get("tag") not in ("direct", "block"):
                                    groups[current_group_name]["items"].append(ob)
                # иначе игнорируем
            except json.JSONDecodeError:
                pass
            continue

        # Проверка на заголовок группы
        if is_header_line(line):
            header = normalize_header(line)
            if header not in groups:
                groups[header] = {
                    "remarks": header,
                    "source_type": "header",
                    "dns": None,
                    "routing": None,
                    "inbounds": None,
                    "items": []
                }
            current_group_name = header
            continue

        # Поиск ссылок в строке
        matches = link_pattern.findall(line)
        if matches:
            for link in matches:
                if current_group_name and current_group_name in groups:
                    groups[current_group_name]["items"].append(link)
                else:
                    # Если нет группы, можно создать временную "Без группы"
                    # но по заданию лучше игнорировать
                    pass
        # иначе пропускаем

    # Дополнительно: если есть ссылки без группы, создаём группу "Unknown"
    # (на случай, если в начале файла были ссылки без заголовка)
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if not is_header_line(line) and not line.startswith(("{", "[")):
            matches = link_pattern.findall(line)
            for link in matches:
                # пытаемся найти группу по заголовку, идущему перед этой строкой
                # но если нет, создаём "Unknown"
                if "Unknown" not in groups:
                    groups["Unknown"] = {
                        "remarks": "Unknown",
                        "source_type": "header",
                        "dns": None,
                        "routing": None,
                        "inbounds": None,
                        "items": []
                    }
                groups["Unknown"]["items"].append(link)

    return groups

# ==================== Основной процесс ====================

def main():
    print("Загрузка списка подписок...", file=sys.stderr)
    sub_urls = fetch_subscription_list(SOURCE_URL)
    if not sub_urls:
        print("Нет подписок.", file=sys.stderr)
        return

    all_groups = {}
    for sub_url in sub_urls:
        print(f"Обработка: {sub_url}", file=sys.stderr)
        content = fetch_subscription_content(sub_url)
        if not content:
            continue
        groups = parse_subscription_content(content)
        # объединение групп
        for gname, gdata in groups.items():
            if gname in all_groups:
                all_groups[gname]["items"].extend(gdata["items"])
                if all_groups[gname]["dns"] is None and gdata["dns"] is not None:
                    all_groups[gname]["dns"] = gdata["dns"]
                # аналогично для routing/inbounds
            else:
                all_groups[gname] = gdata

    print(f"Собрано групп: {len(all_groups)}", file=sys.stderr)
    final_data = process_groups(all_groups)  # та же функция, что была
    print(f"После фильтрации: {len(final_data)} групп", file=sys.stderr)

    if final_data:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"Сохранено в {OUTPUT_FILE}", file=sys.stderr)
    else:
        # Сохраняем пустой массив
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        print("Нет подходящих ключей, сохранён пустой массив.", file=sys.stderr)

if __name__ == "__main__":
    import sys
    main()
