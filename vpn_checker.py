#!/usr/bin/env python3
import requests
import re
import json
from datetime import datetime
import urllib.parse

# Список URL для парсинга
URLS = [
    "https://gitlab.com/zieng2/wl/raw/main/vless_universal.txt",
    "https://storage.yandexcloud.net/mystorage123/whitelist.txt",
    "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/e310946a53d9cd7910bb4381e7fceab83e1f8462/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
    "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/0f61abfd23bfc411b14385a95cfdb90498514a45/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/cinev505/VlessTrogan-vpn-key/refs/heads/main/WhiteList-VPN-Vless",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/splitted/trojan.txt",
    "https://hub.mos.ru/zieng2/wl/raw/main/list_universal.txt",
    "https://raw.githubusercontent.com/likzil/vless1/main/Treetcpvpn",
    "https://raw.githubusercontent.com/Ilyacom4ik/free-v2ray-2026/main/subscriptions/FreeCFGHub1.txt",
    "https://gist.githubusercontent.com/j80547013-max/1ed9f2d72fd7613eda3c4a36c96955cb/raw/bfd36277ccf212a8ed2800708a749efbcd5a0885/gistfile1.txt",

]

OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.json"  # Теперь JSON
PING_THRESHOLD = 70
MAX_WORKERS = 30
TIMEOUT = 5

# Метаданные для JSON
PROFILE_TITLE = "Free Vpn From KIrill"
PROFILE_ANNOUNCE = "Бесплатная подписка"
PROFILE_UPDATE_INTERVAL = 12
PROFILE_WEB_PAGE_URL = "https://t.me/TourFromKirill"

# Список плохих доменов
BAD_DOMAINS = [
    'mirror', 'github', 'gist', 'raw.githubusercontent', 'yandexcloud', 'storage',
    'gist.githubusercontent', 'githubusercontent', 'cloudflare', 'amazon', 'aws', 
    'azure', 'google', 'googleapis', 'cloudfront', 'heroku', 'netlify', 'vercel',
    'example', 'test', 'localhost', '127.0.0.1', '0.0.0.0',
    'roc-taiwan', 'taipeicitygovernment', 'seoulcitygovernment', 'seoulcityhall',
    'kdns.fr', 'hllfly.kdns.fr', 'org.ua', 'tokyometropolis',
    'chernigov.ua', 'ivano-frankivsk', 'kharkov.ua', 'kherson.ua',
    'kiev.ua', 'kyiv.ua', 'odesa.ua', 'odessa.ua',
    'chernivtsi', 'dnipro', 'donetsk', 'lviv', 'mariupol',
    'mykolaiv', 'rivne', 'sumy', 'ternopil', 'uzhhorod',
    'vinnitsa', 'zaporizhzhia', 'zhytomyr',
    'duckdns', 'no-ip', 'dyndns', 'ddns', 'serveo', 'ngrok', 'localtunnel',
    'zapto', 'hopto', 'sytes', 'myvnc', 'strangled', 'jumpingcrab',
    'betainabox', 'bonobo', 'afraid', 'freeddns', 'mooo', 'dynu',
    'duckdns.org', 'dynv6', 'freedns', 'noip', 'changeip',
    'dnsomatic', 'easydns', 'dyn.com', 'dyn-o-saur', 'dyndns.org',
    '.tk', '.ml', '.ga', '.cf', '.gq', '.top', '.xyz', '.club',
    '.work', '.click', '.space', '.online', '.site', '.website',
    '.tech', '.store', '.pro', '.live', '.fun', '.cloud', '.host',
    '.press', '.loan', '.men', '.win', '.bid', '.date', '.download',
    '.review', '.trade', '.webcam', '.party', '.gdn', '.science',
    '.faith', '.accountant', '.stream', '.ovh'
]

# Словарь стран и флагов
COUNTRIES = {
    '🇷🇺': 'Россия', '🇺🇸': 'США', '🇬🇧': 'Великобритания',
    '🇩🇪': 'Германия', '🇫🇷': 'Франция', '🇳🇱': 'Нидерланды',
    '🇨🇦': 'Канада', '🇦🇺': 'Австралия', '🇯🇵': 'Япония',
    '🇨🇳': 'Китай', '🇸🇬': 'Сингапур', '🇰🇷': 'Южная Корея',
    '🇧🇷': 'Бразилия', '🇮🇳': 'Индия', '🇮🇹': 'Италия',
    '🇪🇸': 'Испания', '🇨🇭': 'Швейцария', '🇸🇪': 'Швеция',
    '🇳🇴': 'Норвегия', '🇫🇮': 'Финляндия', '🇩🇰': 'Дания',
    '🇵🇱': 'Польша', '🇺🇦': 'Украина', '🇰🇿': 'Казахстан',
    '🇱🇻': 'Латвия', '🇪🇪': 'Эстония', '🇱🇹': 'Литва',
    '🇧🇾': 'Беларусь', '🇹🇷': 'Турция', '🇦🇪': 'ОАЭ',
    '🇮🇱': 'Израиль', '🇿🇦': 'ЮАР', '🇦🇷': 'Аргентина',
    '🇲🇽': 'Мексика'
}

