#!/bin/bash

# Beri jeda 5 detik saat booting agar sistem grafis siap
sleep 5

# Cek apakah ada monitor terhubung di port HDMI mana pun
if kmsprint | grep -q "HDMI-A-.*connector: connected"; then
    echo "HDMI Terdeteksi! Masuk ke Desktop GUI Normal."
else
    echo "HDMI Tidak Ada! Menampilkan Mode Kiosk di Layar 3.5 Inci..."
    # Menjalankan script Python yang kita buat di Langkah 1
    python3 /home/lucifrr/Documents/Tkinter-Kiosk/dashboard.py
fi

