#!/usr/bin/env python3
import requests
from datetime import datetime

print("🚀 START")

# Просто список URL
urls = [
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/1.txt",
    "https://raw.githubusercontent.com/nikita29a/FreeProxyList/main/mirror/2.txt",
]

all_keys = []

for url in urls:
    try:
        print(f"Downloading: {url}")
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            lines = r.text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '://' in line:
                        all_keys.append(line)
            print(f"  Found {len(lines)} lines")
    except Exception as e:
        print(f"  Error: {e}")

print(f"Total keys: {len(all_keys)}")

# Сохраняем
with open("FREE-VPN-FROM-KIRILL.txt", "w") as f:
    f.write("#profile-title: Free Vpn From KIrill\n")
    f.write("#announce: Бесплатная подписка\n")
    f.write("#profile-update-interval: 12\n")
    f.write("#profile-web-page-url: https://t.me/TourFromKirill\n")
    f.write("\n")
    f.write(f"# Updated: {datetime.now()}\n")
    f.write(f"# Total: {len(all_keys)}\n\n")
    
    for key in all_keys[:10]:  # Только первые 10 для теста
        f.write(key + "\n")

print("✅ DONE")
