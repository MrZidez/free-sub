#!/usr/bin/env python3
print("Hello from Python!")
print("Creating file...")

with open("FREE-VPN-FROM-KIRILL.txt", "w") as f:
    f.write("#profile-title: Free Vpn From KIrill\n")
    f.write("#announce: Бесплатная подписка\n")
    f.write("#profile-update-interval: 12\n")
    f.write("#profile-web-page-url: https://t.me/TourFromKirill\n")
    f.write("\n")
    f.write("# Test file created successfully!\n")
    f.write("vless://test@example.com:443?encryption=none#Test\n")

print("File created!")
