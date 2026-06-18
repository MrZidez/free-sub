#!/usr/bin/env python3
import requests
import re
from datetime import datetime
import sys

# Список URL для парсинга
URLS = [
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/1.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/2.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/3.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/4.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/5.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/6.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/7.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/8.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/9.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/10.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/11.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/12.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/13.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/14.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/15.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/16.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/17.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/26.txt",
    "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/27.txt",
    "https://github.com/KiryaScript/white-lists/raw/refs/heads/main/githubmirror/28.txt",
    "https://github.com/AvenCores/goida-vpn-configs/raw/refs/heads/main/githubmirror/26.txt",
    "https://gist.githubusercontent.com/j80547013-max/5ef5a20db71c4458ea9ddb6f8344d092/raw/66c6ff7874bff72282e75b20750f2562696d5f0b/gistfile1.txt",
    "https://raw.githubusercontent.com/uretkavpn/Uretkavpn/refs/heads/main/UretkaVpn.txt",
    "https://gist.githubusercontent.com/moksim76/2e08a884c87b12cb98fcfb684820d475/raw/2a1c8f1ce486e0759e2922fd9be27de02d3ec6bb/XuexVpn%2520Free",
    "https://raw.githubusercontent.com/WSJuJuB01/cyan-anatola-55/refs/heads/main/WSVPN",
    "https://github.com/Remiuc0ff/ya-nikogo-ne-ubival/raw/refs/heads/Remiuc0ff-patch-1/okak",
    "https://storage.yandexcloud.net/mystorage123/whitelist.txt",
    "https://raw.githubusercontent.com/VansFenix/WildVF-/refs/heads/main/vansFenix%232",
    "https://raw.githubusercontent.com/ByeWhiteLists/ByeWhiteLists2/refs/heads/main/ByeWhiteLists2.txt",
    "https://raw.githubusercontent.com/VansFenix/WildVF-/refs/heads/main/VansFenix%231",
    "https://raw.githubusercontent.com/cinev505/VlessTrogan-vpn-key/refs/heads/main/WhiteList-VPN-Vless",
    "https://raw.githubusercontent.com/WSJuJuB01/urban-succotash/refs/heads/main/NotHinGV5",
    "https://raw.githubusercontent.com/xpavpn-official/XpaVPN/refs/heads/main/index.html",
    "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/splitted/trojan.txt"
]

OUTPUT_FILE = "FREE-VPN-FROM-KIRILL.txt"

print("🚀 Запуск VPN парсера...")

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
    f.write(f"# Всего ключей: {len(all_keys)}\n")
    f.write("#" + "="*50 + "\n\n")
    
    # Записываем ключи
    if all_keys:
        for key in sorted(all_keys):
            f.write(key + '\n')
        print(f"✅ Сохранено {len(all_keys)} ключей")
    else:
        f.write("# Ключи не найдены\n")
        print("⚠️ Ключи не найдены")

print("✅ Готово!")
print("📁 Файл:", OUTPUT_FILE)
