#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import copy
import functools
import hashlib
import html
import ipaddress
import json
import logging
import os
import re
import socket
import sys
import tempfile
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, unquote, urlsplit

import requests
from requests.adapters import HTTPAdapter

try:  # python-dotenv необязателен: в GitHub Actions переменные приходят из env
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

log = logging.getLogger("vpn_checker")


# ============================================================
#  КОНФИГУРАЦИЯ
# ============================================================
_TRUE = {"1", "true", "yes", "on"}


def _env(key: str, default: Any) -> Any:
    """Читает переменную окружения и приводит её к типу значения по умолчанию."""
    raw = os.getenv(key)
    if raw is None or not raw.strip():
        return default
    raw = raw.strip()
    try:
        if isinstance(default, bool):  # bool раньше int: bool — подкласс int
            return raw.lower() in _TRUE
        if isinstance(default, int):
            return int(raw)
        if isinstance(default, float):
            return float(raw)
    except ValueError:
        log.warning("Некорректное значение %s=%r, использую %r", key, raw, default)
        return default
    return raw


@dataclass(frozen=True)
class Config:
    # источники и вывод
    source_file: str = "source"
    output_file: str = "FREE-VPN-FROM-KIRILL.json"
    brand: str = "@TourFromKirill"
    min_profiles: int = 1  # меньше — файл НЕ перезаписывается
    # сеть
    user_agent: str = "happ"
    timeout: float = 15.0
    max_workers: int = 10
    max_response_mb: int = 20
    retry_enabled: bool = True
    retry_count: int = 3
    retry_delay: float = 2.0
    # кэш
    cache_enabled: bool = False
    cache_ttl: int = 3600
    cache_dir: str = "cache"
    # проверки
    enable_dedup: bool = True
    enable_ping_check: bool = True  # TCP-проверка доступности
    ping_threshold_ms: int = 250
    connect_timeout: float = 3.0
    check_workers: int = 50
    enable_geo_check: bool = False  # сверка страны по IP через ip-api.com
    geo_drop_mismatch: bool = False  # False — исправлять страну, True — выкидывать ключ
    keep_unknown_country: bool = False
    # группировка
    max_keys_per_group: int = 8
    max_groups_per_country: int = 5
    # вывод
    compress_output: bool = False
    add_metadata: bool = False
    # логи
    enable_logging: bool = True  # запись в файл (консоль работает всегда)
    log_level: str = "INFO"
    log_dir: str = "logs"
    # telegram
    tg_bot_token: str = ""
    tg_chat_id: str = ""
    tg_notify_on_success: bool = True
    tg_notify_on_error: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        d = cls()
        kw = {}
        for f in cls.__dataclass_fields__.values():
            kw[f.name] = _env(f.name.upper(), getattr(d, f.name))
        return cls(**kw)


# ============================================================
#  ЛОГИРОВАНИЕ (секреты маскируются)
# ============================================================
class _MaskingFormatter(logging.Formatter):
    def __init__(self, fmt: str, secrets: list[str]):
        super().__init__(fmt)
        self._secrets = [s for s in secrets if s]

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        for s in self._secrets:
            text = text.replace(s, "***")
        return text


def setup_logging(cfg: Config, verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else getattr(logging, cfg.log_level.upper(), logging.INFO)
    fmt = _MaskingFormatter("%(asctime)s %(levelname)-7s %(message)s",
                            [cfg.tg_bot_token, cfg.tg_chat_id])
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if cfg.enable_logging:
        try:
            Path(cfg.log_dir).mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(Path(cfg.log_dir) / "vpn-checker.log",
                                                encoding="utf-8"))
        except OSError as e:
            print(f"Не удалось открыть файл лога: {e}", file=sys.stderr)
    log.handlers.clear()
    for h in handlers:
        h.setFormatter(fmt)
        log.addHandler(h)
    log.setLevel(level)
    log.propagate = False