# Сокращения стран
COUNTRY_CODES = {
    'RU': '🇷🇺', 'US': '🇺🇸', 'GB': '🇬🇧', 'DE': '🇩🇪',
    'FR': '🇫🇷', 'NL': '🇳🇱', 'CA': '🇨🇦', 'AU': '🇦🇺',
    'JP': '🇯🇵', 'CN': '🇨🇳', 'SG': '🇸🇬', 'KR': '🇰🇷',
    'BR': '🇧🇷', 'IN': '🇮🇳', 'IT': '🇮🇹', 'ES': '🇪🇸',
    'CH': '🇨🇭', 'SE': '🇸🇪', 'NO': '🇳🇴', 'FI': '🇫🇮',
    'DK': '🇩🇰', 'PL': '🇵🇱', 'UA': '🇺🇦', 'KZ': '🇰🇿',
    'LV': '🇱🇻', 'EE': '🇪🇪', 'LT': '🇱🇹', 'BY': '🇧🇾',
    'TR': '🇹🇷', 'AE': '🇦🇪', 'IL': '🇮🇱', 'ZA': '🇿🇦',
    'AR': '🇦🇷', 'MX': '🇲🇽'
}

def is_bad_domain(hostname):
    if not hostname:
        return True
    hostname_lower = hostname.lower()
    for bad in BAD_DOMAINS:
        if bad in hostname_lower:
            return True
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ip_pattern, hostname):
        parts = hostname.split('.')
        if parts[0] in ['10', '127', '192', '172', '169']:
            return True
        if parts[0] == '192' and parts[1] == '168':
            return True
        if parts[0] == '172' and 16 <= int(parts[1]) <= 31:
            return True
        if hostname.startswith('127.') or hostname.startswith('0.'):
            return True
    return False

def detect_country(key):
    # Ищем флаг
    for flag in COUNTRIES.keys():
        if flag in key:
            return flag, COUNTRIES[flag]
    # Ищем код страны
    for code, flag in COUNTRY_CODES.items():
        if f'#{code}' in key or f'_{code}_' in key or f'-{code}-' in key:
            return flag, COUNTRIES.get(flag, code)
    # Ищем в домене
    try:
        if '://' in key:
            parsed = urllib.parse.urlparse(key)
            hostname = parsed.hostname or ''
            for code, flag in COUNTRY_CODES.items():
                if hostname.endswith(f'.{code.lower()}'):
                    return flag, COUNTRIES.get(flag, code)
    except:
        pass
    return None, None

