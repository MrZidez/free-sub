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

OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.json"
PING_THRESHOLD = 70
MAX_WORKERS = 30
TIMEOUT = 5

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

def convert_key_to_config(key, country, index):
    """Конвертирует ключ в JSON-конфиг для Sing-Box"""
    try:
        parsed = urllib.parse.urlparse(key)
        protocol = parsed.scheme
        hostname = parsed.hostname or ''
        port = parsed.port or 443
        query = urllib.parse.parse_qs(parsed.query)
        
        config = {
            "protocol": protocol,
            "settings": {},
            "streamSettings": {},
            "tag": f"proxy-{country}-{index}"
        }
        
        # Настраиваем в зависимости от протокола
        if protocol == 'vless':
            user_id = parsed.username or ''
            config["settings"] = {
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
            
            security = query.get('security', ['none'])[0]
            network = query.get('type', ['tcp'])[0]
            
            stream_settings = {
                "network": network,
                "security": security
            }
            
            if network == 'ws':
                ws_settings = {
                    "path": query.get('path', ['/'])[0],
                }
                if 'host' in query:
                    ws_settings["headers"] = {"Host": query['host'][0]}
                stream_settings["wsSettings"] = ws_settings
            
            if security == 'tls':
                stream_settings["tlsSettings"] = {
                    "serverName": query.get('sni', [hostname])[0],
                    "fingerprint": query.get('fp', ['chrome'])[0],
                    "allowInsecure": False
                }
            
            if security == 'reality':
                stream_settings["realitySettings"] = {
                    "serverName": query.get('sni', [hostname])[0],
                    "publicKey": query.get('pbk', [''])[0],
                    "fingerprint": query.get('fp', ['chrome'])[0],
                    "show": False
                }
            
            if network == 'grpc':
                stream_settings["grpcSettings"] = {
                    "serviceName": query.get('serviceName', [''])[0],
                    "multiMode": True
                }
            
            if network == 'tcp':
                stream_settings["tcpSettings"] = {
                    "header": {"type": "none"}
                }
            
            config["streamSettings"] = stream_settings
            
        elif protocol == 'trojan':
            password = parsed.username or ''
            config["settings"] = {
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
        return None

print("🚀 Запуск VPN парсера (группировка по странам)...")

# Собираем ключи по странам
country_keys = {}
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
                        flag, country = detect_country(line)
                        if flag and country:
                            try:
                                if '://' in line:
                                    parsed = urllib.parse.urlparse(line)
                                    hostname = parsed.hostname or ''
                                    if not is_bad_domain(hostname):
                                        if country not in country_keys:
                                            country_keys[country] = []
                                        country_keys[country].append(line)
                            except:
                                pass
            print(f"  ✓ [{i}/{len(URLS)}] Загружено")
        else:
            print(f"  ✗ [{i}/{len(URLS)}] Ошибка {response.status_code}")
    except Exception as e:
        print(f"  ✗ [{i}/{len(URLS)}] Ошибка: {str(e)[:30]}")

print(f"\n📊 Найдено ключей по странам:")
for country, keys in country_keys.items():
    print(f"  🌍 {country}: {len(keys)} ключей")

# Создаем JSON с группировкой по странам
json_output = []

for country, keys in country_keys.items():
    print(f"\n🔄 Создаю профиль для {country} ({len(keys)} ключей)...")
    
    # Создаем один профиль для страны
    profile = {
        "remarks": f"{country} | VPN From Kirill",
        "outbounds": []
    }
    
    # Добавляем все ключи этой страны в outbounds
    for idx, key in enumerate(keys, 1):
        config = convert_key_to_config(key, country, idx)
        if config:
            profile["outbounds"].append(config)
    
    if profile["outbounds"]:
        json_output.append(profile)
        print(f"  ✅ Добавлено {len(profile['outbounds'])} серверов")

print(f"\n✅ Создано {len(json_output)} профилей стран")

# Сохраняем в JSON
print("💾 Сохраняю в JSON...")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2)

print(f"✅ Сохранено в {OUTPUT_FILE}")

# Показываем статистику
total_servers = sum(len(p['outbounds']) for p in json_output)
print(f"\n📊 Итоговая статистика:")
print(f"  🌍 Стран: {len(json_output)}")
print(f"  🔗 Всего серверов: {total_servers}")
