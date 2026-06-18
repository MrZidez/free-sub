#!/usr/bin/env python3
import requests
import re
import json
import sys
from datetime import datetime
import urllib.parse

print("🚀 Запуск VPN парсера...")

try:
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
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
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

    # Список плохих доменов
    BAD_DOMAINS = [
        'mirror', 'github', 'gist', 'raw.githubusercontent', 'yandexcloud', 'storage',
        'gist.githubusercontent', 'githubusercontent', 'cloudflare', 'amazon', 'aws',
        'azure', 'google', 'googleapis', 'cloudfront', 'heroku', 'netlify', 'vercel',
        'example', 'test', 'localhost', '127.0.0.1', '0.0.0.0',
        'roc-taiwan', 'taipeicitygovernment', 'seoulcitygovernment', 'seoulcityhall',
        'kdns.fr', 'hllfly.kdns.fr', 'org.ua', 'tokyometropolis',
        'duckdns', 'no-ip', 'dyndns', 'ddns', 'serveo', 'ngrok',
        '.tk', '.ml', '.ga', '.cf', '.gq', '.top', '.xyz', '.club'
    ]

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

    # Базовая структура DNS и INBOUNDS (общая для всех)
    BASE_DNS = {
        "servers": ["77.88.8.8", "77.88.8.1"],
        "queryStrategy": "UseIP",
        "cacheSize": 512,
        "readTimeout": "50ms",
        "writeTimeout": "50ms"
    }

    BASE_INBOUNDS = [
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
    ]

    BASE_POLICY = {
        "levels": {
            "8": {
                "connIdle": 60,
                "downlinkOnly": 0,
                "handshake": 1,
                "uplinkOnly": 0,
                "bufferSize": 16
            }
        }
    }

    BASE_ROUTING = {
        "domainStrategy": "AsIs",
        "rules": [
            {"ip": ["geoip:private"], "outboundTag": "direct"},
            {"network": "tcp,udp", "outboundTag": "proxy"}
        ]
    }

    def is_bad_domain(hostname):
        if not hostname:
            return True
        hostname_lower = hostname.lower()
        for bad in BAD_DOMAINS:
            if bad in hostname_lower:
                return True
        return False

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

    def convert_to_singbox_config(key, flag, country_name):
        """Конвертирует ключ в Sing-Box конфиг"""
        try:
            parsed = urllib.parse.urlparse(key)
            protocol = parsed.scheme
            hostname = parsed.hostname or ''
            port = parsed.port or 443
            query = urllib.parse.parse_qs(parsed.query)
            
            # Базовая структура outbounds
            outbounds = [
                {"protocol": protocol, "settings": {}, "streamSettings": {}, "tag": "proxy"},
                {"protocol": "freedom", "settings": {"domainStrategy": "UseIP"}, "tag": "direct"},
                {"protocol": "blackhole", "tag": "block"}
            ]
            
            # Настраиваем в зависимости от протокола
            if protocol == 'vless':
                user_id = parsed.username or ''
                outbounds[0]["settings"] = {
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
                    ws_settings = {"path": query.get('path', ['/'])[0]}
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
                    stream_settings["grpcSettings"] = {
                        "serviceName": query.get('serviceName', [''])[0],
                        "multiMode": True
                    }
                
                if network == 'tcp':
                    stream_settings["tcpSettings"] = {"header": {"type": "none"}}
                
                outbounds[0]["streamSettings"] = stream_settings
                
            elif protocol == 'trojan':
                password = parsed.username or ''
                outbounds[0]["settings"] = {
                    "servers": [{
                        "address": hostname,
                        "port": port,
                        "password": password,
                        "sni": query.get('sni', [hostname])[0],
                        "udp": True
                    }]
                }
                
                security = query.get('security', ['tls'])[0]
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
                
                if security == 'tls':
                    stream_settings["tlsSettings"] = {
                        "serverName": query.get('sni', [hostname])[0],
                        "fingerprint": query.get('fp', ['chrome'])[0],
                        "allowInsecure": False
                    }
                
                if network == 'ws':
                    ws_settings = {"path": query.get('path', ['/'])[0]}
                    if 'host' in query:
                        ws_settings["headers"] = {"Host": query['host'][0]}
                    stream_settings["wsSettings"] = ws_settings
                
                outbounds[0]["streamSettings"] = stream_settings
            
            # Собираем полный конфиг
            config = {
                "dns": BASE_DNS,
                "inbounds": BASE_INBOUNDS,
                "log": {"loglevel": "none"},
                "outbounds": outbounds,
                "policy": BASE_POLICY,
                "remarks": f"{flag} {country_name}",
                "routing": BASE_ROUTING
            }
            
            return config
            
        except Exception as e:
            print(f"  ⚠️ Ошибка конвертации ключа: {e}")
            return None

    print(f"📥 Загружаю {len(URLS)} источников...")

    # Собираем ключи
    all_keys = []
    
    for i, url in enumerate(URLS, 1):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                lines = response.text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if any(p in line for p in ['vless://', 'trojan://', 'vmess://', 'ss://', 'h2://']):
                            all_keys.append(line)
                print(f"  ✓ [{i}/{len(URLS)}] Загружено")
            else:
                print(f"  ✗ [{i}/{len(URLS)}] Ошибка {response.status_code}")
        except Exception as e:
            print(f"  ✗ [{i}/{len(URLS)}] Ошибка: {str(e)[:30]}")

    print(f"\n📊 Найдено {len(all_keys)} ключей")

    # Фильтруем и конвертируем
    json_output = []
    country_stats = {}

    for key in all_keys:
        flag, country = detect_country(key)
        if flag and country:
            # Проверяем домен
            try:
                if '://' in key:
                    parsed = urllib.parse.urlparse(key)
                    hostname = parsed.hostname or ''
                    if is_bad_domain(hostname):
                        continue
            except:
                continue
            
            # Конвертируем в Sing-Box конфиг
            config = convert_to_singbox_config(key, flag, country)
            if config:
                json_output.append(config)
                if country not in country_stats:
                    country_stats[country] = 0
                country_stats[country] += 1

    print(f"\n📊 Сконвертировано {len(json_output)} профилей")
    print("\n🌍 Статистика по странам:")
    for country, count in sorted(country_stats.items(), key=lambda x: -x[1]):
        print(f"  {country}: {count} ключей")

    # Сохраняем в JSON
    print("\n💾 Сохраняю в JSON...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)

    print(f"✅ Сохранено в {OUTPUT_FILE}")
    print(f"\n📊 Итоговая статистика:")
    print(f"  🔗 Всего серверов: {len(json_output)}")
    print(f"  🌍 Стран: {len(country_stats)}")
    
    print("\n✅ Скрипт выполнен успешно!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    
    # Создаем пустой JSON чтобы не ломать workflow
    with open("FREE-VPN-FROM-KIRILL.json", 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    
    sys.exit(0)
