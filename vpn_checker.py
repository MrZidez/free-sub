#!/usr/bin/env python3
"""
VPN Parser & Country Grouper
Parses VPN links from sources, filters valid ones, groups by country.
Output: Sing-Box JSON format
"""

import json
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import requests

# ============================================================
#  КОНФИГУРАЦИЯ
# ============================================================
USER_AGENT = "happ"
PING_THRESHOLD_MS = 250
MAX_KEYS_PER_GROUP = 8
MAX_GROUPS_PER_COUNTRY = 5
SOURCE_FILE = "source"
OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.json"
TIMEOUT = 15
MAX_WORKERS = 10
# ============================================================

# Протоколы
VALID_PROTOCOLS = {"vless://", "trojan://", "vmess://", "hysteria://"}
EXCLUDED_PROTOCOLS = {"hy2://", "ss://", "tuic://"}

# Плохие домены
BAD_DOMAINS = {
    "mirror", "github", "gist", "raw.githubusercontent", "yandexcloud",
    "storage", "gist.githubusercontent", "githubusercontent", "cloudflare",
    "amazon", "aws", "azure", "google", "googleapis", "cloudfront",
    "heroku", "netlify", "vercel", "example", "test", "localhost",
    "127.0.0.1", "0.0.0.0", "roc-taiwan", "taipeicitygovernment",
    "seoulcitygovernment", "seoulcityhall", "kdns.fr", "hllfly.kdns.fr",
    "org.ua", "tokyometropolis", "duckdns", "no-ip", "dyndns", "ddns",
    "serveo", "ngrok", ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".xyz", ".club"
}

# Страны и флаги
COUNTRIES = {
    "🇷🇺": "Россия", "🇺🇸": "США", "🇬🇧": "Великобритания",
    "🇩🇪": "Германия", "🇫🇷": "Франция", "🇳🇱": "Нидерланды",
    "🇨🇦": "Канада", "🇦🇺": "Австралия", "🇯🇵": "Япония",
    "🇨🇳": "Китай", "🇸🇬": "Сингапур", "🇰🇷": "Южная Корея",
    "🇧🇷": "Бразилия", "🇮🇳": "Индия", "🇮🇹": "Италия",
    "🇪🇸": "Испания", "🇨🇭": "Швейцария", "🇸🇪": "Швеция",
    "🇳🇴": "Норвегия", "🇫🇮": "Финляндия", "🇩🇰": "Дания",
    "🇵🇱": "Польша", "🇺🇦": "Украина", "🇰🇿": "Казахстан",
    "🇱🇻": "Латвия", "🇪🇪": "Эстония", "🇱🇹": "Литва",
    "🇧🇾": "Беларусь", "🇹🇷": "Турция", "🇦🇪": "ОАЭ",
    "🇮🇱": "Израиль", "🇿🇦": "ЮАР", "🇦🇷": "Аргентина",
    "🇲🇽": "Мексика"
}

COUNTRY_CODES = {
    "RU": "🇷🇺", "US": "🇺🇸", "GB": "🇬🇧", "DE": "🇩🇪",
    "FR": "🇫🇷", "NL": "🇳🇱", "CA": "🇨🇦", "AU": "🇦🇺",
    "JP": "🇯🇵", "CN": "🇨🇳", "SG": "🇸🇬", "KR": "🇰🇷",
    "BR": "🇧🇷", "IN": "🇮🇳", "IT": "🇮🇹", "ES": "🇪🇸",
    "CH": "🇨🇭", "SE": "🇸🇪", "NO": "🇳🇴", "FI": "🇫🇮",
    "DK": "🇩🇰", "PL": "🇵🇱", "UA": "🇺🇦", "KZ": "🇰🇿",
    "LV": "🇱🇻", "EE": "🇪🇪", "LT": "🇱🇹", "BY": "🇧🇾",
    "TR": "🇹🇷", "AE": "🇦🇪", "IL": "🇮🇱", "ZA": "🇿🇦",
    "AR": "🇦🇷", "MX": "🇲🇽"
}

# Базовая структура Sing-Box
BASE_DNS = {
    "servers": ["1.1.1.1", "1.0.0.1"],
    "queryStrategy": "UseIP"
}

BASE_ROUTING = {
    "rules": [
        {
            "type": "field",
            "protocol": ["bittorrent"],
            "outboundTag": "direct"
        }
    ],
    "domainMatcher": "hybrid",
    "domainStrategy": "IPIfNonMatch"
}

