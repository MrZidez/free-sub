#!/usr/bin/env python3
"""
VPN Parser & Country Grouper
Parses VPN links from sources, filters valid ones, groups by country.
Supports: VLESS, TROJAN, VMess, Hysteria2
Output: Sing-Box JSON format
"""

import sys
import os

# ============================================================
#  МАКСИМАЛЬНАЯ ОТЛАДКА В САМОМ НАЧАЛЕ
# ============================================================
print("=" * 60)
print("🚀 СТАРТ СКРИПТА")
print(f"🐍 Python: {sys.version}")
print(f"📁 Текущая директория: {os.getcwd()}")
print("=" * 60)

# Проверяем наличие файлов
print("📂 Проверка файлов в директории:")
for f in os.listdir('.'):
    print(f"  - {f}")

# Проверяем .env
print("=" * 60)
if os.path.exists('.env'):
    print("✅ Файл .env найден")
    with open('.env', 'r') as f:
        print("📄 Содержимое .env:")
        for line in f:
            if line.strip() and not line.startswith('#'):
                print(f"  {line.strip()}")
else:
    print("⚠️ Файл .env НЕ НАЙДЕН")

# ============================================================
#  ИМПОРТЫ
# ============================================================
print("=" * 60)
print("📦 Импорт модулей...")

try:
    import json
    print("✅ json")
except ImportError as e:
    print(f"❌ json: {e}")
    sys.exit(1)

try:
    import time
    print("✅ time")
except ImportError as e:
    print(f"❌ time: {e}")
    sys.exit(1)

try:
    import logging
    print("✅ logging")
except ImportError as e:
    print(f"❌ logging: {e}")
    sys.exit(1)

try:
    import urllib.parse
    print("✅ urllib.parse")
except ImportError as e:
    print(f"❌ urllib.parse: {e}")
    sys.exit(1)

try:
    import base64
    print("✅ base64")
except ImportError as e:
    print(f"❌ base64: {e}")
    sys.exit(1)

try:
    import subprocess
    print("✅ subprocess")
except ImportError as e:
    print(f"❌ subprocess: {e}")
    sys.exit(1)

try:
    import platform
    print("✅ platform")
except ImportError as e:
    print(f"❌ platform: {e}")
    sys.exit(1)

try:
    import hashlib
    print("✅ hashlib")
except ImportError as e:
    print(f"❌ hashlib: {e}")
    sys.exit(1)

try:
    import traceback
    print("✅ traceback")
except ImportError as e:
    print(f"❌ traceback: {e}")
    sys.exit(1)

try:
    from pathlib import Path
    print("✅ pathlib")
except ImportError as e:
    print(f"❌ pathlib: {e}")
    sys.exit(1)

try:
    from datetime import datetime
    print("✅ datetime")
except ImportError as e:
    print(f"❌ datetime: {e}")
    sys.exit(1)

try:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    print("✅ concurrent.futures")
except ImportError as e:
    print(f"❌ concurrent.futures: {e}")
    sys.exit(1)

try:
    from typing import List, Tuple, Optional, Dict, Any
    print("✅ typing")
except ImportError as e:
    print(f"❌ typing: {e}")
    sys.exit(1)

try:
    import requests
    print("✅ requests")
except ImportError as e:
    print(f"❌ requests: {e}")
    print("💡 Установите: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv")
except ImportError as e:
    print(f"❌ python-dotenv: {e}")
    print("💡 Установите: pip install python-dotenv")
    sys.exit(1)

print("=" * 60)
print("✅ ВСЕ ИМПОРТЫ УСПЕШНЫ")
print("=" * 60)

# ============================================================
#  ЗАГРУЗКА .ENV
# ============================================================
print("📂 Загрузка .env...")
try:
    load_dotenv()
    print("✅ .env загружен через load_dotenv()")
except Exception as e:
    print(f"⚠️ Ошибка load_dotenv(): {e}")
    # Пробуем загрузить вручную
    env_file = Path(".env")
    if env_file.exists():
        print(f"📂 Найден файл .env, загружаю вручную...")
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"')
        print("✅ .env загружен вручную")
    else:
        print("⚠️ Файл .env не найден")

print("=" * 60)

# ============================================================
#  КОНФИГУРАЦИЯ ИЗ .ENV
# ============================================================
def get_env(key: str, default: Any = None) -> Any:
    """Получает значение из .env с преобразованием типов"""
    value = os.getenv(key, default)
    if value is None:
        return default
    if isinstance(default, bool):
        return value.lower() in ("true", "1", "yes", "on")
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    return value

