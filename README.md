## 📄 README.md

```markdown
# 🚀 VPN Parser & Country Grouper

[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Auto%20Update-blue)](https://github.com/MrZidez/free-sub/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Автоматический парсер VPN-ключей с группировкой по странам и конвертацией в формат **Sing-Box**.  
Скрипт собирает ключи из указанных источников, фильтрует валидные, группирует по странам и сохраняет в JSON.

---

## 📋 Оглавление

- [Возможности](#-возможности)
- [Установка](#-установка)
- [Настройка](#-настройка)
- [Запуск](#-запуск)
- [Формат вывода](#-формат-вывода)
- [Переменные окружения](#-переменные-окружения)
- [Telegram уведомления](#-telegram-уведомления)
- [GitHub Actions](#-github-actions)
- [Локальный запуск](#-локальный-запуск)

---

## ✨ Возможности

| Фича | Описание |
|------|----------|
| 🔄 **Автообновление** | Запуск каждые 6 часов через GitHub Actions |
| 🌍 **Группировка по странам** | Все ключи из одной страны объединяются в один профиль |
| 📦 **Sing-Box формат** | Совместимость с Sing-Box, Xray, v2rayN, Nekoray |
| 🔐 **Поддержка протоколов** | VLESS, TROJAN, VMess, Hysteria2 |
| 🏓 **Проверка пинга** | Опциональная фильтрация по времени ответа |
| 🌐 **Геолокация** | Опциональная проверка реального расположения сервера |
| 🗑️ **Дедупликация** | Удаление дубликатов по IP/домену |
| 📦 **Кэширование** | Сохранение загруженных источников на 1 час |
| 🔄 **Retry-механизм** | Повторные попытки при ошибках загрузки |
| 📝 **Логирование** | Запись всех действий в файл |
| 📤 **Telegram уведомления** | Отчёты об успехе/ошибке |
| ⚙️ **.env конфигурация** | Все настройки через файл `.env` |

---

## 📦 Установка

### Клонирование репозитория

```bash
git clone https://github.com/MrZidez/free-sub.git
cd free-sub
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Создание файла `source`

В корне проекта создайте файл `source` и добавьте ссылки на источники:

```txt
# Мои источники
https://gitlab.com/zieng2/wl/raw/main/vless_universal.txt
https://storage.yandexcloud.net/mystorage123/whitelist.txt
https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt
```

> 💡 Каждая ссылка на новой строке. Строки начинающиеся с `#` игнорируются.

---

## ⚙️ Настройка

### Файл `.env`

Скопируйте пример конфигурации:

```bash
cp .env.example .env
```

Отредактируйте `.env` под свои нужды:

```env
# Основные настройки
USER_AGENT="happ"
PING_THRESHOLD_MS=250
MAX_KEYS_PER_GROUP=8
MAX_GROUPS_PER_COUNTRY=5
SOURCE_FILE="source"
OUTPUT_FILE="FREE-VPN-FROM-KIRILL.json"
TIMEOUT=15
MAX_WORKERS=10

# Кэширование
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_DIR="cache"

# Retry
RETRY_ENABLED=true
RETRY_COUNT=3
RETRY_DELAY=2

# Фичи
ENABLE_PING_CHECK=false      # Проверка пинга (медленно)
ENABLE_GEO_CHECK=false       # Проверка геолокации (медленно)
ENABLE_DEDUP=true             # Удаление дубликатов
ENABLE_LOGGING=true
LOG_LEVEL="INFO"
LOG_DIR="logs"
COMPRESS_OUTPUT=false         # Сжатый JSON
ADD_METADATA=true             # Добавить метаданные в JSON

# Telegram (опционально)
TG_BOT_TOKEN=""
TG_CHAT_ID=""
TG_NOTIFY_ON_SUCCESS=true
TG_NOTIFY_ON_ERROR=true
```

---

## 🚀 Запуск

### Локальный запуск

```bash
python vpn_checker.py
```

### Запуск с отладкой

```bash
python vpn_checker.py --debug
```

### Одноразовый запуск

Если нужно запустить вручную без ожидания:

```bash
python vpn_checker.py
```

---

## 📄 Формат вывода

### Пример `FREE-VPN-FROM-KIRILL.json`

```json
[
  {
    "remarks": "🇷🇺 Россия",
    "dns": {
      "servers": ["1.1.1.1", "1.0.0.1"],
      "queryStrategy": "UseIP"
    },
    "routing": {
      "rules": [
        {
          "type": "field",
          "protocol": ["bittorrent"],
          "outboundTag": "direct"
        }
      ],
      "domainMatcher": "hybrid",
      "domainStrategy": "IPIfNonMatch"
    },
    "inbounds": [
      {
        "tag": "socks",
        "port": 10808,
        "listen": "127.0.0.1",
        "protocol": "socks",
        "settings": {"udp": true, "auth": "noauth"},
        "sniffing": {
          "enabled": true,
          "routeOnly": false,
          "destOverride": ["http", "tls", "quic"]
        }
      },
      {
        "tag": "http",
        "port": 10809,
        "listen": "127.0.0.1",
        "protocol": "http",
        "settings": {"allowTransparent": false},
        "sniffing": {
          "enabled": true,
          "routeOnly": false,
          "destOverride": ["http", "tls", "quic"]
        }
      }
    ],
    "outbounds": [
      {
        "tag": "proxy-1",
        "protocol": "vless",
        "settings": {
          "vnext": [
            {
              "address": "91.185.83.127",
              "port": 443,
              "users": [
                {
                  "id": "f013e723-e1fb-4cfb-b0e2-044fe058954a",
                  "encryption": "none",
                  "flow": "",
                  "level": 0
                }
              ]
            }
          ]
        },
        "streamSettings": {
          "network": "grpc",
          "security": "reality",
          "realitySettings": {
            "serverName": "max.ru",
            "fingerprint": "qq",
            "publicKey": "t192lvTN6ZtCch9LSAkLOKnKuyYdLLaTJx8tn3VRHz0",
            "shortId": "dfdee30a27b11f0f"
          },
          "grpcSettings": {
            "serviceName": "grpc",
            "multiMode": true
          }
        }
      },
      {"tag": "direct", "protocol": "freedom"},
      {"tag": "block", "protocol": "blackhole"}
    ]
  }
]
```

