#!/usr/bin/env python3
"""
VPN Parser & Country Grouper for Happ (Xray-core)
Parses VPN links, filters, groups by country, outputs Xray JSON.
Supports: VLESS, VMess, Trojan, Hysteria2 (hy2://)
"""

import sys
import os
import json
import time
import logging
import urllib.parse
import base64
import socket
import hashlib
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Dict, Any

try:
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing dependency: {e}. Install: pip install requests python-dotenv")
    sys.exit(1)

# ============================================================
#  SAFE STARTUP (no .env leakage)
# ============================================================
print("=" * 60)
print("🚀 VPN Parser v4 (Happ / Xray-core)")
print(f"🐍 Python: {sys.version}")
print(f"📁 CWD: {os.getcwd()}")
print("=" * 60)

if os.path.exists('.env'):
    print("✅ .env found (contents NOT printed)")
else:
    print("⚠️ .env not found")

# ============================================================
#  ENV LOAD
# ============================================================
load_dotenv()

def get_env(key: str, default: Any = None) -> Any:
    value = os.getenv(key, default)
    if value is None:
        return default
    if isinstance(default, bool):
        return str(value).lower() in ("true", "1", "yes", "on")
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    return value

# ============================================================
#  CONFIG
# ============================================================
USER_AGENT = get_env("USER_AGENT", "happ")
MAX_KEYS_PER_GROUP = get_env("MAX_KEYS_PER_GROUP", 8)
MAX_GROUPS_PER_COUNTRY = get_env("MAX_GROUPS_PER_COUNTRY", 5)
SOURCE_FILE = get_env("SOURCE_FILE", "source")
OUTPUT_FILE = get_env("OUTPUT_FILE", "FREE-VPN-FROM-KIRILL.json")
TIMEOUT = get_env("TIMEOUT", 15)
MAX_WORKERS = get_env("MAX_WORKERS", 10)

CACHE_ENABLED = get_env("CACHE_ENABLED", False)
CACHE_TTL = get_env("CACHE_TTL", 3600)
CACHE_DIR = get_env("CACHE_DIR", "cache")

RETRY_ENABLED = get_env("RETRY_ENABLED", True)
RETRY_COUNT = get_env("RETRY_COUNT", 3)
RETRY_DELAY = get_env("RETRY_DELAY", 2)

ENABLE_TCP_CHECK = get_env("ENABLE_TCP_CHECK", False)
TCP_CHECK_TIMEOUT = get_env("TCP_CHECK_TIMEOUT", 3)

ENABLE_DEDUP = get_env("ENABLE_DEDUP", True)
ENABLE_LOGGING = get_env("ENABLE_LOGGING", True)
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
LOG_DIR = get_env("LOG_DIR", "logs")
COMPRESS_OUTPUT = get_env("COMPRESS_OUTPUT", False)

TG_BOT_TOKEN = get_env("TG_BOT_TOKEN", "")
TG_CHAT_ID = get_env("TG_CHAT_ID", "")
TG_NOTIFY_ON_SUCCESS = get_env("TG_NOTIFY_ON_SUCCESS", True)
TG_NOTIFY_ON_ERROR = get_env("TG_NOTIFY_ON_ERROR", True)
TG_DISABLED = not TG_BOT_TOKEN or not TG_CHAT_ID

print(f"📋 OUTPUT: {OUTPUT_FILE}")
print(f"📋 TCP-check: {'ON' if ENABLE_TCP_CHECK else 'OFF'}")
print("=" * 60)

# ============================================================
#  LOGGING
# ============================================================
Path(LOG_DIR).mkdir(exist_ok=True)
if CACHE_ENABLED:
    Path(CACHE_DIR).mkdir(exist_ok=True)

