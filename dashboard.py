import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
import sys
import subprocess
from datetime import datetime
import psutil

# Import modular components
from widgets import FONT_FAMILY, FlatProgressBar, CardButton
from system_services import (
    get_ip_address,
    get_x1202_battery_percentage,
    get_ssh_status,
    get_firewall_status,
    get_dnsmasq_status,
    toggle_ssh,
    _get_linux_terminal
)
from screensaver import ScreensaverManager

class KioskApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Kiosk Controller")
        
        # Setup screen geometry and fullscreen based on command line arguments
        if "--screen 2" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "--screen"):
            # Posisi monitor kedua dimulai dari koordinat X=1920 (lebar monitor pertama)
            self.window.geometry("480x320+1920+0") 
            if os.name == 'nt':
                self.window.attributes('-fullscreen', True)
            else:
                self.window.overrideredirect(True)
                self.window.focus_force()
        else:
            # Jika mode single monitor (Hanya LCD 3.5 inci)
            self.window.geometry("480x320+0+0")
            if os.name == 'nt':
                self.window.attributes('-fullscreen', True)
            else:
                self.window.overrideredirect(True)
                self.window.focus_force()
            
        self.window.configure(bg="#0f172a") # Dark Slate 900

        self.window.bind('<q>', lambda e: self.exit_app())

        # Main Layout Grid
        self.window.grid_rowconfigure(0, weight=0)
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_rowconfigure(2, weight=0)
        self.window.grid_columnconfigure(0, weight=1)

        # ------------------- HEADER FRAME -------------------
        self.header = tk.Frame(window, bg="#1e293b", height=30)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        self.lbl_title = tk.Label(
            self.header, 
            text="⚙️ KIOSK", 
            font=(FONT_FAMILY, 10, "bold"), 
            bg="#1e293b", 
            fg="#f8fafc"
        )
        self.lbl_title.pack(side="left", padx=5, pady=5)

        self.ip_address = get_ip_address()
        self.lbl_ip = tk.Label(
            self.header,
            text=f"IP: {self.ip_address}",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#1e293b",
            fg="#94a3b8"
        )
        self.lbl_ip.pack(side="left", padx=6, pady=5)

        self.lbl_firewall = tk.Label(
            self.header,
            text="FW: ...",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#1e293b",
            fg="#94a3b8"
        )
        self.lbl_firewall.pack(side="left", padx=6, pady=5)

        self.lbl_dnsmasq = tk.Label(
            self.header,
            text="DNS: ...",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#1e293b",
            fg="#94a3b8"
        )
        self.lbl_dnsmasq.pack(side="left", padx=6, pady=5)

        self.lbl_clock = tk.Label(
            self.header,
            font=(FONT_FAMILY, 9, "bold"),
            bg="#1e293b",
            fg="#38bdf8"
        )
        self.lbl_clock.pack(side="right", padx=6, pady=5)
        self.update_clock()

        # ------------------- CONTENT FRAME -------------------
        self.content = tk.Frame(window, bg="#0f172a")
        self.content.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=1)

        # CardButton 1: TTY1
        self.btn_terminal = CardButton(
            self.content, 
            icon="💻", 
            title="TTY1", 
            subtitle="CLI Murni",
            bg_color="#0284c7",
            hover_color="#0369a1",
            command=self.switch_to_tty1
        )
        self.btn_terminal.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # CardButton 2: Wi-Fi Setup
        self.btn_wifi = CardButton(
            self.content, 
            icon="📶", 
            title="WIFI SETUP", 
            subtitle="nmtui Panel",
            bg_color="#6d28d9",
            hover_color="#5b21b6",
            command=self.switch_to_wifi_setup
        )
        self.btn_wifi.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # CardButton 3: SSH Control
        self.btn_ssh = CardButton(
            self.content, 
            icon="🔑", 
            title="SSH SYSTEM", 
            subtitle="Memeriksa...",
            bg_color="#475569", 
            hover_color="#334155",
            command=self.confirm_toggle_ssh
        )
        self.btn_ssh.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.update_ssh_button_loop()

        # CardButton 4: TTY2 (BTOP)
        self.btn_btop = CardButton(
            self.content, 
            icon="📊", 
            title="TTY2", 
            subtitle="BTOP Monitor",
            bg_color="#d97706",
            hover_color="#b45309",
            command=self.switch_to_tty2
        )
        self.btn_btop.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # ------------------- BOTTOM STATS BAR -------------------
        self.stats_bar = tk.Frame(window, bg="#1e293b", height=42)
        self.stats_bar.grid(row=2, column=0, sticky="ew")
        self.stats_bar.grid_propagate(False)
        self.stats_bar.grid_columnconfigure(0, weight=1)
        self.stats_bar.grid_columnconfigure(1, weight=1)
        self.stats_bar.grid_columnconfigure(2, weight=1)
        self.stats_bar.grid_columnconfigure(3, weight=1)
        self.stats_bar.grid_columnconfigure(4, weight=1)

        # CPU Card
        self.cell_cpu = tk.Frame(self.stats_bar, bg="#0f172a", highlightthickness=1, highlightbackground="#334155")
        self.cell_cpu.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
        self.lbl_cpu = tk.Label(self.cell_cpu, text="CPU: 0%", font=(FONT_FAMILY, 8, "bold"), bg="#0f172a", fg="#f1f5f9")
        self.lbl_cpu.pack(anchor="center", pady=(2, 0))
        self.bar_cpu = FlatProgressBar(self.cell_cpu, width=70, height=3, bg_color="#1e293b", fill_color="#3b82f6")
        self.bar_cpu.pack(anchor="center", pady=(1, 2))

        # RAM Card
        self.cell_ram = tk.Frame(self.stats_bar, bg="#0f172a", highlightthickness=1, highlightbackground="#334155")
        self.cell_ram.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")
        self.lbl_ram = tk.Label(self.cell_ram, text="RAM: 0%", font=(FONT_FAMILY, 8, "bold"), bg="#0f172a", fg="#f1f5f9")
        self.lbl_ram.pack(anchor="center", pady=(2, 0))
        self.bar_ram = FlatProgressBar(self.cell_ram, width=70, height=3, bg_color="#1e293b", fill_color="#a855f7")
        self.bar_ram.pack(anchor="center", pady=(1, 2))

        # Storage/Disk Card
        self.cell_disk = tk.Frame(self.stats_bar, bg="#0f172a", highlightthickness=1, highlightbackground="#334155")
        self.cell_disk.grid(row=0, column=2, padx=2, pady=2, sticky="nsew")
        self.lbl_disk = tk.Label(self.cell_disk, text="Disk: 0%", font=(FONT_FAMILY, 8, "bold"), bg="#0f172a", fg="#f1f5f9")
        self.lbl_disk.pack(anchor="center", pady=(2, 0))
        self.bar_disk = FlatProgressBar(self.cell_disk, width=70, height=3, bg_color="#1e293b", fill_color="#eab308")
        self.bar_disk.pack(anchor="center", pady=(1, 2))

        # Temperature Card
        self.cell_temp = tk.Frame(self.stats_bar, bg="#0f172a", highlightthickness=1, highlightbackground="#334155")
        self.cell_temp.grid(row=0, column=3, padx=2, pady=2, sticky="nsew")
        self.lbl_temp = tk.Label(self.cell_temp, text="Temp: N/A", font=(FONT_FAMILY, 8, "bold"), bg="#0f172a", fg="#f43f5e")
        self.lbl_temp.pack(anchor="center", pady=(2, 0))
        self.bar_temp = FlatProgressBar(self.cell_temp, width=70, height=3, bg_color="#1e293b", fill_color="#f43f5e")
        self.bar_temp.pack(anchor="center", pady=(1, 2))

        # Battery Card
        self.cell_battery = tk.Frame(self.stats_bar, bg="#0f172a", highlightthickness=1, highlightbackground="#334155")
        self.cell_battery.grid(row=0, column=4, padx=2, pady=2, sticky="nsew")
        self.lbl_battery = tk.Label(self.cell_battery, text="Bat: N/A", font=(FONT_FAMILY, 8, "bold"), bg="#0f172a", fg="#10b981")
        self.lbl_battery.pack(anchor="center", pady=(2, 0))
        self.bar_battery = FlatProgressBar(self.cell_battery, width=70, height=3, bg_color="#1e293b", fill_color="#10b981")
        self.bar_battery.pack(anchor="center", pady=(1, 2))

        # Trigger initial stats updates
        self.update_stats()

        # ------------------- SCREENSAVER MANAGER -------------------
        self.screensaver_manager = ScreensaverManager(self.window)

    def update_clock(self):
        now = datetime.now().strftime("%d-%m  %H:%M:%S")
        self.lbl_clock.configure(text=now)
        self.window.after(1000, self.update_clock)

    def update_stats(self):
        try:
            # CPU
            cpu = psutil.cpu_percent()
            self.lbl_cpu.configure(text=f"CPU: {cpu}%")
            self.bar_cpu.set_value(cpu)

            # RAM
            ram = psutil.virtual_memory()
            self.lbl_ram.configure(text=f"RAM: {ram.percent}%")
            self.bar_ram.set_value(ram.percent)

            # Storage
            disk = psutil.disk_usage('/')
            self.lbl_disk.configure(text=f"Disk: {disk.percent}%")
            self.bar_disk.set_value(disk.percent)

            # Temperature
            temp_c = 0
            temp_str = "Temp: N/A"
            if os.name != 'nt':
                try:
                    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                        temp_c = int(f.read()) / 1000.0
                        temp_str = f"Temp: {temp_c:.1f}°C"
                except Exception:
                    pass
            else:
                temp_c = 38.5
                temp_str = f"Temp: {temp_c:.1f}°C"
            self.lbl_temp.configure(text=temp_str)
            
            temp_pct = max(0, min(100, int((temp_c - 30) / 50.0 * 100))) if temp_c > 0 else 0
            self.bar_temp.set_value(temp_pct)

            # Battery
            battery = psutil.sensors_battery()
            if battery:
                plugged = "⚡" if battery.power_plugged else "🔋"
                self.lbl_battery.configure(text=f"Bat: {battery.percent}% {plugged}")
                self.bar_battery.set_value(battery.percent)
            else:
                capacity, voltage = get_x1202_battery_percentage()
                if capacity is not None:
                    self.lbl_battery.configure(text=f"Bat: {capacity:.1f}% ({voltage:.2f}V) 🔋")
                    self.bar_battery.set_value(int(capacity))
                else:
                    self.lbl_battery.configure(text="Bat: AC 🔌")
                    self.bar_battery.set_value(100)

            # Firewall Status
            fw_active = get_firewall_status()
            if fw_active:
                self.lbl_firewall.configure(text="FW: ON", fg="#10b981")
            else:
                self.lbl_firewall.configure(text="FW: OFF", fg="#ef4444")

            # dnsmasq Status
            dns_active = get_dnsmasq_status()
            if dns_active:
                self.lbl_dnsmasq.configure(text="DNS: ON", fg="#10b981")
            else:
                self.lbl_dnsmasq.configure(text="DNS: OFF", fg="#ef4444")
        except Exception as e:
            print(f"Error updating stats: {e}")
            
        self.window.after(3000, self.update_stats)

    def exit_app(self):
        if messagebox.askokcancel("Keluar Kiosk", "Apakah Anda yakin ingin menutup aplikasi Kiosk?"):
            self.window.destroy()

    def switch_to_tty1(self):
        try:
            if os.name == 'nt':
                # Windows fallback: buka cmd
                subprocess.Popen(["cmd.exe"])
            else:
                # Buka terminal emulator dalam mode fullscreen (seperti CLI murni TTY)
                term = _get_linux_terminal()
                if term:
                    if term in ["lxterminal", "xfce4-terminal", "konsole"]:
                        subprocess.Popen([term, "--fullscreen"])
                    elif term == "gnome-terminal":
                        subprocess.Popen([term, "--fullscreen"])
                    elif term == "xterm":
                        subprocess.Popen([term, "-fullscreen"])
                    else:
                        subprocess.Popen([term])
                else:
                    messagebox.showerror(
                        "Terminal Tidak Ditemukan", 
                        "Tidak ada terminal emulator (lxterminal, xterm, dll) yang terinstall di sistem."
                    )
        except Exception as e:
            messagebox.showerror("Error TTY1", f"Gagal membuka terminal: {e}")

    def switch_to_tty2(self):
        try:
            if os.name == 'nt':
                # Windows fallback: buka cmd running btop if possible
                subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", "btop -p 1"])
            else:
                import shutil
                if not shutil.which("btop"):
                    messagebox.showerror(
                        "BTOP Tidak Ditemukan",
                        "Aplikasi btop belum terinstall di sistem Anda.\n\n"
                        "Silakan install via SSH dengan menjalankan:\n"
                        "sudo apt update && sudo apt install -y btop"
                    )
                    return

                # Buka BTOP monitor secara fullscreen menggunakan terminal emulator
                term = _get_linux_terminal()
                if term:
                    if term == "lxterminal":
                        subprocess.Popen([term, "--fullscreen", "-e", "btop -p 1"])
                    elif term == "xterm":
                        subprocess.Popen([term, "-fullscreen", "-e", "btop -p 1"])
                    elif term == "xfce4-terminal":
                        subprocess.Popen([term, "--fullscreen", "-e", "btop -p 1"])
                    elif term == "gnome-terminal":
                        subprocess.Popen([term, "--fullscreen", "--", "btop", "-p", "1"])
                    elif term == "konsole":
                        subprocess.Popen([term, "--fullscreen", "-e", "btop -p 1"])
                    else:
                        subprocess.Popen([term, "-e", "btop -p 1"])
                else:
                    messagebox.showerror(
                        "Terminal Tidak Ditemukan", 
                        "Tidak ada terminal emulator untuk menjalankan btop."
                    )
        except Exception as e:
            messagebox.showerror("Error TTY2", f"Gagal membuka BTOP: {e}")

    def update_ssh_button(self):
        is_active = get_ssh_status()
        if is_active:
            self.btn_ssh.configure_button(
                title="SSH SYSTEM", 
                subtitle="Status: AKTIF (Mati)",
                bg_color="#10b981",
                hover_color="#059669"
            )
        else:
            self.btn_ssh.configure_button(
                title="SSH SYSTEM", 
                subtitle="Status: MATI (Aktif)",
                bg_color="#e11d48",
                hover_color="#be123c"
            )

    def update_ssh_button_loop(self):
        self.update_ssh_button()
        self.window.after(5000, self.update_ssh_button_loop)

    def confirm_toggle_ssh(self):
        current_active = get_ssh_status()
        action_name = "MEMATIKAN" if current_active else "MENGAKTIFKAN"
        if messagebox.askyesno("SSH System", f"Apakah Anda yakin ingin {action_name} SSH server?"):
            try:
                toggle_ssh(current_active)
                self.window.after(1200, self.update_ssh_button)
            except Exception as e:
                messagebox.showerror("Error SSH", f"Gagal mengontrol SSH: {e}")

    def switch_to_wifi_setup(self):
        try:
            if os.name == 'nt':
                # Windows fallback: buka cmd running nmtui if possible
                subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", "nmtui"])
            else:
                import shutil
                if not shutil.which("nmtui"):
                    messagebox.showerror(
                        "NMTUI Tidak Ditemukan",
                        "Aplikasi nmtui belum terinstall di sistem Anda."
                    )
                    return

                # Buka NMTUI secara fullscreen menggunakan terminal emulator
                term = _get_linux_terminal()
                if term:
                    if term == "lxterminal":
                        subprocess.Popen([term, "--fullscreen", "-e", "nmtui"])
                    elif term == "xterm":
                        subprocess.Popen([term, "-fullscreen", "-e", "nmtui"])
                    elif term == "xfce4-terminal":
                        subprocess.Popen([term, "--fullscreen", "-e", "nmtui"])
                    elif term == "gnome-terminal":
                        subprocess.Popen([term, "--fullscreen", "--", "nmtui"])
                    elif term == "konsole":
                        subprocess.Popen([term, "--fullscreen", "-e", "nmtui"])
                    else:
                        subprocess.Popen([term, "-e", "nmtui"])
                else:
                    messagebox.showerror(
                        "Terminal Tidak Ditemukan", 
                        "Tidak ada terminal emulator untuk menjalankan nmtui."
                    )
        except Exception as e:
            messagebox.showerror("Error WIFI Setup", f"Gagal membuka NMTUI: {e}")

# Menjalankan aplikasi
if __name__ == "__main__":
    root = tk.Tk()
    
    # Fix dropdown/listbox styling issue on Linux (blank/white text on white background)
    root.option_add('*TCombobox*Listbox.background', '#1e293b')
    root.option_add('*TCombobox*Listbox.foreground', 'white')
    root.option_add('*TCombobox*Listbox.selectBackground', '#38bdf8')
    root.option_add('*TCombobox*Listbox.selectForeground', '#0f172a')
    root.option_add('*TCombobox*Listbox.font', (FONT_FAMILY, 9))
    
    style = ttk.Style()
    style.theme_use('default')
    style.configure(
        "TCombobox", 
        fieldbackground="#1e293b", 
        background="#0f172a", 
        foreground="white", 
        arrowcolor="white"
    )
    
    app = KioskApp(root)
    root.mainloop()