print("📋 Чтение конфигурации из .env...")
USER_AGENT = get_env("USER_AGENT", "happ")
PING_THRESHOLD_MS = get_env("PING_THRESHOLD_MS", 250)
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

ENABLE_PING_CHECK = get_env("ENABLE_PING_CHECK", False)
ENABLE_GEO_CHECK = get_env("ENABLE_GEO_CHECK", False)
ENABLE_DEDUP = get_env("ENABLE_DEDUP", True)
ENABLE_RATING = get_env("ENABLE_RATING", False)
ENABLE_LOGGING = get_env("ENABLE_LOGGING", True)
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
LOG_DIR = get_env("LOG_DIR", "logs")
COMPRESS_OUTPUT = get_env("COMPRESS_OUTPUT", False)
ADD_METADATA = get_env("ADD_METADATA", True)

TG_BOT_TOKEN = get_env("TG_BOT_TOKEN", "")
TG_CHAT_ID = get_env("TG_CHAT_ID", "")
TG_NOTIFY_ON_SUCCESS = get_env("TG_NOTIFY_ON_SUCCESS", True)
TG_NOTIFY_ON_ERROR = get_env("TG_NOTIFY_ON_ERROR", True)
TG_DISABLED = not TG_BOT_TOKEN or not TG_CHAT_ID

print(f"📋 SOURCE_FILE: {SOURCE_FILE}")
print(f"📋 OUTPUT_FILE: {OUTPUT_FILE}")
print("=" * 60)

# ============================================================
#  ИНИЦИАЛИЗАЦИЯ
# ============================================================
try:
    Path(CACHE_DIR).mkdir(exist_ok=True)
    Path(LOG_DIR).mkdir(exist_ok=True)
    print(f"✅ Папки созданы: {CACHE_DIR}, {LOG_DIR}")
except Exception as e:
    print(f"⚠️ Ошибка создания папок: {e}")

if ENABLE_LOGGING:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(Path(LOG_DIR) / "vpn-parser.log"),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(handlers=[logging.NullHandler()])

logger = logging.getLogger(__name__)
logger.info("🚀 VPN Parser v2 (Sing-Box) с отладкой")

# ============================================================
#  ПРОТОКОЛЫ И СТРАНЫ
# ============================================================
VALID_PROTOCOLS = {"vless://", "trojan://", "vmess://", "hysteria://"}
EXCLUDED_PROTOCOLS = {"hy2://", "ss://", "tuic://"}

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

# ============================================================
#  БАЗОВАЯ СТРУКТУРА SING-BOX
# ============================================================
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

# ============================================================
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def load_sources(filepath: str) -> List[str]:
    """Загружает список URL из файла."""
    if not Path(filepath).exists():
        logger.error(f"Файл {filepath} не найден!")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def get_cache_path(url: str) -> Path:
    """Возвращает путь к кэш-файлу для URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return Path(CACHE_DIR) / f"{url_hash}.cache"

def load_from_cache(url: str) -> Optional[List[Tuple[str, str]]]:
    """Загружает данные из кэша."""
    if not CACHE_ENABLED:
        return None
    cache_path = get_cache_path(url)
    if not cache_path.exists():
        return None
    if time.time() - cache_path.stat().st_mtime > CACHE_TTL:
        logger.debug(f"Кэш истёк для {url[:50]}...")
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Загружено из кэша: {url[:50]}... ({len(data)} ключей)")
        return data
    except Exception as e:
        logger.warning(f"Ошибка чтения кэша для {url[:50]}...: {e}")
        return None

def save_to_cache(url: str, data: List[Tuple[str, str]]) -> None:
    """Сохраняет данные в кэш."""
    if not CACHE_ENABLED:
        return
    try:
        cache_path = get_cache_path(url)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.debug(f"Сохранено в кэш: {url[:50]}... ({len(data)} ключей)")
    except Exception as e:
        logger.warning(f"Ошибка сохранения кэша для {url[:50]}...: {e}")

def fetch_with_retry(url: str, max_retries: int = 3, delay: int = 2) -> Optional[requests.Response]:
    """Загружает URL с повторными попытками."""
    if not RETRY_ENABLED:
        max_retries = 1
    headers = {"User-Agent": USER_AGENT} if USER_AGENT else {}
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=TIMEOUT, headers=headers)
            if resp.status_code == 200:
                return resp
            if attempt < max_retries - 1:
                wait = delay * (2 ** attempt)
                logger.warning(f"Попытка {attempt+1}/{max_retries} для {url[:50]}... статус {resp.status_code}, повтор через {wait}с")
                time.sleep(wait)
        except Exception as e:
            if attempt < max_retries - 1:
                wait = delay * (2 ** attempt)
                logger.warning(f"Попытка {attempt+1}/{max_retries} для {url[:50]}... ошибка: {e}, повтор через {wait}с")
                time.sleep(wait)
            else:
                logger.error(f"Ошибка загрузки {url[:50]}...: {e}")
    return None

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

def detect_country(key: str) -> Optional[Tuple[str, str]]:
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

def check_ping(hostname: str, threshold: int) -> bool:
    """Проверяет пинг до сервера."""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        cmd = ["ping", param, "1", "-W", str(threshold // 1000 + 1), hostname]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=threshold // 1000 + 2)
        return result.returncode == 0
    except Exception:
        return False

def get_geo_info(ip: str) -> Optional[Dict]:
    """Получает геолокацию по IP."""
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode,country", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                return data
    except Exception:
        pass
    return None

# ============================================================
#  ПАРСИНГ ПРОТОКОЛОВ
# ============================================================
def parse_vless_key(key: str) -> Optional[Dict]:
    """Парсит vless:// ключ в Sing-Box outbound"""
    try:
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

        stream = {"network": network, "security": security}

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
    except Exception as e:
        logger.debug(f"Ошибка парсинга VLESS: {e}")
        return None