def convert_to_json_config(key, country):
    """Конвертирует ключ в JSON-конфиг для Sing-Box"""
    try:
        # Парсим URL
        parsed = urllib.parse.urlparse(key)
        protocol = parsed.scheme
        hostname = parsed.hostname or ''
        port = parsed.port or 443
        path = parsed.path or ''
        query = urllib.parse.parse_qs(parsed.query)
        
        # Базовая структура
        config = {
            "dns": {
                "servers": ["77.88.8.8", "77.88.8.1"],
                "queryStrategy": "UseIP",
                "cacheSize": 512,
                "readTimeout": "50ms",
                "writeTimeout": "50ms"
            },
            "inbounds": [
                {
                    "listen": "127.0.0.1",
                    "port": 10808,
                    "protocol": "socks",
                    "settings": {"udp": True},
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls"], "routeOnly": True},
                    "tag": "socks"
                },
                {
                    "listen": "127.0.0.1",
                    "port": 10809,
                    "protocol": "http",
                    "settings": {},
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls"], "routeOnly": True},
                    "tag": "http"
                }
            ],
            "log": {"loglevel": "none"},
            "outbounds": [
                {
                    "protocol": protocol,
                    "settings": {},
                    "streamSettings": {},
                    "tag": "proxy"
                }
            ],
            "policy": {
                "levels": {
                    "8": {
                        "connIdle": 60,
                        "downlinkOnly": 0,
                        "handshake": 1,
                        "uplinkOnly": 0,
                        "bufferSize": 16
                    }
                }
            },
            "remarks": country,
            "routing": {
                "domainStrategy": "AsIs",
                "rules": [
                    {"ip": ["geoip:private"], "outboundTag": "direct"},
                    {"network": "tcp,udp", "outboundTag": "proxy"}
                ]
            }
        }
        
        # Настраиваем в зависимости от протокола
        if protocol == 'vless':
            user_id = parsed.username or ''
            config["outbounds"][0]["settings"] = {
                "vnext": [{
                    "address": hostname,
                    "port": port,
                    "users": [{
                        "id": user_id,
                        "encryption": query.get('encryption', ['none'])[0],
                        "flow": query.get('flow', [''])[0]
                    }]
                }]
            }
            
            # Настройка streamSettings
            security = query.get('security', ['none'])[0]
            network = query.get('type', ['tcp'])[0]
            
            stream_settings = {
                "network": network,
                "security": security,
                "sockopt": {
                    "tcpNoDelay": True,
                    "tcpKeepAliveIdle": 5,
                    "tcpKeepAliveInterval": 2,
                    "tcpKeepAliveProbes": 2,
                    "mark": 255,
                    "domainStrategy": "UseIP"
                }
            }
            
            if network == 'ws':
                ws_settings = {
                    "path": query.get('path', ['/'])[0],
                }
                if 'host' in query:
                    ws_settings["headers"] = {"Host": query['host'][0]}
                stream_settings["wsSettings"] = ws_settings
            
            if security == 'tls':
                tls_settings = {
                    "serverName": query.get('sni', [hostname])[0],
                    "fingerprint": query.get('fp', ['chrome'])[0],
                    "allowInsecure": False
                }
                if 'alpn' in query:
                    tls_settings["alpn"] = query['alpn'][0].split(',')
                stream_settings["tlsSettings"] = tls_settings
            
            if security == 'reality':
                reality_settings = {
                    "serverName": query.get('sni', [hostname])[0],
                    "publicKey": query.get('pbk', [''])[0],
                    "fingerprint": query.get('fp', ['chrome'])[0],
                    "show": False
                }
                if 'sid' in query:
                    reality_settings["shortId"] = query['sid'][0]
                stream_settings["realitySettings"] = reality_settings
            
            if network == 'grpc':
                grpc_settings = {
                    "serviceName": query.get('serviceName', [''])[0],
                    "multiMode": True
                }
                stream_settings["grpcSettings"] = grpc_settings
            
            if network == 'tcp':
                stream_settings["tcpSettings"] = {
                    "header": {"type": "none"}
                }
            
            config["outbounds"][0]["streamSettings"] = stream_settings
            
        elif protocol == 'trojan':
            password = parsed.username or ''
            config["outbounds"][0]["settings"] = {
                "servers": [{
                    "address": hostname,
                    "port": port,
                    "password": password,
                    "sni": query.get('sni', [hostname])[0],
                    "udp": True
                }]
            }
        
        return config
        
    except Exception as e:
        print(f"  ⚠️ Ошибка конвертации ключа: {e}")
        return None

print("🚀 Запуск VPN парсера с JSON-конвертацией...")

# Собираем все ключи
all_keys = {}
print(f"📥 Загружаю {len(URLS)} источников...")

for i, url in enumerate(URLS, 1):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            lines = response.text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if any(p in line for p in ['vless://', 'trojan://', 'vmess://', 'ss://', 'h2://']):
                        # Определяем страну
                        flag, country = detect_country(line)
                        if flag and country:
                            # Проверяем домен
                            try:
                                if '://' in line:
                                    parsed = urllib.parse.urlparse(line)
                                    hostname = parsed.hostname or ''
                                    if not is_bad_domain(hostname):
                                        if country not in all_keys:
                                            all_keys[country] = []
                                        all_keys[country].append(line)
                            except:
                                pass
            print(f"  ✓ [{i}/{len(URLS)}] Загружено")
        else:
            print(f"  ✗ [{i}/{len(URLS)}] Ошибка {response.status_code}")
    except Exception as e:
        print(f"  ✗ [{i}/{len(URLS)}] Ошибка: {str(e)[:30]}")

print(f"📊 Найдено ключей по странам:")
for country, keys in all_keys.items():
    print(f"  🌍 {country}: {len(keys)} ключей")

# Конвертируем в JSON
json_profiles = []
total_keys = 0

for country, keys in all_keys.items():
    print(f"🔄 Конвертирую {len(keys)} ключей для {country}...")
    for key in keys:
        config = convert_to_json_config(key, f"{country} | VPN From Kirill")
        if config:
            json_profiles.append(config)
            total_keys += 1

print(f"✅ Сконвертировано {total_keys} ключей")

# Сохраняем в JSON
print("💾 Сохраняю в JSON...")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(json_profiles, f, ensure_ascii=False, indent=2)

print(f"✅ Сохранено {len(json_profiles)} профилей в {OUTPUT_FILE}")
print(f"📁 Файл: {OUTPUT_FILE}")
