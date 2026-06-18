#!/usr/bin/env python3
import requests
import re
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

OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.txt"

BAD_DOMAINS = [
    'mirror',
    'github',
    'gist',
    'raw.githubusercontent',
    'yandexcloud',
    'storage',
    'gist.githubusercontent',
    'githubusercontent',
    
    'cloudflare',
    'amazon',
    'aws',
    'azure',
    'google',
    'googleapis',
    'cloudfront',
    'heroku',
    'netlify',
    'vercel',
    
    'example',
    'test',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    
    'roc-taiwan',
    'taipeicitygovernment',
    'seoulcitygovernment',
    'kdns.fr',
    'hllfly.kdns.fr',
    'org.ua', 
    
    'duckdns',
    'no-ip',
    'dyndns',
    'ddns',
    'serveo',
    'ngrok',
    'localtunnel',
    'zapto',
    'hopto',
    'sytes',
    'myvnc',
    'strangled',
    'jumpingcrab',
    'betainabox',
    'bonobo',
    'afraid',
    'freeddns',
    'mooo',
    'dynu',
    'duckdns.org',
    'dynv6',
    'freedns',
    'noip',
    'changeip',
    'dnsomatic',
    'easydns',
    'dyn.com',
    'dyn-o-saur',
    'dyndns.org',
    
    '.tk',
    '.ml',
    '.ga',
    '.cf',
    '.gq',
    '.top',
    '.xyz',
    '.club',
    '.work',
    '.click',
    '.space',
    '.online',
    '.site',
    '.website',
    '.tech',
    '.store',
    '.pro',
    '.live',
    '.fun',
    '.cloud',
    '.host',
    '.press',
    '.loan',
    '.men',
    '.win',
    '.bid',
    '.date',
    '.download',
    '.review',
    '.trade',
    '.webcam',
    '.party'
]

COUNTRIES = {
    '🇷🇺': 'Россия',
    '🇺🇸': 'США',
    '🇬🇧': 'Великобритания',
    '🇩🇪': 'Германия',
    '🇫🇷': 'Франция',
    '🇳🇱': 'Нидерланды',
    '🇨🇦': 'Канада',
    '🇦🇺': 'Австралия',
    '🇯🇵': 'Япония',
    '🇨🇳': 'Китай',
    '🇸🇬': 'Сингапур',
    '🇰🇷': 'Южная Корея',
    '🇧🇷': 'Бразилия',
    '🇮🇳': 'Индия',
    '🇮🇹': 'Италия',
    '🇪🇸': 'Испания',
    '🇨🇭': 'Швейцария',
    '🇸🇪': 'Швеция',
    '🇳🇴': 'Норвегия',
    '🇫🇮': 'Финляндия',
    '🇩🇰': 'Дания',
    '🇵🇱': 'Польша',
    '🇺🇦': 'Украина',
    '🇰🇿': 'Казахстан',
    '🇱🇻': 'Латвия',
    '🇪🇪': 'Эстония',
    '🇱🇹': 'Литва',
    '🇧🇾': 'Беларусь',
    '🇹🇷': 'Турция',
    '🇦🇪': 'ОАЭ',
    '🇮🇱': 'Израиль',
    '🇿🇦': 'ЮАР',
    '🇦🇷': 'Аргентина',
    '🇲🇽': 'Мексика'
}

COUNTRY_CODES = {
    'RU': '🇷🇺',
    'US': '🇺🇸',
    'GB': '🇬🇧',
    'DE': '🇩🇪',
    'FR': '🇫🇷',
    'NL': '🇳🇱',
    'CA': '🇨🇦',
    'AU': '🇦🇺',
    'JP': '🇯🇵',
    'CN': '🇨🇳',
    'SG': '🇸🇬',
    'KR': '🇰🇷',
    'BR': '🇧🇷',
    'IN': '🇮🇳',
    'IT': '🇮🇹',
    'ES': '🇪🇸',
    'CH': '🇨🇭',
    'SE': '🇸🇪',
    'NO': '🇳🇴',
    'FI': '🇫🇮',
    'DK': '🇩🇰',
    'PL': '🇵🇱',
    'UA': '🇺🇦',
    'KZ': '🇰🇿',
    'LV': '🇱🇻',
    'EE': '🇪🇪',
    'LT': '🇱🇹',
    'BY': '🇧🇾',
    'TR': '🇹🇷',
    'AE': '🇦🇪',
    'IL': '🇮🇱',
    'ZA': '🇿🇦',
    'AR': '🇦🇷',
    'MX': '🇲🇽'
}