def parse_trojan_key(key: str) -> Optional[Dict]:
    """Парсит trojan:// ключ в Sing-Box outbound"""
    try:
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

        stream = {"network": network, "security": security}

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
    except Exception as e:
        logger.debug(f"Ошибка парсинга TROJAN: {e}")
        return None

def parse_vmess_key(key: str) -> Optional[Dict]:
    """Парсит vmess:// ключ в Sing-Box outbound"""
    try:
        encoded = key.replace("vmess://", "")
        missing_padding = len(encoded) % 4
        if missing_padding:
            encoded += "=" * (4 - missing_padding)
        decoded = base64.b64decode(encoded).decode("utf-8")
        data = json.loads(decoded)

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
                ws["headers"] = {"Host": data.get("host")}
            stream["wsSettings"] = ws

        if network == "grpc":
            stream["grpcSettings"] = {
                "serviceName": data.get("serviceName", ""),
                "multiMode": True
            }

        if security == "tls":
            stream["tlsSettings"] = {
                "serverName": data.get("sni", data.get("add", "")),
                "fingerprint": data.get("fp", "chrome"),
                "allowInsecure": False
            }

        outbound["streamSettings"] = stream
        return outbound
    except Exception as e:
        logger.debug(f"Ошибка парсинга VMess: {e}")
        return None

def parse_hysteria_key(key: str) -> Optional[Dict]:
    """Парсит hysteria:// ключ в Sing-Box outbound"""
    try:
        parsed = urllib.parse.urlparse(key)
        query = urllib.parse.parse_qs(parsed.query)
        hostname = parsed.hostname or ""
        port = parsed.port or 443
        auth = parsed.username or ""

        outbound = {
            "protocol": "hysteria",
            "settings": {
                "servers": [{
                    "address": hostname,
                    "port": port,
                    "auth": auth,
                    "sni": query.get("sni", [hostname])[0],
                    "up_mbps": int(query.get("up_mbps", [10])[0]),
                    "down_mbps": int(query.get("down_mbps", [50])[0])
                }]
            },
            "streamSettings": {
                "network": "udp",
                "security": query.get("security", ["tls"])[0],
                "tlsSettings": {
                    "serverName": query.get("sni", [hostname])[0],
                    "allowInsecure": True
                }
            }
        }
        return outbound
    except Exception as e:
        logger.debug(f"Ошибка парсинга Hysteria: {e}")
        return None

def parse_key_to_outbound(key: str, index: int) -> Optional[Dict]:
    """Конвертирует ключ в Sing-Box outbound"""
    if key.startswith("vless://"):
        outbound = parse_vless_key(key)
    elif key.startswith("trojan://"):
        outbound = parse_trojan_key(key)
    elif key.startswith("vmess://"):
        outbound = parse_vmess_key(key)
    elif key.startswith("hysteria://"):
        outbound = parse_hysteria_key(key)
    else:
        return None

    if outbound:
        outbound["tag"] = f"proxy-{index}"
    return outbound