BASE_INBOUNDS = [
    {
        "tag": "socks",
        "port": 10808,
        "listen": "127.0.0.1",
        "protocol": "socks",
        "settings": {"udp": True, "auth": "noauth"},
        "sniffing": {
            "enabled": True,
            "routeOnly": False,
            "destOverride": ["http", "tls", "quic"]
        }
    },
    {
        "tag": "http",
        "port": 10809,
        "listen": "127.0.0.1",
        "protocol": "http",
        "settings": {"allowTransparent": False},
        "sniffing": {
            "enabled": True,
            "routeOnly": False,
            "destOverride": ["http", "tls", "quic"]
        }
    }
]

BASE_OUTBOUNDS_EXTRA = [
    {"tag": "direct", "protocol": "freedom"},
    {"tag": "block", "protocol": "blackhole"}
]


def load_sources(filepath: str) -> list:
    """Загружает список URL из файла."""
    if not Path(filepath).exists():
        print(f"❌ Файл {filepath} не найден!")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def is_valid_key(key: str) -> bool:
    """Проверяет валидность ключа."""
    key = key.strip()
    if len(key) < 20:
        return False
    if not any(key.startswith(p) for p in VALID_PROTOCOLS):
        return False
    if any(key.startswith(p) for p in EXCLUDED_PROTOCOLS):
        return False
    try:
        parsed = urllib.parse.urlparse(key)
        hostname = parsed.hostname or ""
        if len(hostname) < 3:
            return False
        if not parsed.port and not parsed.path:
            return False
    except Exception:
        return False
    return True


def is_bad_domain(hostname: str) -> bool:
    if not hostname:
        return True
    hostname = hostname.lower()
    return any(bad in hostname for bad in BAD_DOMAINS)


def detect_country(key: str) -> tuple:
    try:
        for flag, country in COUNTRIES.items():
            if flag in key:
                return flag, country
        for code, flag in COUNTRY_CODES.items():
            if f"#{code}" in key or f"_{code}_" in key or f"-{code}-" in key:
                return flag, COUNTRIES.get(flag, code)
        if "://" in key:
            parsed = urllib.parse.urlparse(key)
            hostname = parsed.hostname or ""
            for code, flag in COUNTRY_CODES.items():
                if hostname.endswith(f".{code.lower()}"):
                    return flag, COUNTRIES.get(flag, code)
    except Exception:
        pass
    return None, None


def parse_vless_key(key: str) -> dict:
    """Парсит vless:// ключ в Sing-Box outbound"""
    parsed = urllib.parse.urlparse(key)
    query = urllib.parse.parse_qs(parsed.query)
    hostname = parsed.hostname or ""
    port = parsed.port or 443
    user_id = parsed.username or ""

    outbound = {
        "protocol": "vless",
        "settings": {
            "vnext": [{
                "address": hostname,
                "port": port,
                "users": [{
                    "id": user_id,
                    "encryption": query.get("encryption", ["none"])[0],
                    "flow": query.get("flow", [""])[0],
                    "level": 0
                }]
            }]
        },
        "streamSettings": {}
    }

    security = query.get("security", ["none"])[0]
    network = query.get("type", ["tcp"])[0]

    stream = {
        "network": network,
        "security": security
    }

    if network == "ws":
        ws = {"path": query.get("path", ["/"])[0]}
        if "host" in query:
            ws["headers"] = {"Host": query["host"][0]}
        stream["wsSettings"] = ws

    if network == "grpc":
        stream["grpcSettings"] = {
            "serviceName": query.get("serviceName", [""])[0],
            "multiMode": True
        }

    if network == "tcp":
        stream["tcpSettings"] = {"header": {"type": "none"}}

    if security == "tls":
        stream["tlsSettings"] = {
            "serverName": query.get("sni", [hostname])[0],
            "fingerprint": query.get("fp", ["chrome"])[0],
            "allowInsecure": False
        }

    if security == "reality":
        reality = {
            "serverName": query.get("sni", [hostname])[0],
            "fingerprint": query.get("fp", ["chrome"])[0],
            "publicKey": query.get("pbk", [""])[0],
        }
        if "sid" in query:
            reality["shortId"] = query["sid"][0]
        stream["realitySettings"] = reality

    outbound["streamSettings"] = stream
    return outbound


