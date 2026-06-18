import datetime

# Просто создаем файл с датой
with open("FREE-VPN-FROM-KIRILL.txt", "w") as f:
    f.write("#profile-title: Free Vpn From KIrill\n")
    f.write("#announce: Бесплатная подписка\n")
    f.write("#profile-update-interval: 12\n")
    f.write("#profile-web-page-url: https://t.me/TourFromKirill\n")
    f.write("\n")
    f.write(f"# Тестовый запуск: {datetime.datetime.now()}\n")
    f.write("vless://test@example.com:443?encryption=none#Test\n")
    f.write("trojan://test@example.com:443?security=tls#Test2\n")

print("✅ Файл создан успешно!")