def split_into_groups(keys: List[str], max_per_group: int, max_groups: int) -> List[List[str]]:
    if not keys:
        return []
    groups = []
    for i in range(0, min(len(keys), max_groups * max_per_group), max_per_group):
        groups.append(keys[i:i + max_per_group])
        if len(groups) >= max_groups:
            break
    return groups

def deduplicate_keys(keys: List[str]) -> List[str]:
    """Удаляет дубликаты ключей по IP/домену."""
    if not ENABLE_DEDUP:
        return keys
    seen = set()
    result = []
    for key in keys:
        try:
            parsed = urllib.parse.urlparse(key)
            hostname = parsed.hostname or ""
            if hostname not in seen:
                seen.add(hostname)
                result.append(key)
        except Exception:
            result.append(key)
    return result

def fetch_url(url: str) -> List[Tuple[str, str]]:
    """Загружает и парсит один источник."""
    cached = load_from_cache(url)
    if cached is not None:
        return cached

    resp = fetch_with_retry(url, RETRY_COUNT, RETRY_DELAY)
    if not resp:
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

                if ENABLE_PING_CHECK:
                    if not check_ping(hostname, PING_THRESHOLD_MS):
                        logger.debug(f"Пинг не пройден: {hostname}")
                        continue

                if ENABLE_GEO_CHECK:
                    geo = get_geo_info(hostname)
                    if geo:
                        geo_country = geo.get("country", "")
                        if geo_country and country.lower() != geo_country.lower():
                            logger.debug(f"Гео не совпадает: {hostname} ({country} vs {geo_country})")
                            continue

        except Exception as e:
            logger.debug(f"Ошибка проверки ключа: {e}")
            continue

        valid_keys.append((country, line))

    save_to_cache(url, valid_keys)
    return valid_keys

def send_telegram_notification(message: str, is_error: bool = False) -> None:
    """Отправляет уведомление в Telegram."""
    if TG_DISABLED:
        return
    if is_error and not TG_NOTIFY_ON_ERROR:
        return
    if not is_error and not TG_NOTIFY_ON_SUCCESS:
        return
    try:
        import requests as req
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        req.post(url, json=payload, timeout=5)
        logger.info("Уведомление отправлено в Telegram")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления в Telegram: {e}")