def is_bad_domain(hostname):
    """Проверка, является ли домен плохим"""
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
    """Определение страны по ключу"""
    for flag in COUNTRIES.keys():
        if flag in key:
            return flag, COUNTRIES[flag]
    
    for code, flag in COUNTRY_CODES.items():
        if f'#{code}' in key or f'_{code}_' in key or f'-{code}-' in key:
            return flag, COUNTRIES.get(flag, code)
    
    try:
        if '://' in key:
            parsed = urllib.parse.urlparse(key)
            hostname = parsed.hostname or ''
            # Проверяем окончания доменов
            for code, flag in COUNTRY_CODES.items():
                if hostname.endswith(f'.{code.lower()}') or hostname.endswith(f'.{code.lower()}'):
                    return flag, COUNTRIES.get(flag, code)
    except:
        pass
    
    return None, None

def rename_key(key):
    """Переименование ключа с добавлением флага и страны"""
    try:
        if '://' in key:
            parsed = urllib.parse.urlparse(key)
            hostname = parsed.hostname or ''
            if is_bad_domain(hostname):
                return None  
    except:
        return None
    
    flag, country = detect_country(key)
    
    if flag is None or country is None:
        return None
    
    if '#' in key:
        base = key.split('#')[0]
        old_name = key.split('#')[1] if len(key.split('#')) > 1 else ''
    else:
        base = key
        old_name = ''
    
    new_name = f"{flag} {country} | VPN From Kirill"
    
    if old_name and old_name[-1].isdigit():
        new_name += f" #{old_name[-1]}"
    
    return f"{base}#{new_name}"

print("🚀 Запуск VPN парсера с переименованием...")
print("🗑️ Ключи без определения страны будут удалены")
print("🚫 Ключи с плохими доменами будут удалены")

all_keys = set()
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
                        all_keys.add(line)
            print(f"  ✓ [{i}/{len(URLS)}] Загружено")
        else:
            print(f"  ✗ [{i}/{len(URLS)}] Ошибка {response.status_code}")
    except Exception as e:
        print(f"  ✗ [{i}/{len(URLS)}] Ошибка: {str(e)[:30]}")

print(f"📊 Найдено {len(all_keys)} уникальных ключей")

renamed_keys = []
deleted_count = 0
bad_domain_count = 0

for key in all_keys:
    try:
        renamed = rename_key(key)
        if renamed is not None:
            renamed_keys.append(renamed)
        else:
            if '://' in key:
                try:
                    parsed = urllib.parse.urlparse(key)
                    hostname = parsed.hostname or ''
                    if is_bad_domain(hostname):
                        bad_domain_count += 1
                    else:
                        deleted_count += 1
                except:
                    deleted_count += 1
            else:
                deleted_count += 1
    except:
        deleted_count += 1

print(f"✏️ Переименовано {len(renamed_keys)} ключей")
print(f"🗑️ Удалено {deleted_count} ключей (без определения страны)")
print(f"🚫 Удалено {bad_domain_count} ключей (плохой домен)")

print("💾 Сохраняю в файл...")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("#profile-title: Free Vpn From KIrill\n")
    f.write("#announce: Бесплатная подписка\n")
    f.write("#profile-update-interval: 12\n")
    f.write("#profile-web-page-url: https://t.me/TourFromKirill\n")
    f.write("\n")
    
    f.write(f"# Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    f.write(f"# Всего ключей: {len(renamed_keys)}\n")
    f.write("#" + "="*50 + "\n\n")
    
    if renamed_keys:
        for key in sorted(renamed_keys):
            f.write(key + '\n')
        print(f"✅ Сохранено {len(renamed_keys)} ключей")
    else:
        f.write("# Ключи не найдены\n")
        print("⚠️ Ключи не найдены")

print("✅ Готово!")
print(f"📁 Файл: {OUTPUT_FILE}")
print(f"📊 Итог: {len(renamed_keys)} ключей сохранено, {deleted_count + bad_domain_count} удалено")
