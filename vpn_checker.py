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

# Список ключевых слов для определения страны в заголовках (русские, английские, сокращения)
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
    # можно добавить другие
]

# ==================== Вспомогательные функции ====================

def is_flag_emoji(char: str) -> bool:
    """Проверяет, является ли символ эмодзи флага (региональный индикатор)."""
    # Флаги состоят из двух региональных индикаторных символов: U+1F1E6..U+1F1FF
    # Проверяем, что оба символа в этом диапазоне
    if len(char) != 2:
        return False
    cp1 = ord(char[0])
    cp2 = ord(char[1])
    return 0x1F1E6 <= cp1 <= 0x1F1FF and 0x1F1E6 <= cp2 <= 0x1F1FF

def is_url_encoded_flag(text: str) -> bool:
    """Проверяет, содержит ли строка URL-кодированный флаг (например, %F0%9F%87%B3%F0%9F%87%B1)."""
    # Простая эвристика: если есть %F0%9F%87, то вероятно флаг
    return "%F0%9F%87" in text

def decode_url_encoded_flags(text: str) -> str:
    """Декодирует URL-кодированные последовательности в текст."""
    try:
        return urllib.parse.unquote(text)
    except Exception:
        return text

def is_header_line(line: str) -> bool:
    """
    Определяет, является ли строка заголовком группы.
    Заголовок: содержит эмодзи флага или ключевое слово страны, и не является ссылкой или JSON.
    """
    line = line.strip()
    if not line:
        return False
    # Пропускаем ссылки
    if line.startswith(("vless://", "trojan://", "hysteria2://", "ss://", "vmess://")):
        return False
    # Пропускаем JSON (начинается с { или [)
    if line.startswith(("{", "[")):
        return False
    # Проверяем наличие эмодзи флага
    # Ищем любую пару региональных индикаторов
    for i in range(len(line)-1):
        if is_flag_emoji(line[i:i+2]):
            return True
    # Проверяем наличие URL-кодированного флага
    if is_url_encoded_flag(line):
        return True
    # Проверяем наличие ключевых слов стран (регистронезависимо)
    lower_line = line.lower()
    for kw in COUNTRY_KEYWORDS:
        if kw in lower_line:
            return True
    return False

def normalize_header(header: str) -> str:
    """Очищает заголовок от лишних пробелов и декодирует URL-кодировку."""
    header = header.strip()
    header = decode_url_encoded_flags(header)
    # Убираем множественные пробелы
    header = re.sub(r'\s+', ' ', header)
    return header

def is_base64_encoded(text: str) -> bool:
    """Проверяет, похожа ли строка на base64 (без пробелов, содержит только допустимые символы)."""
    # Базовая проверка: длина кратна 4, содержит буквы/цифры/+/=/
    pattern = re.compile(r'^[A-Za-z0-9+/=]+$')
    return bool(pattern.match(text))

def decode_base64_if_needed(text: str) -> str:
    """Декодирует текст, если он является base64."""
    if is_base64_encoded(text):
        try:
            decoded = base64.b64decode(text, validate=True).decode('utf-8')
            return decoded
        except Exception:
            pass
    return text

# ==================== Загрузка и парсинг подписок ====================

