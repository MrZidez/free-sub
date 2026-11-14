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
- [Запуск](#-запуск)
- [GitHub Actions](#-github-actions)
- [Локальный запуск](#-локальный-запуск)

---

## ✨ Возможности

| Фича | Описание |
|------|----------|
| 🔄 **Автообновление** | Запуск каждые 6 часов через GitHub Actions |
| 🌍 **Группировка по странам** | Все ключи из одной страны объединяются в один профиль |
| 🔐 **Поддержка протоколов** | VLESS, TROJAN, VMess, Hysteria2 |
| 🏓 **Проверка пинга** | Опциональная фильтрация по времени ответа |
| 🌐 **Геолокация** | Опциональная проверка реального расположения сервера |
| 🗑️ **Дедупликация** | Удаление дубликатов по IP/домену |
| 📦 **Кэширование** | Сохранение загруженных источников на 1 час |
| 🔄 **Retry-механизм** | Повторные попытки при ошибках загрузки |
| 📝 **Логирование** | Запись всех действий в файл |
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

## 📝 Лицензия

MIT License © 2026 [VPN From Kirill](https://t.me/TourFromKirill)

---

---

> 🚀 **Сделано с ❤️ для бесплатного интернета!**
```

ps
весь скрипт написан с помощью нейронки
