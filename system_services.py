import socket
import os
import subprocess
import psutil
import shutil
import time

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Offline / 127.0.0.1"

def _get_linux_terminal():
    for term in ["x-terminal-emulator", "lxterminal", "xterm", "xfce4-terminal", "gnome-terminal", "konsole"]:
        if shutil.which(term):
            return term
    return None

def get_x1202_battery_percentage():
    try:
        import smbus2
        bus = smbus2.SMBus(1)
        address = 0x36

        # Kirim QuickStart hanya sekali saat pertama kali dibaca
        global _x1202_initialized
        if '_x1202_initialized' not in globals():
            bus.write_word_data(address, 0x06, 0x0040)
            time.sleep(0.2)
            _x1202_initialized = True

        volt_data = bus.read_i2c_block_data(address, 0x02, 2)
        raw_volt = (volt_data[0] << 4) | (volt_data[1] >> 4)
        voltage = raw_volt * 1.25 / 1000.0

        soc_data = bus.read_i2c_block_data(address, 0x04, 2)
        capacity = soc_data[0] + soc_data[1] / 256.0
        capacity = max(0.0, min(100.0, capacity))

        bus.close()
        return capacity, voltage
    except Exception as e:
        print(f"[X1202] Error baca baterai: {e}")
        return None, None

def get_ssh_status():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.15)
        result = s.connect_ex(("127.0.0.1", 22))
        s.close()
        return result == 0
    except Exception:
        return False

def get_firewall_status():
    try:
        if os.name == 'nt':
            out = subprocess.check_output(["netsh", "advfirewall", "show", "allprofiles", "state"], text=True, errors='ignore')
            return "ON" in out
        else:
            try:
                if os.path.exists("/etc/ufw/ufw.conf"):
                    with open("/etc/ufw/ufw.conf", "r") as f:
                        for line in f:
                            if line.strip().startswith("ENABLED="):
                                return line.split("=")[1].strip().lower() == "yes"
            except Exception:
                pass

            try:
                res = subprocess.check_output(["systemctl", "is-active", "ufw"], text=True, errors='ignore').strip()
                if res == "active":
                    return True
            except Exception:
                pass
            
            try:
                res = subprocess.check_output(["systemctl", "is-active", "firewalld"], text=True, errors='ignore').strip()
                if res == "active":
                    return True
            except Exception:
                pass
            
            return False
    except Exception:
        return False

def get_dnsmasq_status():
    try:
        if os.name == 'nt':
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'dnsmasq' in proc.info['name'].lower():
                    return True
            return False
        else:
            try:
                res = subprocess.check_output(["systemctl", "is-active", "dnsmasq"], text=True, errors='ignore').strip()
                return res == "active"
            except Exception:
                return False
    except Exception:
        return False

def toggle_ssh(current_active):
    if os.name == 'nt':
        cmd = "Stop-Service sshd" if current_active else "Start-Service sshd"
        subprocess.Popen(["powershell", "-Command", f"Start-Process powershell -ArgumentList '-Command {cmd}' -Verb RunAs"])
    else:
        cmd = ["sudo", "systemctl", "stop", "ssh"] if current_active else ["sudo", "systemctl", "enable", "--now", "ssh"]
        subprocess.run(cmd, check=True)