def parse_trojan_key(key: str) -> dict:
    """Парсит trojan:// ключ в Sing-Box outbound"""
    parsed = urllib.parse.urlparse(key)
    query = urllib.parse.parse_qs(parsed.query)
    hostname = parsed.hostname or ""
    port = parsed.port or 443
    password = parsed.username or ""

    outbound = {
        "protocol": "trojan",
        "settings": {
            "servers": [{
                "address": hostname,
                "port": port,
                "password": password,
                "sni": query.get("sni", [hostname])[0],
                "udp": True
            }]
        },
        "streamSettings": {}
    }

    security = query.get("security", ["tls"])[0]
    network = query.get("type", ["tcp"])[0]

    stream = {
        "network": network,
        "security": security
    }

    if network == "ws":
        ws = {"path": query.get("path", ["/"])[0]}
        if "host" in query:
            ws["headers"] = {"Host": query["host"][0]}
        stream["wsSettings"] = ws

    if security == "tls":
        stream["tlsSettings"] = {
            "serverName": query.get("sni", [hostname])[0],
            "fingerprint": query.get("fp", ["chrome"])[0],
            "allowInsecure": False
        }

    outbound["streamSettings"] = stream
    return outbound


def parse_key_to_outbound(key: str, index: int) -> dict:
    """Конвертирует ключ в Sing-Box outbound"""
    if key.startswith("vless://"):
        outbound = parse_vless_key(key)
    elif key.startswith("trojan://"):
        outbound = parse_trojan_key(key)
    else:
        return None

    outbound["tag"] = f"proxy-{index}"
    return outbound


def fetch_url(url: str) -> list:
    headers = {"User-Agent": USER_AGENT} if USER_AGENT else {}
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=headers)
        if resp.status_code != 200:
            return []

        lines = resp.text.split("\n")
        valid_keys = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if not is_valid_key(line):
                continue

            flag, country = detect_country(line)
            if not flag or not country:
                continue

            try:
                if "://" in line:
                    parsed = urllib.parse.urlparse(line)
                    hostname = parsed.hostname or ""
                    if is_bad_domain(hostname):
                        continue
            except Exception:
                continue

            valid_keys.append((country, line))
        return valid_keys

    except Exception as e:
        print(f"    ⚠️ {url[:50]}... ошибка: {e}")
        return []


def split_into_groups(keys: list, max_per_group: int, max_groups: int) -> list:
    if not keys:
        return []
    groups = []
    for i in range(0, min(len(keys), max_groups * max_per_group), max_per_group):
        groups.append(keys[i:i + max_per_group])
        if len(groups) >= max_groups:
            break
    return groups


def main():
    print("🚀 VPN Parser v2 (Sing-Box)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 User-Agent: {USER_AGENT or 'не задан'}")
    print(f"🎯 Порог пинга: {PING_THRESHOLD_MS} мс")
    print(f"📦 Ключей в группе: {MAX_KEYS_PER_GROUP}")
    print(f"🌍 Групп на страну: {MAX_GROUPS_PER_COUNTRY}")

    urls = load_sources(SOURCE_FILE)
    if not urls:
        print("❌ Нет источников для парсинга")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        sys.exit(0)

    print(f"📥 Источников: {len(urls)}")

    grouped = {}
    total = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_url, url): url for url in urls}

        for i, future in enumerate(as_completed(futures), 1):
            url = futures[future]
            try:
                results = future.result()
                for country, key in results:
                    grouped.setdefault(country, []).append(key)
                    total += 1
                print(f"  [{i}/{len(urls)}] ✅ {url[:50]}... → {len(results)} ключей")
            except Exception as e:
                print(f"  [{i}/{len(urls)}] ❌ {url[:50]}... ошибка: {e}")

    print(f"\n📊 Всего ключей: {total}")
    print("📊 По странам:")
    for country, keys in sorted(grouped.items(), key=lambda x: -len(x[1])):
        print(f"  {country}: {len(keys)}")

    output = []

    for country, keys in grouped.items():
        flag = None
        for f, c in COUNTRIES.items():
            if c == country:
                flag = f
                break
        if not flag:
            flag = "🌍"

        groups = split_into_groups(keys, MAX_KEYS_PER_GROUP, MAX_GROUPS_PER_COUNTRY)

        for gi, group in enumerate(groups, 1):
            outbounds = []
            for idx, key in enumerate(group, 1):
                outbound = parse_key_to_outbound(key, idx)
                if outbound:
                    outbounds.append(outbound)

            # Добавляем direct и block
            outbounds.extend(BASE_OUTBOUNDS_EXTRA)

            suffix = f" #{gi}" if len(groups) > 1 else ""

            profile = {
                "remarks": f"{flag} {country}{suffix}",
                "dns": BASE_DNS,
                "routing": BASE_ROUTING,
                "inbounds": BASE_INBOUNDS,
                "outbounds": outbounds
            }
            output.append(profile)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Сохранено {len(output)} профилей в {OUTPUT_FILE}")
    print(f"📊 Серверов: {sum(len(p['outbounds']) - 2 for p in output)}")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        sys.exit(0)
