#!/usr/bin/env python3
import requests
import re
import json
import sys
import urllib.parse
from datetime import datetime

print("🚀 Запуск VPN парсера...")

try:
    # НОВЫЙ СПИСОК URL ДЛЯ ПАРСИНГА
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
        "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/26.txt",
        "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/27.txt",
        "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/28.txt",
        "https://github.com/AvenCores/goida-vpn-configs/raw/refs/heads/main/githubmirror/26.txt",
        "https://gist.githubusercontent.com/j80547013-max/e1fb675de8bbdc2225f98b5c2302b52b/raw/0820188e0baae9923ed86f6dee0625a33c4555a4/gistfile1.txt",
        "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/d2c8359ceba149c1129c2c57d43c84e85e8baff3/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
        "https://raw.githubusercontent.com/po5p/DLDBL/refs/heads/main/lutvpn.txt",
        "https://raw.githubusercontent.com/likzil/vless1/main/Treetcpvpn",
        "https://raw.githubusercontent.com/Ilyacom4ik/free-v2ray-2026/main/subscriptions/FreeCFGHub1.txt",
        "https://gist.githubusercontent.com/j80547013-max/1ed9f2d72fd7613eda3c4a36c96955cb/raw/bfd36277ccf212a8ed2800708a749efbcd5a0885/gistfile1.txt"
    ]

    OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.json"

    # Словарь стран с флагами
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

    def detect_country(key):
        try:
            # Ищем флаг в ключе
            for flag in COUNTRIES.keys():
                if flag in key:
                    return flag, COUNTRIES[flag]
            # Ищем код страны
            for code, flag in COUNTRY_CODES.items():
                if f'#{code}' in key or f'_{code}_' in key or f'-{code}-' in key:
                    return flag, COUNTRIES.get(flag, code)
            # Ищем в домене
            if '://' in key:
                parsed = urllib.parse.urlparse(key)
                hostname = parsed.hostname or ''
                for code, flag in COUNTRY_CODES.items():
                    if hostname.endswith(f'.{code.lower()}'):
                        return flag, COUNTRIES.get(flag, code)
        except:
            pass
        return None, None

    def extract_country_from_key(key):
        """Извлекает название страны из ключа"""
        flag, country = detect_country(key)
        if flag and country:
            return country
        return None

    print(f"📥 Загружаю {len(URLS)} источников...")

    # Собираем ключи по странам
    country_keys = {}

    for i, url in enumerate(URLS, 1):
        try:
            print(f"  [{i}/{len(URLS)}] Загрузка: {url[:60]}...")
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                lines = response.text.split('\n')
                found = 0
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if any(p in line for p in ['vless://', 'trojan://', 'vmess://', 'ss://', 'h2://']):
                            country = extract_country_from_key(line)
                            if country:
                                if country not in country_keys:
                                    country_keys[country] = []
                                country_keys[country].append(line)
                                found += 1
                print(f"    ✅ Найдено {found} ключей")
            else:
                print(f"    ❌ Ошибка {response.status_code}")
        except Exception as e:
            print(f"    ❌ Ошибка: {str(e)[:50]}")

    print(f"\n📊 Найдено ключей по странам:")
    for country, keys in country_keys.items():
        print(f"  🌍 {country}: {len(keys)} ключей")

    if not country_keys:
        print("\n⚠️ НЕ НАЙДЕНО НИ ОДНОГО КЛЮЧА!")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        sys.exit(0)

    # Создаем JSON с группировкой по странам (ПРОСТОЙ ФОРМАТ)
    json_output = []

    for country, keys in country_keys.items():
        print(f"\n🔄 Создаю профиль для {country} ({len(keys)} ключей)...")
        
        # Находим флаг для страны
        flag = None
        for f, c in COUNTRIES.items():
            if c == country:
                flag = f
                break
        if not flag:
            flag = '🌍'
        
        # ПРОСТОЙ ФОРМАТ - сохраняем оригинальные ссылки
        profile = {
            "remarks": f"{flag} {country}",
            "servers": keys  # Оригинальные ссылки
        }
        
        json_output.append(profile)
        print(f"  ✅ Добавлено {len(keys)} серверов")

    print(f"\n✅ Создано {len(json_output)} профилей стран")

    # Сохраняем в JSON
    print("💾 Сохраняю в JSON...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)

    print(f"✅ Сохранено в {OUTPUT_FILE}")

    total_servers = sum(len(p['servers']) for p in json_output)
    print(f"\n📊 Итоговая статистика:")
    print(f"  🌍 Стран: {len(json_output)}")
    print(f"  🔗 Всего серверов: {total_servers}")
    
    print("\n✅ Скрипт выполнен успешно!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    
    with open("OUTPUT_FILE", 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    
    sys.exit(0)
