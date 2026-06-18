#!/usr/bin/env python3
import requests
import re
import json
import sys
import urllib.parse
from datetime import datetime
import os

print("🚀 Запуск VPN парсера...")
print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
    # НОВЫЙ СПИСОК URL ДЛЯ ПАРСИНГА
    URLS = [
        "https://raw.githubusercontent.com/uretkavpn/Uretkavpn/refs/heads/main/UretkaVpn.txt",
        "https://github.com/Remiuc0ff/ya-nikogo-ne-ubival/raw/refs/heads/Remiuc0ff-patch-1/okak",
        "https://raw.githubusercontent.com/btsk161/Freeinternet_byMygalaru.github.io/refs/heads/main/premium.txt",
        "https://raw.githubusercontent.com/v0id9/vpn-configs/refs/heads/main/vpn.txt"
    ]

    OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.json"

    # Удаляем дубликаты URL
    URLS = list(dict.fromkeys(URLS))
    print(f"📋 Уникальных источников: {len(URLS)}")

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
    total_found = 0

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
                                total_found += 1
                print(f"    ✅ Найдено {found} ключей")
            else:
                print(f"    ❌ Ошибка {response.status_code}")
        except Exception as e:
            print(f"    ❌ Ошибка: {str(e)[:50]}")

    print(f"\n📊 Всего найдено ключей: {total_found}")
    print(f"\n📊 Распределение по странам:")
    for country, keys in country_keys.items():
        print(f"  🌍 {country}: {len(keys)} ключей")

    # ВСЕГДА создаем файл, даже если ключей нет
    json_output = []

    if country_keys:
        # Создаем JSON с группировкой по странам
        for country, keys in country_keys.items():
            print(f"\n🔄 Создаю профиль для {country} ({len(keys)} ключей)...")
            
            flag = None
            for f, c in COUNTRIES.items():
                if c == country:
                    flag = f
                    break
            if not flag:
                flag = '🌍'
            
            profile = {
                "remarks": f"{flag} {country}",
                "servers": keys
            }
            json_output.append(profile)
            print(f"  ✅ Добавлено {len(keys)} серверов")
    else:
        # Если ключей нет - создаем пустой массив с информацией
        print("\n⚠️ КЛЮЧИ НЕ НАЙДЕНЫ! Создаю пустой файл...")
        json_output = []

    print(f"\n✅ Создано {len(json_output)} профилей стран")

    # ПРИНУДИТЕЛЬНО сохраняем в JSON (перезаписываем файл)
    print("💾 Сохраняю в JSON...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)
    
    # Проверяем, что файл создался
    if os.path.exists(OUTPUT_FILE):
        file_size = os.path.getsize(OUTPUT_FILE)
        print(f"✅ Файл создан! Размер: {file_size} байт")
        
        # Показываем содержимое для проверки
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📄 Первые 200 символов: {content[:200]}...")
    else:
        print(f"❌ ОШИБКА: Файл {OUTPUT_FILE} не создан!")

    # Статистика
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
    
    # ПРИНУДИТЕЛЬНО создаем файл даже при ошибке
    print("💾 Создаю пустой JSON из-за ошибки...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    
    sys.exit(0)