if ENABLE_LOGGING:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(Path(LOG_DIR) / "vpn-parser.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(handlers=[logging.NullHandler()])

logger = logging.getLogger(__name__)

# ============================================================
#  PROTOCOLS & COUNTRIES
# ============================================================
VALID_PROTOCOLS = ("vless://", "vmess://", "trojan://", "hysteria2://", "hy2://")
EXCLUDED_PROTOCOLS = ("hysteria://", "ss://", "tuic://")

BAD_DOMAINS = {
    "mirror", "github", "gist", "raw.githubusercontent", "yandexcloud",
    "storage", "gist.githubusercontent", "githubusercontent", "cloudflare",
    "amazon", "aws", "azure", "google", "googleapis", "cloudfront",
    "heroku", "netlify", "vercel", "example", "test", "localhost",
    "127.0.0.1", "0.0.0.0", "duckdns", "no-ip", "dyndns", "ddns",
    "serveo", "ngrok", ".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".xyz", ".club"
}

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

# O(1) reverse lookup
COUNTRY_TO_FLAG = {v: k for k, v in COUNTRIES.items()}

# ============================================================
#  XRAY BASE STRUCTURE (for Happ)
# ============================================================
BASE_DNS = {"servers": ["1.1.1.1", "1.0.0.1"], "queryStrategy": "UseIP"}

BASE_ROUTING = {
    "rules": [{"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"}],
    "domainMatcher": "hybrid",
    "domainStrategy": "IPIfNonMatch"
}

BASE_INBOUNDS = [
    {
        "tag": "socks", "port": 10808, "listen": "127.0.0.1", "protocol": "socks",
        "settings": {"udp": True, "auth": "noauth"},
        "sniffing": {"enabled": True, "routeOnly": False, "destOverride": ["http", "tls", "quic"]}
    },
    {
        "tag": "http", "port": 10809, "listen": "127.0.0.1", "protocol": "http",
        "settings": {"allowTransparent": False},
        "sniffing": {"enabled": True, "routeOnly": False, "destOverride": ["http", "tls", "quic"]}
    }
]

BASE_OUTBOUNDS_EXTRA = [
    {"tag": "direct", "protocol": "freedom"},
    {"tag": "block", "protocol": "blackhole"}
]

# ============================================================
#  HELPERS
# ============================================================
def load_sources(filepath: str) -> List[str]:
    if not Path(filepath).exists():
        logger.error(f"Source file {filepath} not found")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

def get_cache_path(url: str) -> Path:
    return Path(CACHE_DIR) / f"{hashlib.md5(url.encode()).hexdigest()}.cache"

def load_from_cache(url: str) -> Optional[List[Tuple[str, str]]]:
    if not CACHE_ENABLED:
        return None
    p = get_cache_path(url)
    if not p.exists() or time.time() - p.stat().st_mtime > CACHE_TTL:
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_to_cache(url: str, data: List[Tuple[str, str]]) -> None:
    if not CACHE_ENABLED:
        return
    try:
        with open(get_cache_path(url), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Cache save failed: {e}")

def fetch_with_retry(url: str) -> Optional[requests.Response]:
    attempts = RETRY_COUNT if RETRY_ENABLED else 1
    headers = {"User-Agent": USER_AGENT} if USER_AGENT else {}
    for attempt in range(attempts):
        try:
            resp = requests.get(url, timeout=TIMEOUT, headers=headers)
            if resp.status_code == 200:
                return resp
            if attempt < attempts - 1:
                wait = RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Retry {attempt+1}/{attempts} {url[:50]}... status {resp.status_code}, wait {wait}s")
                time.sleep(wait)
        except Exception as e:
            if attempt < attempts - 1:
                wait = RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Retry {attempt+1}/{attempts} {url[:50]}... error: {e}, wait {wait}s")
                time.sleep(wait)
            else:
                logger.error(f"Failed {url[:50]}...: {e}")
    return None

def is_valid_key(key: str) -> bool:
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
        # Hysteria2 may omit port in multi-port format
        if not parsed.port and not parsed.path and not key.startswith(("hysteria2://", "hy2://")):
            return False
        if key.startswith("vmess://"):
            encoded = key.replace("vmess://", "")
            missing = len(encoded) % 4
            if missing:
                encoded += "=" * (4 - missing)
            json.loads(base64.b64decode(encoded).decode("utf-8"))
    except Exception:
        return False
    return True

def is_bad_domain(hostname: str) -> bool:
    if not hostname:
        return True
    h = hostname.lower()
    return any(bad in h for bad in BAD_DOMAINS)

def detect_country(key: str) -> Tuple[Optional[str], Optional[str]]:
    """Returns (flag, country_name). O(1) for emoji lookup."""
    # 1) Emoji in key
    for flag in COUNTRY_TO_FLAG:
        if flag in key:
            return flag, COUNTRY_TO_FLAG[flag]

    # 2) Country code in tag (#RU, #RU-Server, #RU_Server, #RU Server)
    for code, flag in COUNTRY_CODES.items():
        for sep in ("#", "_", "-"):
            marker = f"{sep}{code}"
            idx = key.find(marker)
            if idx != -1:
                after = key[idx + len(marker):idx + len(marker) + 1]
                if not after or not after.isalnum():
                    return flag, COUNTRIES.get(flag, code)

    # 3) Country code in hostname
    try:
        hostname = (urllib.parse.urlparse(key).hostname or "").lower()
        for code, flag in COUNTRY_CODES.items():
            if hostname.endswith(f".{code.lower()}"):
                return flag, COUNTRIES.get(flag, code)
    except Exception:
        pass

    return None, None

def tcp_check(hostname: str, port: int, timeout: float = 3.0) -> bool:
    """TCP-connect check (works on GitHub Actions without ICMP)."""
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except Exception:
        return False

def parse_hysteria2_host_port(parsed) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Hysteria2 multi-port: host:1234,5000-6000
    urllib cannot parse this correctly.
    Returns (host, first_port_or_443, port_range_or_None)
    """
    netloc = parsed.netloc or ""
    if "@" in netloc:
        netloc = netloc.split("@", 1)[1]
    if ":" not in netloc:
        return netloc, 443, None
    host, port_part = netloc.rsplit(":", 1)
    if "," in port_part or "-" in port_part:
        first = port_part.split(",")[0].split("-")[0]
        try:
            return host, int(first), port_part
        except ValueError:
            return host, 443, port_part
    try:
        return host, int(port_part), None
    except ValueError:
        return host, 443, None

# ============================================================
#  PARSERS (Xray format for Happ)
# ============================================================
def parse_vless_key(key: str) -> Optional[Dict]:
    try:
        parsed = urllib.parse.urlparse(key)
        q = urllib.parse.parse_qs(parsed.query)
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
                        "encryption": q.get("encryption", ["none"])[0],
                        "flow": q.get("flow", [""])[0],
                        "level": 0
                    }]
                }]
            },
            "streamSettings": {}
        }

        security = q.get("security", ["none"])[0]
        network = q.get("type", ["tcp"])[0]
        stream = {"network": network, "security": security}

        if network == "ws":
            ws = {"path": q.get("path", ["/"])[0]}
            if "host" in q:
                ws["headers"] = {"Host": q["host"][0]}
            stream["wsSettings"] = ws
        elif network == "grpc":
            stream["grpcSettings"] = {"serviceName": q.get("serviceName", [""])[0], "multiMode": True}
        elif network == "tcp":
            stream["tcpSettings"] = {"header": {"type": "none"}}

        if security == "tls":
            stream["tlsSettings"] = {
                "serverName": q.get("sni", [hostname])[0],
                "fingerprint": q.get("fp", ["chrome"])[0],
                "allowInsecure": False
            }
        elif security == "reality":
            reality = {
                "serverName": q.get("sni", [hostname])[0],
                "fingerprint": q.get("fp", ["chrome"])[0],
                "publicKey": q.get("pbk", [""])[0],
            }
            if "sid" in q:
                reality["shortId"] = q["sid"][0]
            stream["realitySettings"] = reality

        outbound["streamSettings"] = stream
        return outbound
    except Exception as e:
        logger.debug(f"VLESS parse error: {e}")
        return None

def parse_trojan_key(key: str) -> Optional[Dict]:
    try:
        parsed = urllib.parse.urlparse(key)
        q = urllib.parse.parse_qs(parsed.query)
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
                    "sni": q.get("sni", [hostname])[0],
                    "udp": True
                }]
            },
            "streamSettings": {}
        }

        security = q.get("security", ["tls"])[0]
        network = q.get("type", ["tcp"])[0]
        stream = {"network": network, "security": security}

        if network == "ws":
            ws = {"path": q.get("path", ["/"])[0]}
            if "host" in q:
                ws["headers"] = {"Host": q["host"][0]}
            stream["wsSettings"] = ws

        if security == "tls":
            stream["tlsSettings"] = {
                "serverName": q.get("sni", [hostname])[0],
                "fingerprint": q.get("fp", ["chrome"])[0],
                "allowInsecure": False
            }

        outbound["streamSettings"] = stream
        return outbound
    except Exception as e:
        logger.debug(f"Trojan parse error: {e}")
        return None

def parse_vmess_key(key: str) -> Optional[Dict]:
    try:
        encoded = key.replace("vmess://", "")
        missing = len(encoded) % 4
        if missing:
            encoded += "=" * (4 - missing)
        data = json.loads(base64.b64decode(encoded).decode("utf-8"))

        outbound = {
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": data.get("add", ""),
                    "port": data.get("port", 443),
                    "users": [{
                        "id": data.get("id", ""),
                        "security": data.get("scy", "auto"),
                        "alterId": data.get("aid", 0)
                    }]
                }]
            },
            "streamSettings": {}
        }

        network = data.get("net", "tcp")
        security = data.get("tls", "none")
        stream = {"network": network, "security": security if security != "none" else "none"}

        if network == "ws":
            ws = {"path": data.get("path", "/")}
            if data.get("host"):
                ws["headers"] = {"Host": data["host"]}
            stream["wsSettings"] = ws
        elif network == "grpc":
            stream["grpcSettings"] = {"serviceName": data.get("serviceName", ""), "multiMode": True}

        if security == "tls":
            stream["tlsSettings"] = {
                "serverName": data.get("sni", data.get("add", "")),
                "fingerprint": data.get("fp", "chrome"),
                "allowInsecure": False
            }

        outbound["streamSettings"] = stream
        return outbound
    except Exception as e:
        logger.debug(f"VMess parse error: {e}")
        return None

def parse_hysteria2_key(key: str) -> Optional[Dict]:
    """
    Hysteria2 URI: hysteria2://auth@host:port/?sni=...&obfs=salamander&obfs-password=...&insecure=1
    Also supports hy2:// and multi-port (host:1234,5000-6000)
    Happ supports hy2:// explicitly [citation:6][citation:12].
    """
    try:
        parsed = urllib.parse.urlparse(key)
        q = urllib.parse.parse_qs(parsed.query)

        host, port, port_range = parse_hysteria2_host_port(parsed)
        if not host:
            return None

        auth = parsed.username or ""
        password = parsed.password or ""
        auth_value = f"{auth}:{password}" if password else auth

        outbound = {
            "protocol": "hysteria2",
            "settings": {
                "servers": [{
                    "address": host,
                    "port": port,
                    "password": auth_value,
                }]
            },
            "streamSettings": {
                "network": "hysteria2",
                "security": "tls",
                "tlsSettings": {
                    "serverName": q.get("sni", [host])[0],
                    "allowInsecure": q.get("insecure", ["0"])[0] in ("1", "true")
                }
            }
        }

        server = outbound["settings"]["servers"][0]

        # obfs (salamander)
        if "obfs" in q:
            server["obfs"] = q["obfs"][0]
            if "obfs-password" in q:
                server["obfsPassword"] = q["obfs-password"][0]

        # multi-port
        if port_range:
            server["ports"] = port_range

        # bandwidth (optional)
        if "upmbps" in q:
            server["up"] = q["upmbps"][0]
        if "downmbps" in q:
            server["down"] = q["downmbps"][0]

        return outbound
    except Exception as e:
        logger.debug(f"Hysteria2 parse error: {e}")
        return None

def parse_key_to_outbound(key: str, index: int) -> Optional[Dict]:
    if key.startswith("vless://"):
        outbound = parse_vless_key(key)
    elif key.startswith("trojan://"):
        outbound = parse_trojan_key(key)
    elif key.startswith("vmess://"):
        outbound = parse_vmess_key(key)
    elif key.startswith(("hysteria2://", "hy2://")):
        outbound = parse_hysteria2_key(key)
    else:
        return None

    if outbound:
        outbound["tag"] = f"proxy-{index}"
    return outbound

def split_into_groups(keys: List[str], max_per_group: int, max_groups: int) -> List[List[str]]:
    groups = []
    for i in range(0, len(keys), max_per_group):
        if len(groups) >= max_groups:
            break
        groups.append(keys[i:i + max_per_group])
    return groups

def deduplicate_keys(keys: List[str]) -> List[str]:
    """Deduplicate by (hostname, port, protocol)."""
    if not ENABLE_DEDUP:
        return keys
    seen = set()
    result = []
    for key in keys:
        try:
            parsed = urllib.parse.urlparse(key)
            proto = key.split("://", 1)[0].lower()
            if proto in ("hysteria2", "hy2"):
                host, port, _ = parse_hysteria2_host_port(parsed)
            else:
                host = (parsed.hostname or "").lower()
                port = parsed.port
            sig = (host, port, proto)
            if sig not in seen:
                seen.add(sig)
                result.append(key)
        except Exception:
            result.append(key)
    return result

def fetch_url(url: str) -> List[Tuple[str, str]]:
    cached = load_from_cache(url)
    if cached is not None:
        return cached

    resp = fetch_with_retry(url)
    if not resp:
        return []

    valid = []
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        line = line.strip()
        if not line or line.startswith("#") or not is_valid_key(line):
            continue

        flag, country = detect_country(line)
        if not flag or not country:
            continue

        try:
            parsed = urllib.parse.urlparse(line)
            hostname = parsed.hostname or ""
            if is_bad_domain(hostname):
                continue

            if ENABLE_TCP_CHECK:
                proto = line.split("://", 1)[0].lower()
                if proto in ("hysteria2", "hy2"):
                    check_host, check_port, _ = parse_hysteria2_host_port(parsed)
                else:
                    check_host, check_port = hostname, parsed.port or 443
                if not tcp_check(check_host, check_port, TCP_CHECK_TIMEOUT):
                    logger.debug(f"TCP check failed: {check_host}:{check_port}")
                    continue
        except Exception:
            continue

        valid.append((country, line))

    save_to_cache(url, valid)
    return valid

def send_telegram(message: str, is_error: bool = False) -> None:
    if TG_DISABLED:
        return
    if is_error and not TG_NOTIFY_ON_ERROR:
        return
    if not is_error and not TG_NOTIFY_ON_SUCCESS:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            logger.info("Telegram notification sent")
        else:
            logger.error(f"Telegram error: {r.status_code}")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")

# ============================================================
#  MAIN
# ============================================================
def main():
    start = time.time()
    logger.info("🚀 VPN Parser v4 started")
    logger.info(f"📦 Keys/group: {MAX_KEYS_PER_GROUP}, Groups/country: {MAX_GROUPS_PER_COUNTRY}")
    logger.info(f"📦 Dedup: {'ON' if ENABLE_DEDUP else 'OFF'}")

    urls = load_sources(SOURCE_FILE)
    if not urls:
        logger.error("No sources")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        sys.exit(0)

    logger.info(f"📥 Sources: {len(urls)}")

    grouped: Dict[str, List[str]] = {}
    total = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_url, u): u for u in urls}
        for i, fut in enumerate(as_completed(futures), 1):
            url = futures[fut]
            try:
                results = fut.result()
                for country, key in results:
                    grouped.setdefault(country, []).append(key)
                    total += 1
                logger.info(f"  [{i}/{len(urls)}] ✅ {url[:50]}... → {len(results)} keys")
            except Exception as e:
                errors += 1
                logger.error(f"  [{i}/{len(urls)}] ❌ {url[:50]}... error: {e}")

    if ENABLE_DEDUP:
        logger.info("🔄 Deduplicating...")
        for country, keys in grouped.items():
            before = len(keys)
            grouped[country] = deduplicate_keys(keys)
            after = len(grouped[country])
            if before != after:
                logger.info(f"  {country}: removed {before - after} duplicates")

    logger.info(f"\n📊 Total keys: {total}")
    for country, keys in sorted(grouped.items(), key=lambda x: -len(x[1])):
        logger.info(f"  {country}: {len(keys)}")

    output = []
    for country, keys in grouped.items():
        flag = COUNTRY_TO_FLAG.get(country, "🌍")
        groups = split_into_groups(keys, MAX_KEYS_PER_GROUP, MAX_GROUPS_PER_COUNTRY)

        for gi, group in enumerate(groups, 1):
            outbounds = []
            for idx, key in enumerate(group, 1):
                ob = parse_key_to_outbound(key, idx)
                if ob:
                    outbounds.append(ob)
            if not outbounds:
                continue

            outbounds.extend(BASE_OUTBOUNDS_EXTRA)
            suffix = f" #{gi}" if len(groups) > 1 else ""

            output.append({
                "remarks": f"{flag} {country}{suffix} | @TourFromKirill",
                "dns": BASE_DNS,
                "routing": BASE_ROUTING,
                "inbounds": BASE_INBOUNDS,
                "outbounds": outbounds
            })

    total_servers = sum(len(p['outbounds']) - 2 for p in output)
    elapsed = time.time() - start

    logger.info(f"💾 Saving {len(output)} profiles to {OUTPUT_FILE}")
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            if COMPRESS_OUTPUT:
                json.dump(output, f, ensure_ascii=False, separators=(',', ':'))
            else:
                json.dump(output, f, ensure_ascii=False, indent=2)
        size = Path(OUTPUT_FILE).stat().st_size
        logger.info(f"✅ Saved ({size} bytes)")
    except Exception as e:
        logger.error(f"❌ Save failed: {e}")

    logger.info(f"\n✅ Profiles: {len(output)}, Servers: {total_servers}, Time: {elapsed:.2f}s")

    if not TG_DISABLED:
        status = "✅ OK" if errors == 0 else f"⚠️ Partial ({errors} errors)"
        msg = f"""<b>VPN Parser</b>
{status}

📊 Sources: {len(urls)}
📊 Servers: {total_servers}
📊 Countries: {len(grouped)}
📊 Profiles: {len(output)}
📊 Errors: {errors}

⏱️ {elapsed:.2f}s
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        send_telegram(msg, is_error=errors > 0)

    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Fatal: {e}")
        logger.error(traceback.format_exc())
        if not TG_DISABLED:
            send_telegram(f"<b>❌ FATAL</b>\n<code>{str(e)}</code>", is_error=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        sys.exit(1)