### Метаданные (если включены)

В конце файла добавляется объект `_metadata`:

```json
{
  "_metadata": {
    "generated": "2026-08-21T15:30:00.123456",
    "total_servers": 42,
    "total_profiles": 5,
    "total_countries": 5,
    "sources": 10,
    "errors": 0,
    "elapsed_seconds": 12.34
  }
}
```

---

## 📤 Telegram уведомления

### Настройка бота

1. Создайте бота у [@BotFather](https://t.me/BotFather)
2. Получите токен: `123456:ABC-DEF`
3. Получите ID чата у [@userinfobot](https://t.me/userinfobot)
4. Добавьте в `.env`:

```env
TG_BOT_TOKEN="123456:ABC-DEF"
TG_CHAT_ID="-1001234567890"
TG_NOTIFY_ON_SUCCESS=true
TG_NOTIFY_ON_ERROR=true
```

### Пример уведомления

```
<b>VPN Parser</b>
✅ УСПЕХ

📊 <b>Статистика:</b>
• Источников: 10
• Серверов: 42
• Стран: 5
• Профилей: 5
• Ошибок: 0

⏱️ Время: 12.34с
📅 2026-08-21 15:30:00
```

---

## 🔄 GitHub Actions

### Автоматическое обновление

Workflow настроен на запуск каждые 6 часов:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'
  workflow_dispatch:
```

### Ручной запуск

1. Перейдите во вкладку **Actions**
2. Выберите **VPN Ping Checker**
3. Нажмите **Run workflow** → **Run workflow**

### Секреты для Telegram

Добавьте в GitHub Secrets:

| Secret | Значение |
|--------|----------|
| `TG_BOT_TOKEN` | Токен вашего бота |
| `TG_CHAT_ID` | ID чата для уведомлений |

---

## 🖥️ Локальный запуск

### Требования

- Python 3.11+
- pip

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/MrZidez/free-sub.git
cd free-sub

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить .env
cp .env.example .env
# Отредактировать .env

# 4. Создать файл source
echo "https://example.com/source.txt" > source

# 5. Запустить
python vpn_checker.py
```

### Структура проекта

```
free-sub/
├── .env                    # Конфигурация
├── source                  # Список источников
├── vpn_checker.py         # Основной скрипт
├── requirements.txt       # Зависимости
├── README.md              # Документация
├── cache/                 # Кэш загрузок
│   └── *.cache
├── logs/                  # Логи
│   └── vpn-parser.log
└── FREE-VPN-FROM-KIRILL.json  # Выходной файл
```

---

## ❓ FAQ

### Q: Почему ключи не добавляются в JSON?

**A:** Проверьте:
- Файл `source` существует и содержит ссылки
- Ссылки в `source` доступны (не заблокированы)
- В ключах есть флаги стран (`🇷🇺`, `🇺🇸` и т.д.)
- Ключи имеют валидный протокол (`vless://`, `trojan://`, `vmess://`, `hysteria://`)

### Q: Как добавить свои источники?

**A:** Добавьте ссылки в файл `source` (каждая на новой строке):

```txt
# Мои источники
https://my-source.com/vless.txt
https://another-source.com/trojan.txt
```

### Q: Как отключить проверку пинга?

**A:** В `.env` установите:
```env
ENABLE_PING_CHECK=false
```

### Q: Как включить Telegram уведомления?

**A:** Добавьте в `.env`:
```env
TG_BOT_TOKEN="ваш_токен"
TG_CHAT_ID="ваш_chat_id"
```

---

## 📝 Лицензия

MIT License © 2026 [VPN From Kirill](https://t.me/TourFromKirill)

---

## 📞 Контакты

- **Telegram канал:** [@TourFromKirill](https://t.me/TourFromKirill)
- **GitHub:** [MrZidez/free-sub](https://github.com/MrZidez/free-sub)

---

> 🚀 **Сделано с ❤️ для бесплатного интернета!**
```

## 📦 Файл `.env.example`

```env
# ============================================================
#  VPN PARSER CONFIGURATION
# ============================================================

# --- Основные настройки ---
USER_AGENT="happ"
PING_THRESHOLD_MS=250
MAX_KEYS_PER_GROUP=8
MAX_GROUPS_PER_COUNTRY=5
SOURCE_FILE="source"
OUTPUT_FILE="FREE-VPN-FROM-KIRILL.json"
TIMEOUT=15
MAX_WORKERS=10

# --- Кэширование ---
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_DIR="cache"

# --- Retry-механизм ---
RETRY_ENABLED=true
RETRY_COUNT=3
RETRY_DELAY=2

# --- Фичи ---
ENABLE_PING_CHECK=false
ENABLE_GEO_CHECK=false
ENABLE_DEDUP=true
ENABLE_RATING=false
ENABLE_LOGGING=true
LOG_LEVEL="INFO"
LOG_DIR="logs"
COMPRESS_OUTPUT=false
ADD_METADATA=true

# --- Telegram уведомления ---
TG_BOT_TOKEN=""
TG_CHAT_ID=""
TG_NOTIFY_ON_SUCCESS=true
TG_NOTIFY_ON_ERROR=true
```

ps
весь скрипт написан с помощью нейронки