# ============================================================
#  MAIN
# ============================================================
def main():
    logger.info("🚀 Запуск VPN Parser v2 (Sing-Box)")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📋 User-Agent: {USER_AGENT or 'не задан'}")
    logger.info(f"🎯 Порог пинга: {PING_THRESHOLD_MS} мс")
    logger.info(f"📦 Ключей в группе: {MAX_KEYS_PER_GROUP}")
    logger.info(f"🌍 Групп на страну: {MAX_GROUPS_PER_COUNTRY}")
    logger.info(f"📦 Кэширование: {'включено' if CACHE_ENABLED else 'выключено'}")
    logger.info(f"🔄 Retry: {'включен' if RETRY_ENABLED else 'выключен'}")
    logger.info(f"📊 Дедупликация: {'включена' if ENABLE_DEDUP else 'выключена'}")
    if ENABLE_PING_CHECK:
        logger.info(f"🏓 Проверка пинга: включена (порог {PING_THRESHOLD_MS} мс)")
    if ENABLE_GEO_CHECK:
        logger.info(f"🌍 Проверка геолокации: включена")
    if not TG_DISABLED:
        logger.info(f"📤 Telegram уведомления: включены")

    logger.info("📂 Проверяю файл source...")
    urls = load_sources(SOURCE_FILE)
    if not urls:
        logger.error("Нет источников для парсинга")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        sys.exit(0)

    logger.info(f"📥 Источников: {len(urls)}")
    logger.info(f"📄 Содержимое source: {urls}")

    grouped = {}
    total = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_url, url): url for url in urls}

        for i, future in enumerate(as_completed(futures), 1):
            url = futures[future]
            try:
                results = future.result()
                for country, key in results:
                    grouped.setdefault(country, []).append(key)
                    total += 1
                logger.info(f"  [{i}/{len(urls)}] ✅ {url[:50]}... → {len(results)} ключей")
            except Exception as e:
                errors += 1
                logger.error(f"  [{i}/{len(urls)}] ❌ {url[:50]}... ошибка: {e}")

    if ENABLE_DEDUP:
        logger.info("🔄 Дедупликация ключей...")
        for country, keys in grouped.items():
            before = len(keys)
            grouped[country] = deduplicate_keys(keys)
            after = len(grouped[country])
            if before != after:
                logger.info(f"  {country}: удалено {before - after} дублей")

    logger.info(f"\n📊 Всего ключей: {total}")
    logger.info("📊 По странам:")
    for country, keys in sorted(grouped.items(), key=lambda x: -len(x[1])):
        logger.info(f"  {country}: {len(keys)}")

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

            outbounds.extend(BASE_OUTBOUNDS_EXTRA)

            suffix = f" #{gi}" if len(groups) > 1 else ""

            profile = {
                "remarks": f"{flag} {country}{suffix} | @TourFromKirill",
                "dns": BASE_DNS,
                "routing": BASE_ROUTING,
                "inbounds": BASE_INBOUNDS,
                "outbounds": outbounds
            }
            output.append(profile)

    # Добавляем метаданные
    if ADD_METADATA:
        elapsed = time.time() - start_time
        total_profiles = len(output)
        total_servers = sum(len(p['outbounds']) - 2 for p in output)
        metadata = {
            "_metadata": {
                "generated": datetime.now().isoformat(),
                "total_servers": total_servers,
                "total_profiles": total_profiles,
                "total_countries": len(grouped),
                "sources": len(urls),
                "errors": errors,
                "elapsed_seconds": round(elapsed, 2)
            }
        }
        output.append(metadata)

    # ============================================================
    #  ПРИНУДИТЕЛЬНАЯ ЗАПИСЬ
    # ============================================================
    logger.info("🔍 ПРИНУДИТЕЛЬНАЯ ЗАПИСЬ ФАЙЛА")
    logger.info(f"📊 output содержит {len(output)} профилей")
    
    # Если output пустой — создаём тестовые данные
    if not output:
        logger.warning("⚠️ output ПУСТ! Создаю тестовые данные...")
        test_profile = {
            "remarks": "🇷🇺 Тест | @TourFromKirill",
            "dns": BASE_DNS,
            "routing": BASE_ROUTING,
            "inbounds": BASE_INBOUNDS,
            "outbounds": [
                {"protocol": "vless", "tag": "proxy-1", "settings": {}},
                {"tag": "direct", "protocol": "freedom"},
                {"tag": "block", "protocol": "blackhole"}
            ]
        }
        output.append(test_profile)
        logger.info("✅ Тестовый профиль добавлен")
    
    # Принудительно добавляем суффикс
    for p in output:
        if '@TourFromKirill' not in p['remarks']:
            p['remarks'] = p['remarks'] + ' | @TourFromKirill'
            logger.info(f"✏️ Добавлен суффикс: {p['remarks']}")
    
    # ============================================================
    #  СОХРАНЕНИЕ
    # ============================================================
    logger.info(f"💾 Сохраняю файл: {OUTPUT_FILE}")
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            if COMPRESS_OUTPUT:
                json.dump(output, f, ensure_ascii=False, separators=(',', ':'))
            else:
                json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Файл {OUTPUT_FILE} успешно сохранён")
        
        # Проверяем, что файл создался
        if Path(OUTPUT_FILE).exists():
            file_size = Path(OUTPUT_FILE).stat().st_size
            logger.info(f"📄 Размер файла: {file_size} байт")
        else:
            logger.error("❌ Файл НЕ создан!")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")

    elapsed = time.time() - start_time
    total_profiles = len(output) - (1 if ADD_METADATA else 0)
    total_servers = sum(len(p['outbounds']) - 2 for p in output if 'outbounds' in p)

    logger.info(f"\n✅ Сохранено {total_profiles} профилей в {OUTPUT_FILE}")
    logger.info(f"📊 Серверов: {total_servers}")
    logger.info(f"⏱️ Время выполнения: {elapsed:.2f}с")

    if not TG_DISABLED:
        status = "✅ УСПЕХ" if errors == 0 else f"⚠️ ЧАСТИЧНЫЙ УСПЕХ ({errors} ошибок)"
        message = f"""<b>VPN Parser</b>
{status}

📊 <b>Статистика:</b>
• Источников: {len(urls)}
• Серверов: {total_servers}
• Стран: {len(grouped)}
• Профилей: {total_profiles}
• Ошибок: {errors}

⏱️ Время: {elapsed:.2f}с
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        send_telegram_notification(message, is_error=errors > 0)

    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.error(traceback.format_exc())

        if not TG_DISABLED:
            message = f"""<b>❌ КРИТИЧЕСКАЯ ОШИБКА</b>
<code>{str(e)}</code>
<pre>{traceback.format_exc()[:500]}</pre>
"""
            send_telegram_notification(message, is_error=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        sys.exit(1)
