import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
import sys
import subprocess
import socket
import threading
from datetime import datetime
import psutil
import random
from PIL import Image, ImageTk

# Deteksi Font Family berdasarkan OS
FONT_FAMILY = "Segoe UI" if os.name == "nt" else "Helvetica"

class FlatProgressBar(tk.Canvas):
    def __init__(self, parent, width=105, height=5, bg_color="#1e293b", fill_color="#3b82f6", **kwargs):
        super().__init__(parent, width=width, height=height, bg="#1e293b", highlightthickness=0, bd=0, **kwargs)
        self.width = width
        self.height = height
        self.fill_color = fill_color
        self.bg_color = bg_color
        
        self.y = height / 2
        self.r = height / 2  # Radius untuk efek rounded cap
        
        self.bg_line = self.create_line(self.r, self.y, width - self.r, self.y, width=height, capstyle="round", fill=bg_color)
        self.fill_line = self.create_line(self.r, self.y, self.r, self.y, width=height, capstyle="round", fill=fill_color)
        
    def set_value(self, pct):
        pct = max(0, min(100, pct))
        if pct <= 0:
            self.coords(self.fill_line, self.r, self.y, self.r, self.y)
        else:
            val_w = self.r + ((pct / 100.0) * (self.width - 2 * self.r))
            self.coords(self.fill_line, self.r, self.y, val_w, self.y)

class CardButton(tk.Frame):
    def __init__(self, parent, icon, title, subtitle, bg_color, hover_color, command, **kwargs):
        super().__init__(parent, bg=bg_color, cursor="hand2", highlightthickness=1, highlightbackground="#334155", **kwargs)
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.command = command
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
        
        self.lbl_icon = tk.Label(self, text=icon, font=(FONT_FAMILY, 22), bg=bg_color, fg="white")
        self.lbl_icon.grid(row=1, column=0, pady=(8, 2))
        
        self.lbl_title = tk.Label(self, text=title, font=(FONT_FAMILY, 11, "bold"), bg=bg_color, fg="white")
        self.lbl_title.grid(row=2, column=0, pady=1)
        
        self.lbl_sub = tk.Label(self, text=subtitle, font=(FONT_FAMILY, 8), bg=bg_color, fg="#94a3b8")
        self.lbl_sub.grid(row=3, column=0, pady=(0, 8))
        
        for widget in (self, self.lbl_icon, self.lbl_title, self.lbl_sub):
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
            widget.bind("<Button-1>", self.on_click)
            
    def configure_button(self, icon=None, title=None, subtitle=None, bg_color=None, hover_color=None):
        if bg_color is not None:
            self.bg_color = bg_color
            self.configure(bg=bg_color)
            self.lbl_icon.configure(bg=bg_color)
            self.lbl_title.configure(bg=bg_color)
            self.lbl_sub.configure(bg=bg_color)
        if hover_color is not None:
            self.hover_color = hover_color
        if icon is not None:
            self.lbl_icon.configure(text=icon)
        if title is not None:
            self.lbl_title.configure(text=title)
        if subtitle is not None:
            self.lbl_sub.configure(text=subtitle)
            
    def on_enter(self, event):
        self.configure(bg=self.hover_color, highlightbackground=self.hover_color)
        self.lbl_icon.configure(bg=self.hover_color)
        self.lbl_title.configure(bg=self.hover_color)
        self.lbl_sub.configure(bg=self.hover_color)
        
    def on_leave(self, event):
        self.configure(bg=self.bg_color, highlightbackground="#334155")
        self.lbl_icon.configure(bg=self.bg_color)
        self.lbl_title.configure(bg=self.bg_color)
        self.lbl_sub.configure(bg=self.bg_color)
        
    def on_click(self, event):
        if self.command:
            self.command()

class KioskApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Kiosk Controller")
        
        # Setup screen geometry and fullscreen based on command line arguments
        if "--screen 2" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "--screen"):
            # Posisi monitor kedua dimulai dari koordinat X=1920 (lebar monitor pertama)
            # Menampilkan fullscreen di monitor kedua
            self.window.geometry("480x320+1920+0") 
            self.window.attributes('-fullscreen', True)
        else:
            # Jika mode single monitor (Hanya LCD 3.5 inci)
            self.window.geometry("480x320+0+0")
            self.window.attributes('-fullscreen', True)
            
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
        self.lbl_title.pack(side="left", padx=10, pady=5)

        self.ip_address = self.get_ip_address()
        self.lbl_ip = tk.Label(
            self.header,
            text=f"IP: {self.ip_address}",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#1e293b",
            fg="#94a3b8"
        )
        self.lbl_ip.pack(side="left", padx=15, pady=5)

        self.lbl_clock = tk.Label(
            self.header,
            font=(FONT_FAMILY, 9, "bold"),
            bg="#1e293b",
            fg="#38bdf8"
        )
        self.lbl_clock.pack(side="right", padx=10, pady=5)
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
            subtitle="Jaringan Jarak Jauh",
            bg_color="#6d28d9",
            hover_color="#5b21b6",
            command=self.show_wifi_dialog
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

        # ------------------- SCREENSAVER CONFIGURATIONS -------------------
        self.screensaver_active = False
        self.ss_timer_job = None
        self.ss_anim_job = None
        
        # Bind global input events to reset screensaver timer
        self.window.bind_all("<Any-KeyPress>", self.reset_screensaver_timer)
        self.window.bind_all("<Any-Button>", self.reset_screensaver_timer)
        self.window.bind_all("<Motion>", self.reset_screensaver_timer)
        
        # Start the initial screensaver idle timer
        self.reset_screensaver_timer()

    def update_clock(self):
        now = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
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
                capacity, voltage = self.get_x1202_battery_percentage()
                if capacity is not None:
                    self.lbl_battery.configure(text=f"Bat: {capacity:.1f}% ({voltage:.2f}V) 🔋")
                    self.bar_battery.set_value(int(capacity))
                else:
                    self.lbl_battery.configure(text="Bat: AC 🔌")
                    self.bar_battery.set_value(100)
        except Exception as e:
            print(f"Error updating stats: {e}")
            
        self.window.after(3000, self.update_stats)

    def get_x1202_battery_percentage(self):
        try:
            import smbus2
            import time
            bus = smbus2.SMBus(1)
            address = 0x36

            # Kirim QuickStart hanya sekali saat pertama kali dibaca
            if not getattr(self, '_x1202_initialized', False):
                # Register MODE (0x06), tulis 0x4000 = QuickStart command
                bus.write_word_data(address, 0x06, 0x0040)
                time.sleep(0.2)  # Tunggu chip reset dan kalkulasi ulang
                self._x1202_initialized = True

            # Baca register VCELL (0x02): voltase baterai
            # Chip mengirim 2 byte big-endian: byte[0]=MSB, byte[1]=LSB
            volt_data = bus.read_i2c_block_data(address, 0x02, 2)
            raw_volt = (volt_data[0] << 4) | (volt_data[1] >> 4)
            voltage = raw_volt * 1.25 / 1000.0

            # Baca register SOC (0x04): state of charge (persen baterai)
            # Chip mengirim 2 byte: byte[0]=bagian integer, byte[1]=bagian desimal/256
            soc_data = bus.read_i2c_block_data(address, 0x04, 2)
            capacity = soc_data[0] + soc_data[1] / 256.0
            capacity = max(0.0, min(100.0, capacity))

            bus.close()
            return capacity, voltage
        except Exception as e:
            print(f"[X1202] Error baca baterai: {e}")
            return None, None

    def get_ip_address(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Offline / 127.0.0.1"

    def exit_app(self):
        if messagebox.askokcancel("Keluar Kiosk", "Apakah Anda yakin ingin menutup aplikasi Kiosk?"):
            self.window.destroy()

    def _get_linux_terminal(self):
        import shutil
        for term in ["x-terminal-emulator", "lxterminal", "xterm", "xfce4-terminal", "gnome-terminal", "konsole"]:
            if shutil.which(term):
                return term
        return None

    def switch_to_tty1(self):
        try:
            if os.name == 'nt':
                # Windows fallback: buka cmd
                subprocess.Popen(["cmd.exe"])
            else:
                # Buka terminal emulator dalam mode fullscreen (seperti CLI murni TTY)
                term = self._get_linux_terminal()
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

    # ------------------- SSH MANAGEMENT -------------------
    def get_ssh_status(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.15)
            result = s.connect_ex(("127.0.0.1", 22))
            s.close()
            return result == 0
        except Exception:
            return False

    def update_ssh_button(self):
        is_active = self.get_ssh_status()
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
        current_active = self.get_ssh_status()
        action_name = "MEMATIKAN" if current_active else "MENGAKTIFKAN"
        if messagebox.askyesno("SSH System", f"Apakah Anda yakin ingin {action_name} SSH server?"):
            self.toggle_ssh(current_active)

    def toggle_ssh(self, current_active):
        try:
            if os.name == 'nt':
                cmd = "Stop-Service sshd" if current_active else "Start-Service sshd"
                subprocess.Popen(["powershell", "-Command", f"Start-Process powershell -ArgumentList '-Command {cmd}' -Verb RunAs"])
            else:
                cmd = ["sudo", "systemctl", "stop", "ssh"] if current_active else ["sudo", "systemctl", "enable", "--now", "ssh"]
                subprocess.run(cmd, check=True)
            self.window.after(1200, self.update_ssh_button)
        except Exception as e:
            messagebox.showerror("Error SSH", f"Gagal mengontrol SSH: {e}")

    def switch_to_tty2(self):
        try:
            if os.name == 'nt':
                # Windows fallback: buka cmd running btop if possible
                subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe", "/k", "btop -p 1"])
            else:
                # Buka BTOP monitor secara fullscreen menggunakan terminal emulator
                term = self._get_linux_terminal()
                if term:
                    if term == "lxterminal":
                        subprocess.Popen([term, "--fullscreen", "-e", "btop"])
                    elif term == "xterm":
                        subprocess.Popen([term, "-fullscreen", "-e", "btop"])
                    elif term == "xfce4-terminal":
                        subprocess.Popen([term, "--fullscreen", "-e", "btop"])
                    elif term == "gnome-terminal":
                        subprocess.Popen([term, "--fullscreen", "--", "btop"])
                    elif term == "konsole":
                        subprocess.Popen([term, "--fullscreen", "-e", "btop"])
                    else:
                        subprocess.Popen([term, "-e", "btop"])
                else:
                    messagebox.showerror(
                        "Terminal Tidak Ditemukan", 
                        "Tidak ada terminal emulator untuk menjalankan btop."
                    )
        except Exception as e:
            messagebox.showerror("Error TTY2", f"Gagal membuka BTOP: {e}")

    # ------------------- WI-FI CONNECTION DIALOG -------------------
    def close_wifi_dialog(self):
        try:
            self.wifi_dialog.destroy()
        except Exception:
            pass
        self.reset_screensaver_timer()

    def show_wifi_dialog(self):
        # Batalkan timer screensaver agar tidak aktif saat dialog WiFi terbuka
        if hasattr(self, "ss_timer_job") and self.ss_timer_job:
            self.window.after_cancel(self.ss_timer_job)
            self.ss_timer_job = None
        if hasattr(self, "ss_blank_job") and self.ss_blank_job:
            self.window.after_cancel(self.ss_blank_job)
            self.ss_blank_job = None

        self.wifi_dialog = tk.Toplevel(self.window)
        self.wifi_dialog.title("Setup Jaringan Wi-Fi")
        self.wifi_dialog.configure(bg="#0f172a")
        self.wifi_dialog.resizable(False, False)
        
        # Center the dialog on screen
        width = 380
        height = 250
        self.window.update_idletasks()
        parent_x = self.window.winfo_x()
        parent_y = self.window.winfo_y()
        parent_w = self.window.winfo_width()
        parent_h = self.window.winfo_height()
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        self.wifi_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        self.wifi_dialog.transient(self.window)
        self.wifi_dialog.grab_set()
        self.wifi_dialog.protocol("WM_DELETE_WINDOW", self.close_wifi_dialog)

        lbl = tk.Label(
            self.wifi_dialog, 
            text="📶 SETUP WI-FI KIOSK", 
            font=(FONT_FAMILY, 11, "bold"), 
            bg="#0f172a", fg="#f8fafc"
        )
        lbl.pack(pady=(15, 8))

        form_frame = tk.Frame(self.wifi_dialog, bg="#0f172a")
        form_frame.pack(fill="both", expand=True, padx=24)

        lbl_ssid = tk.Label(form_frame, text="Pilih WiFi (SSID):", font=(FONT_FAMILY, 9, "bold"), bg="#0f172a", fg="#94a3b8")
        lbl_ssid.grid(row=0, column=0, sticky="w", pady=4)

        self.combo_ssid = ttk.Combobox(form_frame, font=(FONT_FAMILY, 9), width=22)
        self.combo_ssid.grid(row=0, column=1, sticky="w", pady=4, padx=5)
        self.combo_ssid.set("Mencari jaringan...")

        lbl_pass = tk.Label(form_frame, text="Password:", font=(FONT_FAMILY, 9, "bold"), bg="#0f172a", fg="#94a3b8")
        lbl_pass.grid(row=1, column=0, sticky="w", pady=4)

        self.entry_pass = tk.Entry(
            form_frame, 
            font=(FONT_FAMILY, 9), 
            show="*", 
            width=24, 
            bg="#1e293b", 
            fg="white", 
            insertbackground="white",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground="#334155",
            highlightcolor="#38bdf8"
        )
        self.entry_pass.grid(row=1, column=1, sticky="w", pady=4, padx=5)

        self.show_pass_var = tk.BooleanVar(value=False)
        chk_show = tk.Checkbutton(
            form_frame, 
            text="Tampilkan Password", 
            variable=self.show_pass_var,
            onvalue=True, offvalue=False,
            font=(FONT_FAMILY, 8),
            bg="#0f172a", fg="#64748b",
            activebackground="#0f172a", activeforeground="white",
            selectcolor="#1e293b", bd=0,
            command=self.toggle_password_visibility
        )
        chk_show.grid(row=2, column=1, sticky="w", pady=2, padx=5)

        btn_frame = tk.Frame(self.wifi_dialog, bg="#0f172a")
        btn_frame.pack(fill="x", side="bottom", pady=15, padx=24)

        self.btn_connect = tk.Button(
            btn_frame,
            text="Hubungkan",
            font=(FONT_FAMILY, 10, "bold"),
            bg="#10b981", fg="white",
            activebackground="#059669", activeforeground="white",
            relief="flat", bd=0, height=2,
            command=self.connect_wifi_action
        )
        self.btn_connect.pack(side="left", fill="x", expand=True, padx=5)
        self.btn_connect.bind("<Enter>", lambda e: self.btn_connect.configure(bg="#059669"))
        self.btn_connect.bind("<Leave>", lambda e: self.btn_connect.configure(bg="#10b981"))

        btn_cancel = tk.Button(
            btn_frame,
            text="Batal",
            font=(FONT_FAMILY, 10),
            bg="#475569", fg="white",
            activebackground="#334155", activeforeground="white",
            relief="flat", bd=0, height=2,
            command=self.close_wifi_dialog
        )
        btn_cancel.pack(side="right", fill="x", expand=True, padx=5)
        btn_cancel.bind("<Enter>", lambda e: btn_cancel.configure(bg="#334155"))
        btn_cancel.bind("<Leave>", lambda e: btn_cancel.configure(bg="#475569"))

        threading.Thread(target=self.scan_wifi_async, daemon=True).start()

    def toggle_password_visibility(self):
        if self.show_pass_var.get():
            self.entry_pass.configure(show="")
        else:
            self.entry_pass.configure(show="*")

    def scan_wifi_async(self):
        networks = []
        try:
            if os.name == 'nt':
                out = subprocess.check_output(["netsh", "wlan", "show", "networks"], text=True, errors='ignore')
                for line in out.splitlines():
                    if "SSID" in line and not "BSSID" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            ssid = parts[1].strip()
                            if ssid:
                                networks.append(ssid)
            else:
                out = subprocess.check_output(["nmcli", "-t", "-f", "SSID", "dev", "wifi"], text=True, errors='ignore')
                for line in out.splitlines():
                    ssid = line.strip()
                    if ssid and ssid not in networks:
                        networks.append(ssid)
        except Exception:
            pass

        networks = sorted(list(set(networks)))
        if not networks:
            networks = ["Gagal mencari wifi (Refresh)"]

        self.window.after(0, lambda: self.update_combo_networks(networks))

    def update_combo_networks(self, networks):
        try:
            self.combo_ssid['values'] = networks
            if networks:
                self.combo_ssid.set(networks[0])
            else:
                self.combo_ssid.set("Tidak ada WiFi ditemukan")
        except Exception:
            pass

    def connect_wifi_action(self):
        wifi_name = self.combo_ssid.get()
        wifi_pass = self.entry_pass.get()

        if not wifi_name or wifi_name == "Mencari jaringan..." or wifi_name == "Gagal mencari wifi (Refresh)":
            messagebox.showwarning("WiFi Setup", "Silakan pilih nama WiFi yang valid!")
            return

        self.btn_connect.configure(text="Menghubungkan...", state="disabled", bg="#059669")
        threading.Thread(target=self.connect_wifi_thread, args=(wifi_name, wifi_pass), daemon=True).start()

    def connect_wifi_thread(self, ssid, password):
        success = False
        try:
            if os.name == 'nt':
                success = True
            else:
                cmd = f"nmcli device wifi connect '{ssid}' password '{password}'"
                exit_code = os.system(cmd)
                success = (exit_code == 0)
        except Exception:
            success = False

        self.window.after(0, lambda: self.connect_wifi_finish(success, ssid))

    def connect_wifi_finish(self, success, ssid):
        try:
            self.btn_connect.configure(text="Hubungkan", state="normal", bg="#10b981")
            if success:
                self.ip_address = self.get_ip_address()
                self.lbl_ip.configure(text=f"IP: {self.ip_address}")
                messagebox.showinfo("Sukses WiFi", f"Berhasil terhubung ke Wi-Fi: {ssid}!")
                self.close_wifi_dialog()
            else:
                messagebox.showerror("Gagal WiFi", f"Gagal menghubungkan ke Wi-Fi: {ssid}. Silakan periksa kembali password Anda.")
        except Exception:
            pass

    # ------------------- SCREENSAVER LOGIC -------------------
    def reset_screensaver_timer(self, event=None):
        # Jika screensaver sedang aktif, tidak perlu mereset timer
        if hasattr(self, "screensaver_active") and self.screensaver_active:
            return
            
        # Batalkan job timer screensaver sebelumnya jika ada
        if hasattr(self, "ss_timer_job") and self.ss_timer_job:
            self.window.after_cancel(self.ss_timer_job)
            self.ss_timer_job = None
            
        if hasattr(self, "ss_blank_job") and self.ss_blank_job:
            self.window.after_cancel(self.ss_blank_job)
            self.ss_blank_job = None
            
        # Jadwalkan kemunculan screensaver setelah 60 detik (60000 milidetik) idle
        self.ss_timer_job = self.window.after(60000, self.show_screensaver)
        # Jadwalkan kemunculan layar blank hitam setelah 5 menit (300000 milidetik) idle
        self.ss_blank_job = self.window.after(300000, self.show_blank_screensaver)

    def show_screensaver(self):
        self.screensaver_active = True
        
        # Buat overlay Frame hitam penuh jika belum ada
        if not hasattr(self, "ss_frame") or not self.ss_frame or not self.ss_frame.winfo_exists():
            self.ss_frame = tk.Frame(self.window, bg="#020617")
            self.ss_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            
            # Label untuk menampilkan gambar
            self.ss_image_label = tk.Label(self.ss_frame, bg="#020617")
            self.ss_image_label.pack(fill="both", expand=True)
            
            # Deteksi mouse untuk mencegah dismiss langsung akibat jitter kecil
            self.ss_mouse_x = None
            self.ss_mouse_y = None
            
            # Bind event untuk keluar dari screensaver
            for widget in (self.ss_frame, self.ss_image_label):
                widget.bind("<Button-1>", lambda e: self.hide_screensaver())
                widget.bind("<Key>", lambda e: self.hide_screensaver())
                widget.bind("<Motion>", self.on_screensaver_motion)
            
        # Tampilkan gambar pertama dan jalankan rotasi otomatis
        self.rotate_screensaver_image()

    def show_blank_screensaver(self):
        self.screensaver_active = True
        
        # Hentikan rotasi gambar
        if hasattr(self, "ss_anim_job") and self.ss_anim_job:
            self.window.after_cancel(self.ss_anim_job)
            self.ss_anim_job = None
            
        # Buat/ubah overlay Frame menjadi hitam penuh tanpa gambar
        if not hasattr(self, "ss_frame") or not self.ss_frame or not self.ss_frame.winfo_exists():
            self.ss_frame = tk.Frame(self.window, bg="#000000")
            self.ss_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            
            self.ss_image_label = tk.Label(self.ss_frame, bg="#000000")
            self.ss_image_label.pack(fill="both", expand=True)
            
            self.ss_mouse_x = None
            self.ss_mouse_y = None
            
            for widget in (self.ss_frame, self.ss_image_label):
                widget.bind("<Button-1>", lambda e: self.hide_screensaver())
                widget.bind("<Key>", lambda e: self.hide_screensaver())
                widget.bind("<Motion>", self.on_screensaver_motion)
        else:
            self.ss_frame.configure(bg="#000000")
            self.ss_image_label.configure(image="", bg="#000000")

    def on_screensaver_motion(self, event):
        # Mencegah jitter pointer langsung menutup screensaver
        if self.ss_mouse_x is None or self.ss_mouse_y is None:
            self.ss_mouse_x = event.x
            self.ss_mouse_y = event.y
        else:
            dx = abs(event.x - self.ss_mouse_x)
            dy = abs(event.y - self.ss_mouse_y)
            if dx > 12 or dy > 12:  # Toleransi gerakan pointer 12px
                self.hide_screensaver()

    def rotate_screensaver_image(self):
        if not hasattr(self, "screensaver_active") or not self.screensaver_active:
            return
            
        # Dapatkan direktori tempat script ini berada
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Cari file .jpg di direktori script
        jpg_files = [os.path.join(script_dir, f) for f in os.listdir(script_dir) if f.lower().endswith('.jpg') or f.lower().endswith('.jpeg')]
        
        if jpg_files:
            chosen_img = random.choice(jpg_files)
            try:
                # Dapatkan ukuran layar aktual
                w = self.window.winfo_width()
                h = self.window.winfo_height()
                if w < 10: w = 480
                if h < 10: h = 320
                
                # Load dan resize gambar agar pas di layar
                img = Image.open(chosen_img)
                img = img.resize((w, h), Image.Resampling.LANCZOS)
                self.ss_photo = ImageTk.PhotoImage(img)
                self.ss_image_label.configure(image=self.ss_photo)
            except Exception as e:
                print(f"Error loading screensaver image: {e}")
                
        # Rotasi gambar berikutnya setiap 8 detik (8000 milidetik)
        self.ss_anim_job = self.window.after(8000, self.rotate_screensaver_image)

    def hide_screensaver(self):
        self.screensaver_active = False
        
        # Batalkan loop rotasi gambar
        if hasattr(self, "ss_anim_job") and self.ss_anim_job:
            self.window.after_cancel(self.ss_anim_job)
            self.ss_anim_job = None
            
        # Batalkan job timer screensaver lainnya jika ada
        if hasattr(self, "ss_timer_job") and self.ss_timer_job:
            self.window.after_cancel(self.ss_timer_job)
            self.ss_timer_job = None
            
        if hasattr(self, "ss_blank_job") and self.ss_blank_job:
            self.window.after_cancel(self.ss_blank_job)
            self.ss_blank_job = None
            
        # Tutup frame overlay screensaver
        if hasattr(self, "ss_frame") and self.ss_frame:
            try:
                self.ss_frame.destroy()
            except Exception:
                pass
            self.ss_frame = None
            
        # Reset ulang timer idle
        self.reset_screensaver_timer()

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