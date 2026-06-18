#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import subprocess
import re
from datetime import datetime
import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
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
PING_THRESHOLD = 70
MAX_WORKERS = 30
TIMEOUT = 5

# Метаданные для Happ
METADATA = """#profile-title: Free Vpn From KIrill
#announce: Бесплатная подписка
#profile-update-interval: 12
#profile-web-page-url: https://t.me/TourFromKirill
"""

class VPNPingChecker:
    def __init__(self):
        self.good_keys = []
        
    def fetch_urls(self):
        """Загрузка всех ссылок и извлечение ключей"""
        all_keys = []
        logger.info(f"Начинаю загрузку {len(URLS)} URL...")
        
        for i, url in enumerate(URLS, 1):
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    content = response.text
                    keys = self.extract_keys(content)
                    all_keys.extend(keys)
                    logger.info(f"✓ Загружено {len(keys)} ключей из URL {i}/{len(URLS)}")
                else:
                    logger.warning(f"✗ Не удалось загрузить {url}: статус {response.status_code}")
            except Exception as e:
                logger.error(f"✗ Ошибка при загрузке {url}: {e}")
        
        unique_keys = list(set(all_keys))
        logger.info(f"Всего собрано {len(unique_keys)} уникальных ключей")
        return unique_keys
    
    def extract_keys(self, content):
        """Извлечение ключей из текста"""
        keys = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Проверяем разные форматы ключей
            if any(protocol in line.lower() for protocol in ['vless://', 'trojan://', 'vmess://', 'ss://', 'h2://']):
                keys.append(line)
            elif re.match(r'^\d+\.\d+\.\d+\.\d+:\d+', line):
                keys.append(line)
            elif '://' in line:
                keys.append(line)
                
        return keys
    
    def ping_key(self, key):
        """Проверка пинга для ключа"""
        try:
            server = self.extract_server(key)
            if not server:
                return None, None
            
            # В GitHub Actions используем ping
            cmd = ['ping', '-c', '1', '-W', str(TIMEOUT), server]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT + 1)
            
            if result.returncode == 0:
                match = re.search(r'time[=<](\d+\.?\d*)\s*ms', result.stdout, re.IGNORECASE)
                if match:
                    ping_time = float(match.group(1))
                    return key, ping_time
            
            return None, None
            
        except Exception:
            return None, None
    
    def extract_server(self, key):
        """Извлечение сервера из ключа"""
        try:
            if '://' in key:
                parsed = urllib.parse.urlparse(key)
                hostname = parsed.hostname
                if hostname:
                    return hostname
            
            ip_match = re.match(r'^(\d+\.\d+\.\d+\.\d+):\d+', key)
            if ip_match:
                return ip_match.group(1)
            
            return None
        except:
            return None
    
    def check_all_keys(self, keys):
        """Проверка всех ключей с использованием многопоточности"""
        good_keys = []
        total = len(keys)
        
        if total == 0:
            logger.warning("Нет ключей для проверки")
            return []
        
        logger.info(f"Начинаю проверку {total} ключей (порог: {PING_THRESHOLD}ms)...")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_key = {executor.submit(self.ping_key, key): key for key in keys}
            
            for i, future in enumerate(as_completed(future_to_key), 1):
                key = future_to_key[future]
                try:
                    result_key, ping_time = future.result()
                    if result_key and ping_time is not None and ping_time <= PING_THRESHOLD:
                        good_keys.append(result_key)
                        logger.info(f"[{i}/{total}] ✓ Пинг: {ping_time:.1f}ms")
                    elif result_key:
                        if i % 50 == 0:
                            logger.info(f"Обработано {i}/{total} ключей...")
                except Exception as e:
                    logger.error(f"Ошибка при обработке: {e}")
        
        logger.info(f"Найдено {len(good_keys)} ключей с пингом < {PING_THRESHOLD}ms")
        return good_keys
    
    def save_good_keys(self, keys):
        """Сохранение хороших ключей в файл с метаданными"""
        if not keys:
            logger.warning("Нет ключей для сохранения")
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # Записываем метаданные
            f.write(METADATA)
            f.write("\n")  # Пустая строка для разделения
            
            # Записываем информацию о времени обновления
            f.write(f"# Обновлено: {timestamp}\n")
            f.write(f"# Всего ключей: {len(keys)}\n")
            f.write(f"# Порог пинга: < {PING_THRESHOLD}ms\n")
            f.write("#" + "="*50 + "\n\n")
            
            # Записываем ключи
            for key in sorted(keys):
                f.write(key + '\n')
        
        logger.info(f"✅ Сохранено {len(keys)} ключей в {OUTPUT_FILE}")
    
    def run(self):
        """Основной процесс"""
        logger.info("="*50)
        logger.info("🚀 Запуск проверки VPN ключей")
        logger.info(f"📊 Порог пинга: {PING_THRESHOLD}ms")
        logger.info("="*50)
        
        keys = self.fetch_urls()
        if not keys:
            logger.warning("❌ Не удалось загрузить ни одного ключа")
            return False
        
        good_keys = self.check_all_keys(keys)
        
        if good_keys:
            self.save_good_keys(good_keys)
            return True
        else:
            logger.warning("❌ Не найдено ключей с хорошим пингом")
            return False

if __name__ == "__main__":
    import socket
    socket.setdefaulttimeout(30)
    
    checker = VPNPingChecker()
    success = checker.run()
    
    sys.exit(0 if success else 1)
