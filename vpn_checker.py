#!/usr/bin/env python3
import requests
import re
from datetime import datetime
import urllib.parse

# Список URL для парсинга
URLS = [
    "",
    "https://gitlab.com/zieng2/wl/raw/main/vless_universal.txt",
    "https://storage.yandexcloud.net/mystorage123/whitelist.txt",
    "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/e310946a53d9cd7910bb4381e7fceab83e1f8462/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
    "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/0f61abfd23bfc411b14385a95cfdb90498514a45/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://gist.githubusercontent.com/j80547013-max/1ed9f2d72fd7613eda3c4a36c96955cb/raw/bfd36277ccf212a8ed2800708a749efbcd5a0885/gistfile1.txt",
]

OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.txt"

# Словарь стран и флагов
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

# Сокращения стран для поиска в названиях
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

def detect_country(key):
    """Определение страны по ключу"""
    # Ищем флаг в ключе
    for flag in COUNTRIES.keys():
        if flag in key:
            return flag, COUNTRIES[flag]
    
    # Ищем код страны в названии (например, #RU, #US)
    for code, flag in COUNTRY_CODES.items():
        if f'#{code}' in key or f'_{code}_' in key or f'-{code}-' in key:
            return flag, COUNTRIES.get(flag, code)
    
    # Ищем код страны в домене
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
    
    # Если не найдено - возвращаем 🌍
    return '🌍', 'Мир'

def rename_key(key):
    """Переименование ключа с добавлением флага и страны"""
    flag, country = detect_country(key)
    
    # Удаляем старые названия после #
    if '#' in key:
        base = key.split('#')[0]
        old_name = key.split('#')[1] if len(key.split('#')) > 1 else ''
    else:
        base = key
        old_name = ''
    
    # Создаем новое имя
    new_name = f"{flag} {country} | VPN From Kirill"
    
    # Если в старом имени был номер, добавляем его
    if old_name and old_name[-1].isdigit():
        new_name += f" #{old_name[-1]}"
    
    return f"{base}#{new_name}"

print("🚀 Запуск VPN парсера с переименованием...")

# Собираем все ключи
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
                    # Проверяем наличие протоколов
                    if any(p in line for p in ['vless://', 'trojan://', 'vmess://', 'ss://', 'h2://']):
                        all_keys.add(line)
            print(f"  ✓ [{i}/{len(URLS)}] Загружено")
        else:
            print(f"  ✗ [{i}/{len(URLS)}] Ошибка {response.status_code}")
    except Exception as e:
        print(f"  ✗ [{i}/{len(URLS)}] Ошибка: {str(e)[:30]}")

print(f"📊 Найдено {len(all_keys)} уникальных ключей")

# Переименовываем ключи
renamed_keys = []
for key in all_keys:
    try:
        renamed = rename_key(key)
        renamed_keys.append(renamed)
    except:
        renamed_keys.append(key)

print(f"✏️ Переименовано {len(renamed_keys)} ключей")

# Сохраняем в файл с метаданными
print("💾 Сохраняю в файл...")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    # Метаданные для Happ
    f.write("#profile-title: Free Vpn From KIrill\n")
    f.write("#announce: Бесплатная подписка\n")
    f.write("#profile-update-interval: 12\n")
    f.write("#profile-web-page-url: https://t.me/TourFromKirill\n")
    f.write("\n")
    
    # Информация о времени
    f.write(f"# Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    f.write(f"# Всего ключей: {len(renamed_keys)}\n")
    f.write("#" + "="*50 + "\n\n")
    
    # Записываем ключи
    if renamed_keys:
        for key in sorted(renamed_keys):
            f.write(key + '\n')
        print(f"✅ Сохранено {len(renamed_keys)} ключей")
    else:
        f.write("# Ключи не найдены\n")
        print("⚠️ Ключи не найдены")

print("✅ Готово!")
print("📁 Файл:", OUTPUT_FILE)