def fetch_subscription_list(source_url: str) -> List[str]:
    """Загружает список подписок из source-файла."""
    try:
        resp = requests.get(source_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        # Убираем пустые строки и комментарии (#)
        urls = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
        return urls
    except Exception as e:
        print(f"Не удалось загрузить список подписок: {e}")
        return []

def fetch_subscription_content(url: str) -> str:
    """Загружает содержимое подписки, декодирует base64 при необходимости."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        content = resp.text
        # Пробуем декодировать как base64 (если весь текст выглядит как base64)
        decoded = decode_base64_if_needed(content.strip())
        return decoded
    except Exception as e:
        print(f"Не удалось загрузить подписку {url}: {e}")
        return ""

# ==================== Парсинг отдельных ссылок ====================

def parse_vless_link(link: str) -> Dict[str, Any]:
    """Парсит vless:// ссылку и возвращает словарь параметров."""
    # Формат: vless://id@address:port?params#remarks
    if not link.startswith("vless://"):
        return {}
    link = link[8:]  # убираем протокол
    # Разделяем на часть до # (remarks) и после
    if '#' in link:
        link, remarks = link.split('#', 1)
    else:
        remarks = ""
    # Разделяем на параметры (после ?) и основную часть
    if '?' in link:
        base, query = link.split('?', 1)
        params = urllib.parse.parse_qs(query)
        # приводим значения к строке (если список)
        for k, v in params.items():
            if isinstance(v, list):
                params[k] = v[0]
    else:
        base = link
        params = {}
    # Основная часть: id@address:port
    if '@' in base:
        user, host = base.split('@', 1)
        if ':' in host:
            address, port = host.split(':', 1)
            port = int(port)
        else:
            address = host
            port = 443  # порт по умолчанию
    else:
        user, address, port = "", "", 443
    result = {
        "protocol": "vless",
        "id": user,
        "address": address,
        "port": port,
        "params": params,
        "remarks": remarks
    }
    return result

def parse_trojan_link(link: str) -> Dict[str, Any]:
    """Парсит trojan:// ссылку."""
    if not link.startswith("trojan://"):
        return {}
    link = link[9:]
    if '#' in link:
        link, remarks = link.split('#', 1)
    else:
        remarks = ""
    if '?' in link:
        base, query = link.split('?', 1)
        params = urllib.parse.parse_qs(query)
        for k, v in params.items():
            if isinstance(v, list):
                params[k] = v[0]
    else:
        base = link
        params = {}
    # пароль@адрес:порт
    if '@' in base:
        password, host = base.split('@', 1)
        if ':' in host:
            address, port = host.split(':', 1)
            port = int(port)
        else:
            address = host
            port = 443
    else:
        password, address, port = "", "", 443
    return {
        "protocol": "trojan",
        "password": password,
        "address": address,
        "port": port,
        "params": params,
        "remarks": remarks
    }

def parse_hysteria2_link(link: str) -> Dict[str, Any]:
    """Парсит hysteria2:// ссылку."""
    if not link.startswith("hysteria2://"):
        return {}
    link = link[12:]
    if '#' in link:
        link, remarks = link.split('#', 1)
    else:
        remarks = ""
    if '?' in link:
        base, query = link.split('?', 1)
        params = urllib.parse.parse_qs(query)
        for k, v in params.items():
            if isinstance(v, list):
                params[k] = v[0]
    else:
        base = link
        params = {}
    # auth@address:port
    if '@' in base:
        auth, host = base.split('@', 1)
        if ':' in host:
            address, port = host.split(':', 1)
            port = int(port)
        else:
            address = host
            port = 443
    else:
        auth, address, port = "", "", 443
    return {
        "protocol": "hysteria2",
        "auth": auth,
        "address": address,
        "port": port,
        "params": params,
        "remarks": remarks
    }

def parse_ss_link(link: str) -> Dict[str, Any]:
    """Парсит ss:// ссылку (поддерживает простой формат и base64)."""
    if not link.startswith("ss://"):
        return {}
    link = link[5:]
    if '#' in link:
        link, remarks = link.split('#', 1)
    else:
        remarks = ""
    # Может быть base64-закодированная часть после ss://
    # Попробуем декодировать всё, что до @ или ?
    if '@' in link:
        # формат: method:password@host:port?params
        auth, rest = link.split('@', 1)
        if '?' in rest:
            hostport, query = rest.split('?', 1)
            params = urllib.parse.parse_qs(query)
            for k, v in params.items():
                if isinstance(v, list):
                    params[k] = v[0]
        else:
            hostport = rest
            params = {}
        if ':' in auth:
            method, password = auth.split(':', 1)
        else:
            method, password = "", ""
        if ':' in hostport:
            address, port = hostport.split(':', 1)
            port = int(port)
        else:
            address = hostport
            port = 443
    else:
        # возможно, вся строка base64
        try:
            decoded = base64.b64decode(link, validate=True).decode('utf-8')
            # теперь парсим как method:password@host:port
            if '@' in decoded:
                auth, rest = decoded.split('@', 1)
                if ':' in rest:
                    hostport, query = rest.split('?', 1) if '?' in rest else (rest, "")
                    if ':' in auth:
                        method, password = auth.split(':', 1)
                    else:
                        method, password = "", ""
                    if ':' in hostport:
                        address, port = hostport.split(':', 1)
                        port = int(port)
                    else:
                        address = hostport
                        port = 443
                    params = urllib.parse.parse_qs(query) if query else {}
                    for k, v in params.items():
                        if isinstance(v, list):
                            params[k] = v[0]
                else:
                    method, password, address, port = "", "", "", 443
                    params = {}
            else:
                method, password, address, port = "", "", "", 443
                params = {}
        except Exception:
            method, password, address, port = "", "", "", 443
            params = {}
    return {
        "protocol": "ss",
        "method": method,
        "password": password,
        "address": address,
        "port": port,
        "params": params,
        "remarks": remarks
    }

# ==================== Построение outbound-объектов ====================

def build_outbound_vless(params: Dict[str, Any]) -> Dict[str, Any]:
    """Строит outbound для vless."""
    protocol = "vless"
    settings = {
        "vnext": [
            {
                "address": params["address"],
                "port": params["port"],
                "users": [
                    {
                        "id": params["id"],
                        "flow": params.get("params", {}).get("flow", ""),
                        "encryption": "none"
                    }
                ]
            }
        ]
    }
    stream_settings = {
        "network": params.get("params", {}).get("type", "tcp"),
        "security": params.get("params", {}).get("security", "none")
    }
    # Обработка TLS/Reality
    if stream_settings["security"] == "tls":
        tls_settings = {}
        if "sni" in params.get("params", {}):
            tls_settings["serverName"] = params["params"]["sni"]
        if "fp" in params.get("params", {}):
            tls_settings["fingerprint"] = params["params"]["fp"]
        # allowInsecure? не стандартно для vless, но можно добавить
        stream_settings["tlsSettings"] = tls_settings
    elif stream_settings["security"] == "reality":
        reality_settings = {
            "serverName": params.get("params", {}).get("sni", ""),
            "fingerprint": params.get("params", {}).get("fp", ""),
            "publicKey": params.get("params", {}).get("pbk", ""),
            "shortId": params.get("params", {}).get("sid", "")
        }
        stream_settings["realitySettings"] = reality_settings
    # Настройки для разных типов network
    network = stream_settings["network"]
    if network == "ws":
        ws_settings = {
            "path": params.get("params", {}).get("path", "/"),
            "headers": {
                "Host": params.get("params", {}).get("host", "")
            }
        }
        stream_settings["wsSettings"] = ws_settings
    elif network == "grpc":
        grpc_settings = {
            "serviceName": params.get("params", {}).get("serviceName", "")
        }
        stream_settings["grpcSettings"] = grpc_settings
    elif network == "xhttp":
        xhttp_settings = {
            "path": params.get("params", {}).get("path", "/"),
            "host": params.get("params", {}).get("host", ""),
            "mode": params.get("params", {}).get("mode", ""),
            "extra": params.get("params", {}).get("extra", {}),
        }
        stream_settings["xhttpSettings"] = xhttp_settings
    # fragment, fm – можно добавить отдельно, но не обязательны

    outbound = {
        "tag": "proxy",  # будет заменён позже
        "protocol": protocol,
        "settings": settings,
        "streamSettings": stream_settings
    }
    return outbound

def build_outbound_trojan(params: Dict[str, Any]) -> Dict[str, Any]:
    """Строит outbound для trojan."""
    protocol = "trojan"
    settings = {
        "servers": [
            {
                "address": params["address"],
                "port": params["port"],
                "password": params["password"]
            }
        ]
    }
    stream_settings = {
        "network": params.get("params", {}).get("type", "tcp"),
        "security": params.get("params", {}).get("security", "none")
    }
    if stream_settings["security"] == "tls":
        tls_settings = {}
        if "sni" in params.get("params", {}):
            tls_settings["serverName"] = params["params"]["sni"]
        if "fp" in params.get("params", {}):
            tls_settings["fingerprint"] = params["params"]["fp"]
        stream_settings["tlsSettings"] = tls_settings
    network = stream_settings["network"]
    if network == "ws":
        ws_settings = {
            "path": params.get("params", {}).get("path", "/"),
            "headers": {
                "Host": params.get("params", {}).get("host", "")
            }
        }
        stream_settings["wsSettings"] = ws_settings
    elif network == "grpc":
        grpc_settings = {
            "serviceName": params.get("params", {}).get("serviceName", "")
        }
        stream_settings["grpcSettings"] = grpc_settings

    outbound = {
        "tag": "proxy",
        "protocol": protocol,
        "settings": settings,
        "streamSettings": stream_settings
    }
    return outbound

def build_outbound_hysteria2(params: Dict[str, Any]) -> Dict[str, Any]:
    """Строит outbound для hysteria2."""
    protocol = "hysteria"
    settings = {
        "address": params["address"],
        "port": params["port"],
        "version": 2
    }
    stream_settings = {
        "network": "hysteria",
        "security": params.get("params", {}).get("security", "tls"),
        "hysteriaSettings": {
            "version": 2,
            "auth": params["auth"]
        }
    }
    if stream_settings["security"] == "tls":
        tls_settings = {}
        if "sni" in params.get("params", {}):
            tls_settings["serverName"] = params["params"]["sni"]
        if "fp" in params.get("params", {}):
            tls_settings["fingerprint"] = params["params"]["fp"]
        if "allowinsecure" in params.get("params", {}):
            tls_settings["allowInsecure"] = params["params"]["allowinsecure"] == "1"
        stream_settings["tlsSettings"] = tls_settings

    outbound = {
        "tag": "proxy",
        "protocol": protocol,
        "settings": settings,
        "streamSettings": stream_settings
    }
    return outbound

def build_outbound_ss(params: Dict[str, Any]) -> Dict[str, Any]:
    """Строит outbound для shadowsocks."""
    protocol = "shadowsocks"
    settings = {
        "servers": [
            {
                "address": params["address"],
                "port": params["port"],
                "method": params["method"],
                "password": params["password"],
                "uot": True
            }
        ]
    }
    outbound = {
        "tag": "proxy",
        "protocol": protocol,
        "settings": settings
    }
    return outbound

def build_outbound_from_link(link: str) -> Dict[str, Any]:
    """Парсит ссылку и возвращает outbound-объект (без тега)."""
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
    return {}

def get_host_port_from_link(link: str) -> Tuple[str, int]:
    """Извлекает адрес и порт из ссылки для пинга."""
    if link.startswith("vless://"):
        parsed = parse_vless_link(link)
        return parsed.get("address", ""), parsed.get("port", 443)
    elif link.startswith("trojan://"):
        parsed = parse_trojan_link(link)
        return parsed.get("address", ""), parsed.get("port", 443)
    elif link.startswith("hysteria2://"):
        parsed = parse_hysteria2_link(link)
        return parsed.get("address", ""), parsed.get("port", 443)
    elif link.startswith("ss://"):
        parsed = parse_ss_link(link)
        return parsed.get("address", ""), parsed.get("port", 443)
    return "", 443

# ==================== Проверка пинга ====================

def check_ping_icmp(host: str, timeout: float = 2.0) -> Optional[float]:
    """Проверяет ICMP ping, возвращает задержку в мс или None."""
    if ping is None:
        return None
    try:
        # ping3 возвращает float (секунды) или None
        delay = ping(host, timeout=timeout)
        if delay is not None and delay > 0:
            return delay * 1000  # в мс
    except Exception:
        pass
    return None

def check_ping_tcp(host: str, port: int, timeout: float = 2.0) -> Optional[float]:
    """Проверяет TCP соединение, возвращает задержку в мс или None."""
    try:
        start = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            end = time.time()
            return (end - start) * 1000
    except Exception:
        return None

def check_ping(link: str) -> Optional[float]:
    """Проверяет пинг по ссылке (ICMP и TCP), возвращает минимальную задержку в мс или None."""
    host, port = get_host_port_from_link(link)
    if not host:
        return None
    # Пробуем ICMP
    delay = check_ping_icmp(host)
    if delay is not None and delay < PING_THRESHOLD_MS:
        return delay
    # Пробуем TCP
    delay = check_ping_tcp(host, port)
    if delay is not None and delay < PING_THRESHOLD_MS:
        return delay
    return None

# ==================== Парсинг содержимого подписки ====================

def parse_subscription_content(content: str) -> Dict[str, Dict[str, Any]]:
    """
    Парсит текст подписки и возвращает словарь групп.
    Каждая группа имеет вид:
    {
        "remarks": str,
        "source_type": "header" | "json",
        "dns": dict | None,
        "routing": dict | None,
        "inbounds": list | None,
        "items": list  # строки ссылок или готовые outbound-объекты
    }
    """
    groups = {}
    current_group_name = None

    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Обработка JSON-конфига
        if line.startswith("{") or line.startswith("["):
            try:
                json_obj = json.loads(line)
                # Проверяем, является ли это конфигом с outbounds
                if isinstance(json_obj, dict) and "outbounds" in json_obj:
                    remarks = json_obj.get("remarks", "")
                    # Если есть remarks, создаём/используем группу с этим именем
                    if remarks:
                        group_name = remarks
                        if group_name not in groups:
                            groups[group_name] = {
                                "remarks": group_name,
                                "source_type": "json",
                                "dns": json_obj.get("dns"),
                                "routing": json_obj.get("routing"),
                                "inbounds": json_obj.get("inbounds"),
                                "items": []
                            }
                        else:
                            # Если группа уже существует, не перезаписываем dns/routing/inbounds
                            # (оставляем первые)
                            pass
                        # Добавляем outbounds (кроме direct/block)
                        outbounds = json_obj.get("outbounds", [])
                        for ob in outbounds:
                            if ob.get("tag") not in ("direct", "block"):
                                groups[group_name]["items"].append(ob)
                    else:
                        # Нет remarks – добавляем outbounds в текущую группу (если есть)
                        if current_group_name and current_group_name in groups:
                            outbounds = json_obj.get("outbounds", [])
                            for ob in outbounds:
                                if ob.get("tag") not in ("direct", "block"):
                                    groups[current_group_name]["items"].append(ob)
                        # Если нет текущей группы, игнорируем
                else:
                    # Другой JSON – возможно, это просто данные, пропускаем
                    pass
            except json.JSONDecodeError:
                # Невалидный JSON – возможно, это просто строка, идём дальше
                pass
            continue

        # Проверка на заголовок группы
        if is_header_line(line):
            header = normalize_header(line)
            # Если заголовок уже есть, используем его как есть
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

        # Если это ссылка
        if line.startswith(("vless://", "trojan://", "hysteria2://", "ss://")):
            if current_group_name and current_group_name in groups:
                groups[current_group_name]["items"].append(line)
            else:
                # Если нет группы, создаём группу "Без группы" или игнорируем?
                # По условию, если нет флага, то игнорируем? Но лучше создать временную
                # или пропустить. Пропустим, чтобы не плодить мусор.
                # Но если позже появится заголовок, то эти ссылки не попадут.
                # Лучше сохранять в отдельную группу "Unknown", но по заданию лучше игнорировать.
                pass
        # Иначе, возможно, это комментарий или что-то ещё – пропускаем

    return groups

# ==================== Основной процесс ====================

def process_groups(groups: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Фильтрует ключи по пингу, разбивает группы по 20, строит итоговые JSON-объекты.
    Возвращает список готовых групп.
    """
    final_groups = []

    # Сначала для каждой группы фильтруем ключи по пингу
    for group_name, group_data in groups.items():
        items = group_data["items"]
        if not items:
            continue

        # Разделяем items на ссылки и готовые outbound-объекты
        links = []
        ready_outbounds = []
        for item in items:
            if isinstance(item, str) and item.startswith(("vless://", "trojan://", "hysteria2://", "ss://")):
                links.append(item)
            elif isinstance(item, dict):
                ready_outbounds.append(item)
            # иначе игнорируем

        # Проверяем пинг для ссылок (параллельно)
        good_links = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_link = {executor.submit(check_ping, link): link for link in links}
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    delay = future.result()
                    if delay is not None:
                        good_links.append((link, delay))
                    # иначе отбрасываем
                except Exception:
                    pass

        # Сортируем по задержке (по возрастанию)
        good_links.sort(key=lambda x: x[1])

        # Извлекаем только ссылки
        filtered_links = [link for link, _ in good_links]

        # Все outbound-объекты: сначала готовые, затем построенные из ссылок
        all_outbounds = ready_outbounds.copy()
        for link in filtered_links:
            ob = build_outbound_from_link(link)
            if ob:
                all_outbounds.append(ob)

        if not all_outbounds:
            continue  # группа пуста

        # Теперь разбиваем на подгруппы по MAX_KEYS_PER_GROUP
        total = len(all_outbounds)
        num_subgroups = (total + MAX_KEYS_PER_GROUP - 1) // MAX_KEYS_PER_GROUP

        for i in range(num_subgroups):
            start = i * MAX_KEYS_PER_GROUP
            end = min((i+1) * MAX_KEYS_PER_GROUP, total)
            sub_outbounds = all_outbounds[start:end]

            # Название подгруппы
            if i == 0:
                sub_remarks = group_name
            else:
                sub_remarks = f"{group_name} {i+1}"

            # Копируем dns, routing, inbounds из группы (если есть)
            dns = group_data.get("dns")
            routing = group_data.get("routing")
            inbounds = group_data.get("inbounds")

            # Если нет dns/routing/inbounds – используем стандартные
            if dns is None:
                dns = {
                    "servers": ["1.1.1.1", "1.0.0.1"],
                    "queryStrategy": "UseIP"
                }
            if routing is None:
                routing = {
                    "rules": [
                        {"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"}
                    ],
                    "domainMatcher": "hybrid",
                    "domainStrategy": "IPIfNonMatch"
                }
            if inbounds is None:
                inbounds = [
                    {
                        "tag": "socks",
                        "port": 10808,
                        "listen": "127.0.0.1",
                        "protocol": "socks",
                        "settings": {"udp": True, "auth": "noauth"},
                        "sniffing": {"enabled": True, "routeOnly": False, "destOverride": ["http", "tls", "quic"]}
                    },
                    {
                        "tag": "http",
                        "port": 10809,
                        "listen": "127.0.0.1",
                        "protocol": "http",
                        "settings": {"allowTransparent": False},
                        "sniffing": {"enabled": True, "routeOnly": False, "destOverride": ["http", "tls", "quic"]}
                    }
                ]

            # Добавляем direct и block, если их нет
            has_direct = any(ob.get("tag") == "direct" for ob in sub_outbounds)
            has_block = any(ob.get("tag") == "block" for ob in sub_outbounds)
            if not has_direct:
                sub_outbounds.append({"tag": "direct", "protocol": "freedom"})
            if not has_block:
                sub_outbounds.append({"tag": "block", "protocol": "blackhole"})

            # Переименовываем теги proxy, чтобы избежать дублирования
            proxy_counter = 1
            for ob in sub_outbounds:
                if ob.get("tag") == "proxy":
                    ob["tag"] = f"proxy-{proxy_counter}"
                    proxy_counter += 1

            # Формируем итоговый объект группы
            group_obj = {
                "remarks": sub_remarks,
                "dns": dns,
                "routing": routing,
                "inbounds": inbounds,
                "outbounds": sub_outbounds
            }
            final_groups.append(group_obj)

    return final_groups

def save_result(data: List[Dict[str, Any]], filename: str):
    """Сохраняет результат в JSON файл."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== Главная функция ====================

def main():
    print("Загрузка списка подписок...")
    sub_urls = fetch_subscription_list(SOURCE_URL)
    if not sub_urls:
        print("Нет подписок для обработки.")
        return

    all_groups = {}
    for sub_url in sub_urls:
        print(f"Обработка подписки: {sub_url}")
        content = fetch_subscription_content(sub_url)
        if not content:
            continue
        groups = parse_subscription_content(content)
        # Объединяем группы из разных подписок
        for gname, gdata in groups.items():
            if gname in all_groups:
                # Объединяем items
                all_groups[gname]["items"].extend(gdata["items"])
                # Если одна из групп имеет dns/routing/inbounds, а другая нет, оставляем первую
                if all_groups[gname]["dns"] is None and gdata["dns"] is not None:
                    all_groups[gname]["dns"] = gdata["dns"]
                if all_groups[gname]["routing"] is None and gdata["routing"] is not None:
                    all_groups[gname]["routing"] = gdata["routing"]
                if all_groups[gname]["inbounds"] is None and gdata["inbounds"] is not None:
                    all_groups[gname]["inbounds"] = gdata["inbounds"]
                # source_type не важен
            else:
                all_groups[gname] = gdata

    print(f"Собрано групп: {len(all_groups)}")
    # Фильтрация и разбиение
    final_data = process_groups(all_groups)
    print(f"После фильтрации и разбиения: {len(final_data)} групп")

    if final_data:
        save_result(final_data, OUTPUT_FILE)
        print(f"Результат сохранён в {OUTPUT_FILE}")
    else:
        print("Нет подходящих ключей.")

if __name__ == "__main__":
    # Скрипт запускается один раз, но можно поместить в бесконечный цикл с интервалом 1488 часов
    # Для демонстрации выполним однократно.
    main()
    # Если нужен бесконечный цикл, раскомментировать:
    # while True:
    #     main()
    #     time.sleep(1488 * 3600)
