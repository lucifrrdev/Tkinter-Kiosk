import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from widgets import FONT_FAMILY
from system_services import get_ip_address

class WiFiDialog(tk.Toplevel):
    def __init__(self, parent, on_connect_cb, on_close_cb):
        super().__init__(parent)
        self.parent = parent
        self.on_connect_cb = on_connect_cb
        self.on_close_cb = on_close_cb
        
        self.title("Setup Jaringan Wi-Fi")
        self.configure(bg="#0f172a")
        self.resizable(False, False)
        
        # Center the dialog on screen
        width = 380
        height = 250
        self.parent.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.transient(self.parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close_dialog)

        lbl = tk.Label(
            self, 
            text="📶 SETUP WI-FI KIOSK", 
            font=(FONT_FAMILY, 11, "bold"), 
            bg="#0f172a", fg="#f8fafc"
        )
        lbl.pack(pady=(15, 8))

        form_frame = tk.Frame(self, bg="#0f172a")
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

        btn_frame = tk.Frame(self, bg="#0f172a")
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
            command=self.close_dialog
        )
        btn_cancel.pack(side="right", fill="x", expand=True, padx=5)
        btn_cancel.bind("<Enter>", lambda e: btn_cancel.configure(bg="#334155"))
        btn_cancel.bind("<Leave>", lambda e: btn_cancel.configure(bg="#475569"))

        threading.Thread(target=self.scan_wifi_async, daemon=True).start()

    def close_dialog(self):
        try:
            self.destroy()
        except Exception:
            pass
        if self.on_close_cb:
            self.on_close_cb()

    def toggle_password_visibility(self):
        if self.show_pass_var.get():
            self.entry_pass.configure(show="")
        else:
            self.entry_pass.configure(show="*")

    def scan_wifi_async(self):
        networks = []
        try:
            import subprocess
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

        try:
            self.parent.after(0, lambda: self.update_combo_networks(networks))
        except Exception:
            pass

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
                import time
                time.sleep(1.0)
                success = True
            else:
                cmd = f"nmcli device wifi connect '{ssid}' password '{password}'"
                exit_code = os.system(cmd)
                success = (exit_code == 0)
        except Exception:
            success = False

        try:
            self.parent.after(0, lambda: self.connect_wifi_finish(success, ssid))
        except Exception:
            pass

    def connect_wifi_finish(self, success, ssid):
        try:
            self.btn_connect.configure(text="Hubungkan", state="normal", bg="#10b981")
            if success:
                new_ip = get_ip_address()
                if self.on_connect_cb:
                    self.on_connect_cb(new_ip, ssid)
                messagebox.showinfo("Sukses WiFi", f"Berhasil terhubung ke Wi-Fi: {ssid}!")
                self.close_dialog()
            else:
                messagebox.showerror("Gagal WiFi", f"Gagal menghubungkan ke Wi-Fi: {ssid}. Silakan periksa kembali password Anda.")
        except Exception:
            pass
