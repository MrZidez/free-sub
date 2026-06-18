#!/usr/bin/env python3
import requests
import re
import json
import sys
import urllib.parse
from datetime import datetime

print("🚀 Запуск VPN парсера...")
print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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

    # Базовая структура
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

    BASE_OUTBOUNDS_EXTRA = [
        {"protocol": "freedom", "settings": {"domainStrategy": "UseIP"}, "tag": "direct"},
        {"protocol": "blackhole", "tag": "block"}
    ]

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

    def create_outbound_for_key(key):
        """Создает outbound для одного ключа"""
        try:
            parsed = urllib.parse.urlparse(key)
            protocol = parsed.scheme
            hostname = parsed.hostname or ''
            port = parsed.port or 443
            query = urllib.parse.parse_qs(parsed.query)
            
            outbound = {"protocol": protocol, "settings": {}, "streamSettings": {}, "tag": f"proxy-{hostname}"}
            
            if protocol == 'vless':
                user_id = parsed.username or ''
                outbound["settings"] = {
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
                
                outbound["streamSettings"] = stream_settings
                
            elif protocol == 'trojan':
                password = parsed.username or ''
                outbound["settings"] = {
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
                
                outbound["streamSettings"] = stream_settings
            
            elif protocol == 'vmess':
                try:
                    import base64
                    decoded = base64.b64decode(parsed.username or '').decode('utf-8')
                    vmess_data = json.loads(decoded)
                    outbound["settings"] = {
                        "vnext": [{
                            "address": vmess_data.get('add', hostname),
                            "port": vmess_data.get('port', port),
                            "users": [{
                                "id": vmess_data.get('id', ''),
                                "security": vmess_data.get('scy', 'auto'),
                                "alterId": vmess_data.get('aid', 0)
                            }]
                        }]
                    }
                except:
                    pass
            
            return outbound
            
        except Exception as e:
            return None

    print(f"📥 Загружаю {len(URLS)} источников...")

    # Собираем все ключи
    all_raw_keys = []
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
                            all_raw_keys.append(line)
                            found += 1
                print(f"    ✅ Найдено {found} ключей")
            else:
                print(f"    ❌ Ошибка {response.status_code}")
        except Exception as e:
            print(f"    ❌ Ошибка: {str(e)[:50]}")

    print(f"\n📊 Всего найдено сырых ключей: {len(all_raw_keys)}")

    # Удаляем дубликаты
    all_raw_keys = list(dict.fromkeys(all_raw_keys))
    print(f"📊 Уникальных ключей: {len(all_raw_keys)}")

    # Сортируем по странам
    for key in all_raw_keys:
        flag, country = detect_country(key)
        if flag and country:
            if country not in country_keys:
                country_keys[country] = []
            country_keys[country].append(key)
        else:
            # Если страна не определена - пропускаем
            pass

    print(f"\n📊 Найдено ключей по странам:")
    for country, keys in country_keys.items():
        print(f"  🌍 {country}: {len(keys)} ключей")

    if not country_keys:
        print("\n⚠️ НЕ НАЙДЕНО НИ ОДНОГО КЛЮЧА!")
        print("💾 Сохраняю пустой JSON...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        sys.exit(0)

    # Создаем JSON с группировкой по странам
    json_output = []

    for country, keys in country_keys.items():
        print(f"\n🔄 Создаю профиль для {country} ({len(keys)} ключей)...")
        
        flag = None
        for f, c in COUNTRIES.items():
            if c == country:
                flag = f
                break
        if not flag:
            flag = '🌍'
        
        outbounds = []
        for key in keys:
            outbound = create_outbound_for_key(key)
            if outbound:
                outbounds.append(outbound)
        
        outbounds.extend(BASE_OUTBOUNDS_EXTRA)
        
        profile = {
            "dns": BASE_DNS,
            "inbounds": BASE_INBOUNDS,
            "log": {"loglevel": "none"},
            "outbounds": outbounds,
            "policy": BASE_POLICY,
            "remarks": f"{flag} {country}",
            "routing": BASE_ROUTING
        }
        
        json_output.append(profile)
        print(f"  ✅ Добавлено {len(keys)} серверов")

    print(f"\n✅ Создано {len(json_output)} профилей стран")

    # Сохраняем в JSON
    print("💾 Сохраняю в JSON...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, ensure_ascii=False, indent=2)

    print(f"✅ Сохранено в {OUTPUT_FILE}")

    total_servers = 0
    for profile in json_output:
        proxy_count = len([o for o in profile['outbounds'] if o['tag'].startswith('proxy-')])
        total_servers += proxy_count
    
    print(f"\n📊 Итоговая статистика:")
    print(f"  🌍 Стран: {len(json_output)}")
    print(f"  🔗 Всего серверов: {total_servers}")
    
    print("\n✅ Скрипт выполнен успешно!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    
    with open("FREE-VPN-FROM-KIRILL.json", 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    
    sys.exit(0)
