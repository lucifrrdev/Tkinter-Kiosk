# Kiosk Controller (Tkinter Dashboard)

Panduan ini menjelaskan cara menginstal dependensi dan menjalankan aplikasi Kiosk Controller pada sistem operasi Windows maupun Linux/macOS.

## Prasyarat
Pastikan Anda sudah menginstal Python (disarankan versi **Python 3.10 ke atas**). Anda bisa memverifikasi dengan menjalankan perintah berikut di Terminal/PowerShell:
```bash
python --version
```

---

## Langkah 1: Membuat Virtual Environment (Opsional tetapi Direkomendasikan)
Gunakan *virtual environment* agar pustaka yang diinstal tidak mengganggu instalasi Python global Anda.

### Windows (PowerShell/CMD):
```powershell
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# ATAU Aktifkan virtual environment (CMD)
.\venv\Scripts\activate.bat
```

### Linux / macOS:
```bash
# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate
```

*(Setelah aktif, Anda akan melihat tanda `(venv)` di depan baris terminal Anda).*

---

## Langkah 2: Menginstal Dependensi
Instal pustaka-pustaka yang diperlukan menggunakan file `requirements.txt`:
```bash
pip install -r requirements.txt
```

> **Catatan untuk Windows**: Pustaka `smbus2` dirancang khusus untuk Linux/Raspberry Pi (akses I2C). Pada sistem operasi Windows, modul ini akan tetap terinstal tetapi fungsinya akan memicu error di latar belakang (namun sudah ditangani dengan aman oleh blok `try-except` di kode aplikasi, sehingga aplikasi tidak akan crash).

---

## Langkah 3: Menjalankan Aplikasi

Jalankan skrip utama [dashboard.py](file:///c:/Users/ESI/Documents/Project/Tkinter%20Kiosk/dashboard.py) dengan perintah berikut:

```bash
python dashboard.py
```

### Opsi Tambahan (Menampilkan di Layar Kedua):
Jika Anda memiliki layar/monitor kedua (misal: layar LCD Kiosk eksternal) dan ingin menampilkan aplikasi langsung di monitor tersebut secara otomatis, gunakan argumen berikut:
```bash
python dashboard.py --screen 2
```

---

## Tombol Navigasi / Kontrol
* **Keluar Aplikasi**: Tekan tombol **`q`** pada keyboard Anda untuk menutup jendela aplikasi Kiosk.