# ============================================================
#  СТРАНЫ
# ============================================================
COUNTRY_NAMES = {
    "RU": "Россия", "US": "США", "GB": "Великобритания", "DE": "Германия",
    "FR": "Франция", "NL": "Нидерланды", "CA": "Канада", "AU": "Австралия",
    "JP": "Япония", "CN": "Китай", "SG": "Сингапур", "KR": "Южная Корея",
    "BR": "Бразилия", "IN": "Индия", "IT": "Италия", "ES": "Испания",
    "CH": "Швейцария", "SE": "Швеция", "NO": "Норвегия", "FI": "Финляндия",
    "DK": "Дания", "PL": "Польша", "UA": "Украина", "KZ": "Казахстан",
    "LV": "Латвия", "EE": "Эстония", "LT": "Литва", "BY": "Беларусь",
    "TR": "Турция", "AE": "ОАЭ", "IL": "Израиль", "ZA": "ЮАР",
    "AR": "Аргентина", "MX": "Мексика",
    # добавлено
    "HK": "Гонконг", "TW": "Тайвань", "CZ": "Чехия", "AT": "Австрия",
    "BE": "Бельгия", "IE": "Ирландия", "PT": "Португалия", "GR": "Греция",
    "RO": "Румыния", "BG": "Болгария", "HU": "Венгрия", "MD": "Молдова",
    "GE": "Грузия", "AM": "Армения", "AZ": "Азербайджан", "UZ": "Узбекистан",
    "RS": "Сербия", "SK": "Словакия", "SI": "Словения", "HR": "Хорватия",
    "IS": "Исландия", "LU": "Люксембург", "CY": "Кипр", "TH": "Таиланд",
    "VN": "Вьетнам", "ID": "Индонезия", "MY": "Малайзия", "PH": "Филиппины",
    "CL": "Чили", "CO": "Колумбия", "EG": "Египет", "SA": "Саудовская Аравия",
}
_ISO_ALIASES = {"UK": "GB"}
UNKNOWN_COUNTRY = "??"

_FLAG_RE = re.compile("[\U0001F1E6-\U0001F1FF]{2}")
_CODE_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z]{2})(?![A-Za-z0-9])")


def iso_to_flag(code: str) -> str:
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in code.upper())


def flag_to_iso(flag: str) -> str:
    return "".join(chr(ord(c) - 0x1F1E6 + 65) for c in flag)


def country_label(iso: str) -> tuple[str, str]:
    if iso == UNKNOWN_COUNTRY:
        return "🌍", "Прочие"
    return iso_to_flag(iso), COUNTRY_NAMES.get(iso, iso)


def detect_country(remark: str, host: str) -> Optional[str]:
    """ISO-код страны по флагу/коду в названии ключа или по ccTLD хоста."""
    m = _FLAG_RE.search(remark)
    if m:
        return flag_to_iso(m.group())
    for m in _CODE_RE.finditer(remark):
        code = _ISO_ALIASES.get(m.group(1), m.group(1))
        if code in COUNTRY_NAMES:
            return code
    tld = host.rsplit(".", 1)[-1].upper()
    if len(tld) == 2 and tld.isalpha():
        tld = _ISO_ALIASES.get(tld, tld)
        if tld in COUNTRY_NAMES:
            return tld
    return None


# ============================================================
#  ФИЛЬТР ХОСТОВ
# ============================================================
BAD_TLDS = {"tk", "ml", "ga", "cf", "gq", "top", "xyz", "club"}
BAD_LABELS = {"mirror", "gist", "storage", "aws", "example", "test", "localhost"}
BAD_SUFFIXES = ("kdns.fr", "org.ua")
BAD_SUBSTRINGS = (
    "github", "yandexcloud", "cloudflare", "cloudfront", "amazon", "azure",
    "google", "heroku", "netlify", "vercel", "roc-taiwan", "taipeicitygovernment",
    "seoulcitygovernment", "seoulcityhall", "tokyometropolis", "duckdns",
    "no-ip", "dyndns", "ddns", "serveo", "ngrok",
)


def is_bad_host(host: str) -> bool:
    h = host.lower().rstrip(".")
    if not h:
        return True
    try:  # IP-адрес: отбрасываем приватные, loopback, зарезервированные и т.п.
        return not ipaddress.ip_address(h).is_global
    except ValueError:
        pass
    if "." not in h:
        return True
    labels = h.split(".")
    if labels[-1] in BAD_TLDS or any(lb in BAD_LABELS for lb in labels):
        return True
    if any(h == s or h.endswith("." + s) for s in BAD_SUFFIXES):
        return True
    return any(s in h for s in BAD_SUBSTRINGS)


