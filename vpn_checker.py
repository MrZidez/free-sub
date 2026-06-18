#!/usr/bin/env python3
import requests
from datetime import datetime

print("🚀 START")

# Просто список URL
urls = [
    "https://raw.githubusercontent.com/dmitriistekolnikov/Free_vpns_for_Russ/refs/heads/main/Vip.txt",
    "https://raw.githubusercontent.com/dmitriistekolnikov/Free_vpns_for_Russ/refs/heads/main/YouTube.txt",
    "https://gitlab.com/zieng2/wl/raw/main/vless_universal.txt",
    "https://storage.yandexcloud.net/mystorage123/whitelist.txt",
    "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/e310946a53d9cd7910bb4381e7fceab83e1f8462/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
    "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/0f61abfd23bfc411b14385a95cfdb90498514a45/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
    "https://gist.githubusercontent.com/HalyavusVPNUS/a93def732d3c624029c09c393dd0772e/raw/07febf8476e2603723f94a777542ab69a5c7fa2f/%25D0%25BA%25D0%25BE%25D0%25BD%25D1%2584%25D0%25B8%25D0%25B3%25D0%25B8",
    "https://gist.githubusercontent.com/j80547013-max/1ed9f2d72fd7613eda3c4a36c96955cb/raw/bfd36277ccf212a8ed2800708a749efbcd5a0885/gistfile1.txt",
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
