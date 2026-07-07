#!/bin/bash

sleep 5

# 1. Cek apakah HDMI tercolok
if kmsprint | grep -q "HDMI-A-.*connector: connected"; then
    echo "HDMI Terdeteksi! Mengaktifkan Mode Dual Monitor..."
    
    # Mengatur HDMI-A-1 sebagai layar utama (Desktop), 
    # dan menaruh layar LCD (misal namanya DSI-1 atau SPI-1) di sebelahnya.
    DISPLAY=:0 xrandr --output HDMI-A-1 --primary --mode 1920x1080 --pos 0x0 \
                   --output DSI-1 --mode 480x320 --pos 1920x0
    
    # Jalankan aplikasi Python Kiosk, lalu PAKSA posisinya agar bergeser ke layar kedua (posisi X = 1920)
    DISPLAY=:0 /home/lucifrr/Documents/Tkinter-Kiosk/env/bin/python /home/lucifrr/Documents/Tkinter-Kiosk/dashboard.py --screen 2

else
    echo "HDMI Tidak Ada! Menampilkan Mode Kiosk Tunggal..."
    
    # Jika hanya ada LCD 3.5 inci, jalankan seperti biasa memenuhi layar utama
    DISPLAY=:0 /home/lucifrr/Documents/Tkinter-Kiosk/env/bin/python /home/lucifrr/Documents/Tkinter-Kiosk/dashboard.py
fi