# ============================================================
#  МОДЕЛЬ УЗЛА И ПАРСИНГ ССЫЛОК
# ============================================================
SUPPORTED_NETWORKS = {"tcp", "ws", "grpc", "httpupgrade", "xhttp", "http"}
SUPPORTED_SECURITY = {"none", "tls", "reality"}
_NET_ALIASES = {"raw": "tcp", "h2": "http", "splithttp": "xhttp", "gun": "grpc"}
_LINK_RE = re.compile(r"(?:vless|trojan|vmess)://[^\s\"'<>`]+", re.I)


@dataclass
class Node:
    protocol: str
    host: str
    port: int
    secret: str  # uuid (vless/vmess) или пароль (trojan)
    params: dict = field(default_factory=dict)
    remark: str = ""
    country: Optional[str] = None
    latency_ms: Optional[float] = None
    ip: Optional[str] = None

    @property
    def identity(self) -> tuple:
        p = self.params
        return (self.protocol, self.host, self.port, self.secret,
                p.get("type", ""), p.get("path") or p.get("serviceName", ""),
                p.get("security", ""))


def _s(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _b64decode(text: str) -> bytes:
    text = re.sub(r"\s+", "", text).replace("-", "+").replace("_", "/")
    text += "=" * (-len(text) % 4)
    return base64.b64decode(text)


def _parse_vmess(raw: str) -> Optional[Node]:
    try:
        payload = raw[len("vmess://"):].split("#", 1)[0]
        data = json.loads(_b64decode(payload).decode("utf-8"))
        port = int(data.get("port"))
    except (ValueError, TypeError, AttributeError):  # включая binascii.Error / JSONDecodeError
        return None
    if not isinstance(data, dict):
        return None
    net = _s(data.get("net")).lower() or "tcp"
    tls = _s(data.get("tls")).lower()
    params = {
        "type": net,
        "security": tls if tls in ("tls", "reality") else "none",
        "sni": _s(data.get("sni")),
        "host": _s(data.get("host")),
        "path": _s(data.get("path")),
        "fp": _s(data.get("fp")),
        "alpn": _s(data.get("alpn")),
        "scy": _s(data.get("scy")) or "auto",
        "aid": _s(data.get("aid")) or "0",
    }
    if net == "grpc":
        params["serviceName"] = params["path"]
    return Node("vmess", _s(data.get("add")).lower(), port, _s(data.get("id")),
                params, remark=_s(data.get("ps")))


def _parse_url_link(raw: str, protocol: str) -> Optional[Node]:
    try:
        u = urlsplit(raw)
        host, port = u.hostname or "", u.port
    except ValueError:
        return None
    if port is None:
        return None
    secret = unquote(u.username or "")
    if u.password:
        secret += ":" + unquote(u.password)
    params = {k: v[0] for k, v in parse_qs(u.query).items() if v}
    return Node(protocol, host, port, secret, params, remark=unquote(u.fragment))


def parse_link(raw: str) -> Optional[Node]:
    raw = raw.strip()
    scheme = raw.split("://", 1)[0].lower() if "://" in raw else ""
    if scheme == "vmess":
        node = _parse_vmess(raw)
    elif scheme in ("vless", "trojan"):
        node = _parse_url_link(raw, scheme)
    else:
        return None
    if node is None:
        return None
    p = node.params
    net = (p.get("type") or "tcp").lower()
    p["type"] = _NET_ALIASES.get(net, net)
    p["security"] = (p.get("security") or ("tls" if node.protocol == "trojan" else "none")).lower()
    return node


def reject_reason(node: Node) -> Optional[str]:
    """Причина отбраковки узла или None, если он годится."""
    p = node.params
    if not node.secret:
        return "нет id/пароля"
    if not 1 <= node.port <= 65535:
        return "неверный порт"
    if is_bad_host(node.host):
        return "плохой хост"
    if p["type"] not in SUPPORTED_NETWORKS:
        return "неподдерживаемый транспорт"
    if p["security"] not in SUPPORTED_SECURITY:
        return "неподдерживаемая защита"
    if p["security"] == "reality" and not p.get("pbk"):
        return "reality без public key"  # такой ключ ломает весь профиль в Xray
    return None


def dedupe(nodes: list[Node]) -> list[Node]:
    seen: set = set()
    out = []
    for n in nodes:
        if n.identity not in seen:
            seen.add(n.identity)
            out.append(n)
    return out


# ============================================================
#  XRAY-КОНФИГ
# ============================================================
BASE_DNS = {"servers": ["1.1.1.1", "1.0.0.1"], "queryStrategy": "UseIP"}

BASE_ROUTING = {
    "rules": [{"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"}],
    "domainMatcher": "hybrid",
    "domainStrategy": "IPIfNonMatch",
}

_SNIFFING = {"enabled": True, "routeOnly": False, "destOverride": ["http", "tls", "quic"]}
BASE_INBOUNDS = [
    {"tag": "socks", "port": 10808, "listen": "127.0.0.1", "protocol": "socks",
     "settings": {"udp": True, "auth": "noauth"}, "sniffing": _SNIFFING},
    {"tag": "http", "port": 10809, "listen": "127.0.0.1", "protocol": "http",
     "settings": {"allowTransparent": False}, "sniffing": _SNIFFING},
]

BASE_OUTBOUNDS_EXTRA = [
    {"tag": "direct", "protocol": "freedom"},
    {"tag": "block", "protocol": "blackhole"},
]


def build_stream(node: Node) -> dict:
    p = node.params
    net, sec = p["type"], p["security"]
    stream: dict = {"network": net, "security": sec}
    path = p.get("path") or "/"
    host = p.get("host", "")

    if net == "ws":
        ws = {"path": path}
        if host:
            ws["headers"] = {"Host": host}
        stream["wsSettings"] = ws
    elif net == "grpc":
        stream["grpcSettings"] = {"serviceName": p.get("serviceName", ""), "multiMode": True}
    elif net == "tcp":
        stream["tcpSettings"] = {"header": {"type": "none"}}
    elif net == "httpupgrade":
        s = {"path": path}
        if host:
            s["host"] = host
        stream["httpupgradeSettings"] = s
    elif net == "xhttp":
        s = {"path": path, "mode": p.get("mode") or "auto"}
        if host:
            s["host"] = host
        stream["xhttpSettings"] = s
    elif net == "http":
        s = {"path": path}
        if host:
            s["host"] = [h.strip() for h in host.split(",") if h.strip()]
        stream["httpSettings"] = s

    if sec == "tls":
        tls = {
            "serverName": p.get("sni") or host or node.host,
            "fingerprint": p.get("fp") or "chrome",
            "allowInsecure": False,
        }
        alpn = [a.strip() for a in p.get("alpn", "").split(",") if a.strip()]
        if alpn:
            tls["alpn"] = alpn
        stream["tlsSettings"] = tls
    elif sec == "reality":
        reality = {
            "serverName": p.get("sni") or node.host,
            "fingerprint": p.get("fp") or "chrome",
            "publicKey": p["pbk"],
        }
        if p.get("sid"):
            reality["shortId"] = p["sid"]
        if p.get("spx"):
            reality["spiderX"] = p["spx"]
        stream["realitySettings"] = reality
    return stream


def build_outbound(node: Node, tag: str) -> dict:
    p = node.params
    if node.protocol == "vless":
        settings = {"vnext": [{"address": node.host, "port": node.port, "users": [{
            "id": node.secret, "encryption": p.get("encryption") or "none",
            "flow": p.get("flow", ""), "level": 0}]}]}
    elif node.protocol == "trojan":
        settings = {"servers": [{"address": node.host, "port": node.port,
                                 "password": node.secret}]}
    else:  # vmess
        try:
            aid = int(p.get("aid") or 0)
        except ValueError:
            aid = 0
        settings = {"vnext": [{"address": node.host, "port": node.port, "users": [{
            "id": node.secret, "security": p.get("scy") or "auto",
            "alterId": aid, "level": 0}]}]}
    return {"protocol": node.protocol, "settings": settings,
            "streamSettings": build_stream(node), "tag": tag}


# ============================================================
#  ЗАГРУЗКА ИСТОЧНИКОВ
# ============================================================
def _short(url: str) -> str:
    """URL для логов: без query/fragment (там часто лежат токены подписок)."""
    u = urlsplit(url)
    return f"{u.netloc}{u.path}"[:70]


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_sources(filepath: str) -> list[str]:
    seen: dict[str, None] = {}
    with open(filepath, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                seen.setdefault(line)
    return list(seen)


def make_session(cfg: Config) -> requests.Session:
    s = requests.Session()
    adapter = HTTPAdapter(pool_connections=cfg.max_workers, pool_maxsize=cfg.max_workers)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    if cfg.user_agent:
        s.headers["User-Agent"] = cfg.user_agent
    return s


_RETRY_STATUS = {429, 500, 502, 503, 504}


def fetch_text(session: requests.Session, url: str, cfg: Config) -> Optional[str]:
    """GET с ретраями (только для сетевых ошибок, 429 и 5xx) и лимитом размера."""
    attempts = max(1, cfg.retry_count) if cfg.retry_enabled else 1
    limit = cfg.max_response_mb * 1024 * 1024
    for attempt in range(1, attempts + 1):
        retryable, err = True, ""
        try:
            with session.get(url, timeout=cfg.timeout, stream=True) as r:
                if r.status_code == 200:
                    buf = bytearray()
                    for chunk in r.iter_content(65536):
                        buf.extend(chunk)
                        if len(buf) > limit:
                            log.warning("%s: ответ больше %d МБ, пропускаю",
                                        _short(url), cfg.max_response_mb)
                            return None
                    return bytes(buf).decode("utf-8-sig", errors="replace")
                err = f"HTTP {r.status_code}"
                retryable = r.status_code in _RETRY_STATUS
        except requests.RequestException as e:
            err = type(e).__name__
        if not retryable or attempt == attempts:
            log.error("%s: не удалось загрузить (%s)", _short(url), err)
            return None
        wait = cfg.retry_delay * 2 ** (attempt - 1)
        log.warning("%s: попытка %d/%d (%s), повтор через %.0fс",
                    _short(url), attempt, attempts, err, wait)
        time.sleep(wait)
    return None


def _maybe_b64_text(text: str) -> Optional[str]:
    try:
        decoded = _b64decode(text).decode("utf-8")
    except ValueError:
        return None
    return decoded if "://" in decoded else None


def extract_links(text: str) -> list[str]:
    """Ссылки из текста; понимает и base64-подписки."""
    if not _LINK_RE.search(text):
        text = _maybe_b64_text(text) or text
    links: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            links.extend(_LINK_RE.findall(line))
    return links


def _cache_path(cfg: Config, url: str) -> Path:
    return Path(cfg.cache_dir) / (hashlib.sha256(url.encode()).hexdigest()[:32] + ".json")


def _cache_load(cfg: Config, url: str) -> Optional[list[str]]:
    p = _cache_path(cfg, url)
    try:
        if time.time() - p.stat().st_mtime > cfg.cache_ttl:
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else None
    except (OSError, ValueError):
        return None


def fetch_source(session: requests.Session, url: str, cfg: Config) -> Optional[list[str]]:
    """Сырые ссылки из источника; None — источник недоступен."""
    if cfg.cache_enabled:
        cached = _cache_load(cfg, url)
        if cached is not None:
            log.debug("%s: из кэша (%d)", _short(url), len(cached))
            return cached
    text = fetch_text(session, url, cfg)
    if text is None:
        return None
    links = extract_links(text)
    if cfg.cache_enabled:
        try:
            atomic_write_text(_cache_path(cfg, url), json.dumps(links))
        except OSError as e:
            log.warning("Кэш не записан: %s", e)
    return links


# ============================================================
#  ПРОВЕРКА ДОСТУПНОСТИ И ГЕО
# ============================================================
@functools.lru_cache(maxsize=None)
def resolve(host: str) -> Optional[str]:
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        return None
    v4 = [i[4][0] for i in infos if i[0] == socket.AF_INET]
    return (v4 or [i[4][0] for i in infos] or [None])[0]


def tcp_latency_ms(ip: str, port: int, timeout: float, attempts: int = 2) -> Optional[float]:
    best: Optional[float] = None
    for _ in range(attempts):
        t0 = time.perf_counter()
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                pass
        except OSError:
            continue
        dt = (time.perf_counter() - t0) * 1000
        best = dt if best is None else min(best, dt)
    return best


def check_nodes(nodes: list[Node], cfg: Config) -> tuple[list[Node], Counter]:
    """TCP-проверка: оставляет узлы, к которым удалось подключиться быстрее порога."""
    stats: Counter = Counter()

    def work(n: Node) -> tuple[Node, Optional[float]]:
        n.ip = resolve(n.host)
        return n, (tcp_latency_ms(n.ip, n.port, cfg.connect_timeout) if n.ip else None)

    alive: list[Node] = []
    with ThreadPoolExecutor(max_workers=cfg.check_workers) as ex:
        futures = [ex.submit(work, n) for n in nodes]
        for i, fut in enumerate(as_completed(futures), 1):
            n, lat = fut.result()
            if n.ip is None:
                stats["не резолвится"] += 1
            elif lat is None:
                stats["недоступен"] += 1
            elif lat > cfg.ping_threshold_ms:
                stats["медленный"] += 1
            else:
                n.latency_ms = round(lat, 1)
                alive.append(n)
            if i % 500 == 0:
                log.info("  проверено %d/%d", i, len(nodes))
    return alive, stats


_GEO_URL = "http://ip-api.com/batch?fields=status,countryCode"


def geo_countries(session: requests.Session, ips: list[str]) -> dict[str, str]:
    """ISO-страны по IP через ip-api.com (batch по 100, лимит ~15 запросов/мин)."""
    result: dict[str, str] = {}
    chunks = [ips[i:i + 100] for i in range(0, len(ips), 100)]
    for ci, chunk in enumerate(chunks):
        for _ in range(2):
            try:
                r = session.post(_GEO_URL, json=chunk, timeout=10)
                if r.status_code == 429:
                    ttl = r.headers.get("X-Ttl", "")
                    time.sleep(min(int(ttl) + 1 if ttl.isdigit() else 6, 60))
                    continue
                if r.ok:
                    for ip, item in zip(chunk, r.json()):
                        if isinstance(item, dict) and item.get("status") == "success":
                            result[ip] = item["countryCode"]
            except (requests.RequestException, ValueError) as e:
                log.warning("Geo-запрос не удался: %s", type(e).__name__)
            break
        if ci < len(chunks) - 1:
            time.sleep(4.5)
    return result


def apply_geo(session: requests.Session, nodes: list[Node], cfg: Config) -> list[Node]:
    for n in nodes:
        n.ip = n.ip or resolve(n.host)
    geo = geo_countries(session, sorted({n.ip for n in nodes if n.ip}))
    kept, fixed, dropped = [], 0, 0
    for n in nodes:
        real = geo.get(n.ip) if n.ip else None
        if real and n.country and n.country != real:
            if cfg.geo_drop_mismatch:
                dropped += 1
                continue
            fixed += 1
        if real:
            n.country = real
        kept.append(n)
    log.info("Geo: исправлено меток %d, отброшено %d", fixed, dropped)
    return kept


# ============================================================
#  СБОРКА ПРОФИЛЕЙ
# ============================================================
def split_into_groups(items: list, max_per_group: int, max_groups: int) -> list[list]:
    items = items[: max_per_group * max_groups]
    return [items[i:i + max_per_group] for i in range(0, len(items), max_per_group)]


def build_profiles(nodes: list[Node], cfg: Config) -> list[dict]:
    by_country: dict[str, list[Node]] = {}
    for n in nodes:
        by_country.setdefault(n.country or UNKNOWN_COUNTRY, []).append(n)

    profiles: list[dict] = []
    order = sorted(by_country.items(), key=lambda kv: (-len(kv[1]), country_label(kv[0])[1]))
    for iso, group_nodes in order:
        flag, name = country_label(iso)
        group_nodes.sort(key=lambda n: (n.latency_ms is None, n.latency_ms or 0.0, n.identity))
        groups = split_into_groups(group_nodes, cfg.max_keys_per_group, cfg.max_groups_per_country)
        for gi, group in enumerate(groups, 1):
            outbounds = []
            for n in group:
                try:
                    outbounds.append(build_outbound(n, f"proxy-{len(outbounds) + 1}"))
                except Exception as e:  # один кривой ключ не должен ронять всё
                    log.debug("Пропущен %s:%s — %s", n.host, n.port, e)
            if not outbounds:
                continue
            outbounds += copy.deepcopy(BASE_OUTBOUNDS_EXTRA)
            suffix = f" #{gi}" if len(groups) > 1 else ""
            brand = f" | {cfg.brand}" if cfg.brand else ""
            profiles.append({
                "remarks": f"{flag} {name}{suffix}{brand}",
                "dns": copy.deepcopy(BASE_DNS),
                "routing": copy.deepcopy(BASE_ROUTING),
                "inbounds": copy.deepcopy(BASE_INBOUNDS),
                "outbounds": outbounds,
            })
    return profiles


# ============================================================
#  TELEGRAM
# ============================================================
def notify(cfg: Config, text: str, *, is_error: bool) -> None:
    if not (cfg.tg_bot_token and cfg.tg_chat_id):
        return
    if (is_error and not cfg.tg_notify_on_error) or (not is_error and not cfg.tg_notify_on_success):
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{cfg.tg_bot_token}/sendMessage",
            json={"chat_id": cfg.tg_chat_id, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=10,
        )
        if not r.ok:
            log.warning("Telegram ответил HTTP %s", r.status_code)
    except requests.RequestException as e:
        log.warning("Не удалось отправить уведомление в Telegram: %s", type(e).__name__)


# ============================================================
#  ОСНОВНОЙ ПРОЦЕСС
# ============================================================
def run(cfg: Config, dry_run: bool = False) -> int:
    t0 = time.time()
    log.info("Старт: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        sources = load_sources(cfg.source_file)
    except OSError as e:
        return _fail(cfg, f"Не удалось прочитать {cfg.source_file}: {e}")
    if not sources:
        return _fail(cfg, f"В {cfg.source_file} нет источников")
    log.info("Источников: %d", len(sources))

    # 1. загрузка
    session = make_session(cfg)
    fetched: dict[str, Optional[list[str]]] = {}
    with ThreadPoolExecutor(max_workers=cfg.max_workers) as ex:
        futures = {ex.submit(fetch_source, session, u, cfg): u for u in sources}
        for i, fut in enumerate(as_completed(futures), 1):
            url = futures[fut]
            try:
                fetched[url] = fut.result()
            except Exception as e:
                log.error("%s: ошибка %s", _short(url), e)
                fetched[url] = None
            n = fetched[url]
            log.info("[%d/%d] %s → %s", i, len(sources), _short(url),
                     "ОШИБКА" if n is None else f"{len(n)} ссылок")
    src_errors = sum(1 for v in fetched.values() if v is None)
    raw_links = [link for u in sources for link in (fetched[u] or [])]

    # 2. разбор и фильтрация
    nodes: list[Node] = []
    rejects: Counter = Counter()
    for raw in raw_links:
        node = parse_link(raw)
        if node is None:
            rejects["не разобрана"] += 1
            continue
        reason = reject_reason(node)
        if reason:
            rejects[reason] += 1
            continue
        nodes.append(node)
    valid = len(nodes)
    if cfg.enable_dedup:
        nodes = dedupe(nodes)
    log.info("Ссылок: %d, валидных: %d, после дедупликации: %d", len(raw_links), valid, len(nodes))
    if rejects:
        log.info("Отбраковано: %s", ", ".join(f"{k}: {v}" for k, v in rejects.most_common()))

    for n in nodes:
        n.country = detect_country(n.remark, n.host)

    # 3. доступность
    if cfg.enable_ping_check and nodes:
        log.info("TCP-проверка %d серверов (порог %d мс)...", len(nodes), cfg.ping_threshold_ms)
        alive, stats = check_nodes(nodes, cfg)
        log.info("Живых: %d (%s)", len(alive),
                 ", ".join(f"{k}: {v}" for k, v in stats.most_common()) or "ок")
        if alive:
            nodes = alive
        else:
            log.warning("Ни один сервер не прошёл проверку — похоже, проблема в сети раннера; "
                        "оставляю список без проверки")

    # 4. гео
    if cfg.enable_geo_check and nodes:
        nodes = apply_geo(session, nodes, cfg)

    if not cfg.keep_unknown_country:
        nodes = [n for n in nodes if n.country]

    # 5. профили
    profiles = build_profiles(nodes, cfg)
    countries = len({n.country for n in nodes})
    servers = sum(len(p["outbounds"]) - len(BASE_OUTBOUNDS_EXTRA) for p in profiles)
    elapsed = time.time() - t0

    if len(profiles) < max(1, cfg.min_profiles):
        return _fail(cfg, f"Получилось профилей: {len(profiles)} (минимум {cfg.min_profiles}). "
                          f"Файл {cfg.output_file} НЕ перезаписан.")

    if cfg.add_metadata:
        profiles.append({"_metadata": {
            "generated": datetime.now().isoformat(timespec="seconds"),
            "total_servers": servers, "total_profiles": len(profiles),
            "total_countries": countries, "sources": len(sources),
            "errors": src_errors, "elapsed_seconds": round(elapsed, 2)}})

    if dry_run:
        log.info("dry-run: профилей %d, серверов %d — файл не записан", len(profiles), servers)
        return 0

    text = (json.dumps(profiles, ensure_ascii=False, separators=(",", ":"))
            if cfg.compress_output else json.dumps(profiles, ensure_ascii=False, indent=2))
    atomic_write_text(Path(cfg.output_file), text + "\n")
    log.info("Сохранено: %s (%d профилей, %d серверов, %d стран, %.1f с)",
             cfg.output_file, len(profiles) - (1 if cfg.add_metadata else 0),
             servers, countries, elapsed)

    status = "✅ УСПЕХ" if src_errors == 0 else f"⚠️ ЧАСТИЧНЫЙ УСПЕХ ({src_errors} источн. недоступно)"
    notify(cfg, (
        f"<b>VPN Checker</b>\n{status}\n\n"
        f"• Источников: {len(sources)}\n• Ссылок: {len(raw_links)}\n"
        f"• Серверов в выдаче: {servers}\n• Стран: {countries}\n"
        f"• Профилей: {len(profiles)}\n⏱ {elapsed:.1f} с"), is_error=src_errors > 0)
    return 0


def _fail(cfg: Config, message: str) -> int:
    log.error(message)
    notify(cfg, f"<b>❌ VPN Checker</b>\n{html.escape(message)}", is_error=True)
    return 1


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", help="файл со списком источников (SOURCE_FILE)")
    ap.add_argument("--output", help="выходной JSON (OUTPUT_FILE)")
    ap.add_argument("--no-check", action="store_true", help="не проверять доступность серверов")
    ap.add_argument("--dry-run", action="store_true", help="ничего не записывать")
    ap.add_argument("-v", "--verbose", action="store_true", help="подробный лог")
    return ap.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if load_dotenv:
        load_dotenv()
    cfg = Config.from_env()
    if args.source:
        cfg = replace(cfg, source_file=args.source)
    if args.output:
        cfg = replace(cfg, output_file=args.output)
    if args.no_check:
        cfg = replace(cfg, enable_ping_check=False)
    setup_logging(cfg, args.verbose)
    try:
        return run(cfg, dry_run=args.dry_run)
    except Exception as e:
        log.exception("Критическая ошибка")
        tb = html.escape(traceback.format_exc()[-800:])
        notify(cfg, f"<b>❌ КРИТИЧЕСКАЯ ОШИБКА</b>\n<code>{html.escape(str(e))}</code>\n<pre>{tb}</pre>",
               is_error=True)
        return 1  # существующий выходной файл остаётся нетронутым


if __name__ == "__main__":
    sys.exit(main())
