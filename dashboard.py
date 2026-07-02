import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
import subprocess
import socket
import threading
from datetime import datetime
import psutil

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
        super().__init__(parent, bg=bg_color, cursor="hand2", **kwargs)
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.command = command
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=1)
        
        self.lbl_icon = tk.Label(self, text=icon, font=(FONT_FAMILY, 20), bg=bg_color, fg="white")
        self.lbl_icon.grid(row=1, column=0, pady=(10, 2))
        
        self.lbl_title = tk.Label(self, text=title, font=(FONT_FAMILY, 10, "bold"), bg=bg_color, fg="white")
        self.lbl_title.grid(row=2, column=0, pady=1)
        
        self.lbl_sub = tk.Label(self, text=subtitle, font=(FONT_FAMILY, 8), bg=bg_color, fg="#94a3b8")
        self.lbl_sub.grid(row=3, column=0, pady=(0, 10))
        
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
        self.configure(bg=self.hover_color)
        self.lbl_icon.configure(bg=self.hover_color)
        self.lbl_title.configure(bg=self.hover_color)
        self.lbl_sub.configure(bg=self.hover_color)
        
    def on_leave(self, event):
        self.configure(bg=self.bg_color)
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
        
        # Fullscreen
        self.window.attributes('-fullscreen', True)
        self.window.configure(bg="#0f172a") # Dark Slate 900

        self.window.bind('<q>', lambda e: self.exit_app())

        # Main Layout Grid
        self.window.grid_rowconfigure(0, weight=0)
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_rowconfigure(2, weight=0)
        self.window.grid_columnconfigure(0, weight=1)

        # ------------------- HEADER FRAME -------------------
        self.header = tk.Frame(window, bg="#1e293b", height=45)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        self.lbl_title = tk.Label(
            self.header, 
            text="⚙️ KIOSK CONTROLLER", 
            font=(FONT_FAMILY, 12, "bold"), 
            bg="#1e293b", 
            fg="#f8fafc"
        )
        self.lbl_title.pack(side="left", padx=15, pady=10)

        self.btn_exit = tk.Button(
            self.header,
            text="✕",
            font=(FONT_FAMILY, 11, "bold"),
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=12,
            command=self.exit_app
        )
        self.btn_exit.pack(side="right", padx=15, pady=8)
        self.btn_exit.bind("<Enter>", lambda e: self.btn_exit.configure(bg="#dc2626"))
        self.btn_exit.bind("<Leave>", lambda e: self.btn_exit.configure(bg="#ef4444"))

        self.lbl_clock = tk.Label(
            self.header,
            font=(FONT_FAMILY, 11, "bold"),
            bg="#1e293b",
            fg="#38bdf8"
        )
        self.lbl_clock.pack(side="right", padx=10, pady=10)
        self.update_clock()

        # ------------------- CONTENT FRAME -------------------
        self.content = tk.Frame(window, bg="#0f172a")
        self.content.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=3)

        # ------------------- LEFT PANEL: SYSTEM STATS -------------------
        self.left_panel = tk.Frame(self.content, bg="#1e293b", bd=0)
        self.left_panel.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        self.left_panel.grid_columnconfigure(0, weight=1)
        
        self.lbl_stats_title = tk.Label(
            self.left_panel,
            text="📊 STATISTIK SISTEM",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#1e293b",
            fg="#94a3b8"
        )
        self.lbl_stats_title.pack(anchor="w", padx=10, pady=(10, 4))

        divider = tk.Frame(self.left_panel, bg="#334155", height=1)
        divider.pack(fill="x", padx=10, pady=(0, 6))

        self.stats_container = tk.Frame(self.left_panel, bg="#1e293b")
        self.stats_container.pack(fill="both", expand=True, padx=10, pady=0)

        # CPU Row
        self.frame_cpu = tk.Frame(self.stats_container, bg="#1e293b")
        self.frame_cpu.pack(fill="x", pady=1)
        self.lbl_cpu = tk.Label(self.frame_cpu, text="CPU: 0%", font=(FONT_FAMILY, 8, "bold"), bg="#1e293b", fg="#f1f5f9")
        self.lbl_cpu.pack(anchor="w")
        self.bar_cpu = FlatProgressBar(self.frame_cpu, width=105, height=5, fill_color="#3b82f6")
        self.bar_cpu.pack(anchor="w", pady=(1, 2))

        # RAM Row
        self.frame_ram = tk.Frame(self.stats_container, bg="#1e293b")
        self.frame_ram.pack(fill="x", pady=1)
        self.lbl_ram = tk.Label(self.frame_ram, text="RAM: 0%", font=(FONT_FAMILY, 8, "bold"), bg="#1e293b", fg="#f1f5f9")
        self.lbl_ram.pack(anchor="w")
        self.bar_ram = FlatProgressBar(self.frame_ram, width=105, height=5, fill_color="#a855f7")
        self.bar_ram.pack(anchor="w", pady=(1, 2))

        # Storage Row
        self.frame_disk = tk.Frame(self.stats_container, bg="#1e293b")
        self.frame_disk.pack(fill="x", pady=1)
        self.lbl_disk = tk.Label(self.frame_disk, text="Disk: 0%", font=(FONT_FAMILY, 8, "bold"), bg="#1e293b", fg="#f1f5f9")
        self.lbl_disk.pack(anchor="w")
        self.bar_disk = FlatProgressBar(self.frame_disk, width=105, height=5, fill_color="#eab308")
        self.bar_disk.pack(anchor="w", pady=(1, 2))

        # Temp & Battery Row
        self.frame_other = tk.Frame(self.stats_container, bg="#1e293b")
        self.frame_other.pack(fill="x", pady=(3, 0))
        
        self.lbl_temp = tk.Label(self.frame_other, text="🌡️ Suhu: N/A", font=(FONT_FAMILY, 8, "bold"), bg="#1e293b", fg="#f43f5e")
        self.lbl_temp.pack(anchor="w", pady=1)

        self.lbl_battery = tk.Label(self.frame_other, text="🔋 Baterai: N/A", font=(FONT_FAMILY, 8, "bold"), bg="#1e293b", fg="#10b981")
        self.lbl_battery.pack(anchor="w", pady=1)
        self.bar_battery = FlatProgressBar(self.frame_other, width=105, height=5, fill_color="#10b981")
        self.bar_battery.pack(anchor="w", pady=(1, 2))

        self.update_stats()

        # ------------------- RIGHT PANEL: ACTIONS -------------------
        self.right_panel = tk.Frame(self.content, bg="#0f172a")
        self.right_panel.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(1, weight=1)

        # CardButton 1: Terminal
        self.btn_terminal = CardButton(
            self.right_panel, 
            icon="💻", 
            title="TERMINAL", 
            subtitle="Buka Bash CLI",
            bg_color="#0284c7",
            hover_color="#0369a1",
            command=self.buka_terminal
        )
        self.btn_terminal.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        # CardButton 2: Wi-Fi Setup
        self.btn_wifi = CardButton(
            self.right_panel, 
            icon="📶", 
            title="WIFI SETUP", 
            subtitle="Jaringan Jarak Jauh",
            bg_color="#6d28d9",
            hover_color="#5b21b6",
            command=self.show_wifi_dialog
        )
        self.btn_wifi.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        # CardButton 3: SSH Control
        self.btn_ssh = CardButton(
            self.right_panel, 
            icon="🔑", 
            title="SSH SYSTEM", 
            subtitle="Memeriksa...",
            bg_color="#475569", 
            hover_color="#334155",
            command=self.confirm_toggle_ssh
        )
        self.btn_ssh.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")
        self.update_ssh_button_loop()

        # CardButton 4: System Control
        self.btn_system = CardButton(
            self.right_panel, 
            icon="⚙️", 
            title="SYSTEM DAYA", 
            subtitle="Reboot/Shutdown",
            bg_color="#d97706",
            hover_color="#b45309",
            command=self.show_system_dialog
        )
        self.btn_system.grid(row=1, column=1, padx=6, pady=6, sticky="nsew")

        # ------------------- FOOTER FRAME -------------------
        self.footer = tk.Frame(window, bg="#1e293b", height=25)
        self.footer.grid(row=2, column=0, sticky="ew")
        self.footer.grid_propagate(False)

        # Info IP Address
        self.ip_address = self.get_ip_address()
        self.lbl_ip = tk.Label(
            self.footer, 
            text=f"IP Address: {self.ip_address}  |  Tekan 'q' atau klik '✕' untuk Keluar Kiosk", 
            font=(FONT_FAMILY, 8, "bold"), 
            bg="#1e293b", 
            fg="#94a3b8"
        )
        self.lbl_ip.pack(side="left", padx=15, pady=3)

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
            temp_str = "🌡️ Suhu: N/A"
            if os.name != 'nt':
                try:
                    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                        temp_c = int(f.read()) / 1000.0
                        temp_str = f"🌡️ Suhu: {temp_c:.1f} °C"
                except Exception:
                    pass
            self.lbl_temp.configure(text=temp_str)

            # Battery
            battery = psutil.sensors_battery()
            if battery:
                plugged = "Dicas" if battery.power_plugged else "Baterai"
                self.lbl_battery.configure(text=f"🔋 Baterai: {battery.percent}% ({plugged})")
                self.bar_battery.set_value(battery.percent)
            else:
                self.lbl_battery.configure(text="🔋 Baterai: AC Power")
                self.bar_battery.set_value(100)
        except Exception as e:
            print(f"Error updating stats: {e}")
            
        self.window.after(3000, self.update_stats)

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

    def buka_terminal(self):
        try:
            if os.name == 'nt':
                subprocess.Popen(["cmd.exe"])
            else:
                subprocess.Popen(["lxterminal"])
        except Exception as e:
            messagebox.showerror("Error CLI", f"Gagal membuka terminal: {e}")

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

    # ------------------- SYSTEM DAYA CONTROL -------------------
    def show_system_dialog(self):
        self.sys_dialog = tk.Toplevel(self.window)
        self.sys_dialog.title("Kontrol Sistem")
        self.sys_dialog.geometry("320x180")
        self.sys_dialog.configure(bg="#0f172a")
        self.sys_dialog.resizable(False, False)
        
        self.sys_dialog.transient(self.window)
        self.sys_dialog.grab_set()

        lbl = tk.Label(
            self.sys_dialog, 
            text="⚙️ KONTROL SISTEM", 
            font=(FONT_FAMILY, 12, "bold"), 
            bg="#0f172a", fg="#f8fafc"
        )
        lbl.pack(pady=18)

        btn_frame = tk.Frame(self.sys_dialog, bg="#0f172a")
        btn_frame.pack(fill="x", padx=20)

        btn_reboot = tk.Button(
            btn_frame,
            text="🔄 REBOOT",
            font=(FONT_FAMILY, 10, "bold"),
            bg="#3b82f6", fg="white",
            activebackground="#2563eb", activeforeground="white",
            relief="flat", bd=0, height=2,
            command=self.sys_reboot
        )
        btn_reboot.pack(side="left", fill="x", expand=True, padx=5)
        btn_reboot.bind("<Enter>", lambda e: btn_reboot.configure(bg="#2563eb"))
        btn_reboot.bind("<Leave>", lambda e: btn_reboot.configure(bg="#3b82f6"))

        btn_shutdown = tk.Button(
            btn_frame,
            text="🛑 SHUTDOWN",
            font=(FONT_FAMILY, 10, "bold"),
            bg="#ef4444", fg="white",
            activebackground="#dc2626", activeforeground="white",
            relief="flat", bd=0, height=2,
            command=self.sys_shutdown
        )
        btn_shutdown.pack(side="right", fill="x", expand=True, padx=5)
        btn_shutdown.bind("<Enter>", lambda e: btn_shutdown.configure(bg="#dc2626"))
        btn_shutdown.bind("<Leave>", lambda e: btn_shutdown.configure(bg="#ef4444"))

        btn_cancel = tk.Button(
            self.sys_dialog,
            text="Batal",
            font=(FONT_FAMILY, 9),
            bg="#475569", fg="white",
            activebackground="#334155", activeforeground="white",
            relief="flat", bd=0,
            command=self.sys_dialog.destroy
        )
        btn_cancel.pack(pady=15, side="bottom")
        btn_cancel.bind("<Enter>", lambda e: btn_cancel.configure(bg="#334155"))
        btn_cancel.bind("<Leave>", lambda e: btn_cancel.configure(bg="#475569"))

    def sys_reboot(self):
        if messagebox.askyesno("Reboot Sistem", "Sistem akan segera dijalankan ulang. Lanjutkan?"):
            self.sys_dialog.destroy()
            try:
                if os.name == 'nt':
                    subprocess.run(["shutdown", "/r", "/t", "0"])
                else:
                    subprocess.run(["sudo", "reboot"])
            except Exception as e:
                messagebox.showerror("Error", f"Gagal reboot: {e}")

    def sys_shutdown(self):
        if messagebox.askyesno("Shutdown Sistem", "Sistem akan segera dimatikan. Lanjutkan?"):
            self.sys_dialog.destroy()
            try:
                if os.name == 'nt':
                    subprocess.run(["shutdown", "/s", "/t", "0"])
                else:
                    subprocess.run(["sudo", "poweroff"])
            except Exception as e:
                messagebox.showerror("Error", f"Gagal shutdown: {e}")

    # ------------------- WI-FI CONNECTION DIALOG -------------------
    def show_wifi_dialog(self):
        self.wifi_dialog = tk.Toplevel(self.window)
        self.wifi_dialog.title("Setup Jaringan Wi-Fi")
        self.wifi_dialog.geometry("380x250")
        self.wifi_dialog.configure(bg="#0f172a")
        self.wifi_dialog.resizable(False, False)
        
        self.wifi_dialog.transient(self.window)
        self.wifi_dialog.grab_set()

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
            command=self.wifi_dialog.destroy
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
                self.lbl_ip.configure(text=f"IP Address: {self.ip_address}  |  Tekan 'q' atau klik '✕' untuk Keluar Kiosk")
                messagebox.showinfo("Sukses WiFi", f"Berhasil terhubung ke Wi-Fi: {ssid}!")
                self.wifi_dialog.destroy()
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
            
        # Jadwalkan kemunculan screensaver setelah 10 detik (10000 milidetik) idle
        self.ss_timer_job = self.window.after(10000, self.show_screensaver)

    def show_screensaver(self):
        self.screensaver_active = True
        
        # Buat overlay Frame hitam penuh
        self.ss_frame = tk.Frame(self.window, bg="#020617")
        self.ss_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        
        # Canvas tempat merender jam melantun
        self.ss_canvas = tk.Canvas(self.ss_frame, bg="#020617", highlightthickness=0)
        self.ss_canvas.pack(fill="both", expand=True)
        
        # Teks Jam Utama
        self.ss_time_text = self.ss_canvas.create_text(
            150, 100, 
            text="12:00:00", 
            font=(FONT_FAMILY, 28, "bold"), 
            fill="#38bdf8", 
            anchor="center"
        )
        
        # Teks Tanggal di bawah jam
        self.ss_date_text = self.ss_canvas.create_text(
            150, 135, 
            text="Kamis, 02 Juli 2026", 
            font=(FONT_FAMILY, 12), 
            fill="#64748b", 
            anchor="center"
        )
        
        # Teks petunjuk sentuh layar
        self.ss_hint_text = self.ss_canvas.create_text(
            240, 295, 
            text="Sentuh layar untuk kembali", 
            font=(FONT_FAMILY, 9), 
            fill="#334155", 
            anchor="center"
        )
        
        # Parameter gerak / bounce screensaver (kecepatan awal x, y)
        self.ss_dx = 1.5
        self.ss_dy = 1.5
        
        # Deteksi mouse untuk mencegah dismiss langsung akibat jitter kecil
        self.ss_mouse_x = None
        self.ss_mouse_y = None
        
        # Bind event untuk keluar dari screensaver
        self.ss_canvas.bind("<Button-1>", lambda e: self.hide_screensaver())
        self.ss_canvas.bind("<Key>", lambda e: self.hide_screensaver())
        self.ss_canvas.bind("<Motion>", self.on_screensaver_motion)
        
        # Mulai animasi gerak jam
        self.animate_screensaver()

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

    def animate_screensaver(self):
        if not hasattr(self, "screensaver_active") or not self.screensaver_active:
            return
            
        w = self.ss_canvas.winfo_width()
        h = self.ss_canvas.winfo_height()
        
        # Fallback ukuran default jika winfo belum siap merender resolusi aktual
        if w < 10: w = 480
        if h < 10: h = 320
            
        # Update teks jam & tanggal terbaru
        now_t = datetime.now().strftime("%H:%M:%S")
        now_d = datetime.now().strftime("%d-%m-%Y")
        
        self.ss_canvas.itemconfig(self.ss_time_text, text=now_t)
        self.ss_canvas.itemconfig(self.ss_date_text, text=now_d)
        
        # Dapatkan batas-batas koordinat box teks gabungan jam + tanggal
        bbox_t = self.ss_canvas.bbox(self.ss_time_text)
        bbox_d = self.ss_canvas.bbox(self.ss_date_text)
        
        if bbox_t and bbox_d:
            x1 = min(bbox_t[0], bbox_d[0])
            y1 = min(bbox_t[1], bbox_d[1])
            x2 = max(bbox_t[2], bbox_d[2])
            y2 = max(bbox_t[3], bbox_d[3])
            
            # Deteksi tabrakan dengan batas layar (bouncing)
            if x1 + self.ss_dx <= 10 or x2 + self.ss_dx >= w - 10:
                self.ss_dx = -self.ss_dx
            if y1 + self.ss_dy <= 10 or y2 + self.ss_dy >= h - 35:
                self.ss_dy = -self.ss_dy
                
            # Gerakkan objek teks jam & tanggal
            self.ss_canvas.move(self.ss_time_text, self.ss_dx, self.ss_dy)
            self.ss_canvas.move(self.ss_date_text, self.ss_dx, self.ss_dy)
            
        # Ulangi animasi setiap 40 milidetik (~25 FPS)
        self.ss_anim_job = self.window.after(40, self.animate_screensaver)

    def hide_screensaver(self):
        self.screensaver_active = False
        
        # Batalkan loop animasi jam
        if hasattr(self, "ss_anim_job") and self.ss_anim_job:
            self.window.after_cancel(self.ss_anim_job)
            
        # Tutup frame overlay screensaver
        if hasattr(self, "ss_frame") and self.ss_frame:
            self.ss_frame.destroy()
            
        # Reset ulang timer idle 1 menit baru
        self.reset_screensaver_timer()

# Menjalankan aplikasi
if __name__ == "__main__":
    root = tk.Tk()
    
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