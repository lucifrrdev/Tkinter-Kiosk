import tkinter as tk
import os
import random
from PIL import Image, ImageTk

class ScreensaverManager:
    def __init__(self, window):
        self.window = window
        self.screensaver_active = False
        self.ss_timer_job = None
        self.ss_blank_job = None
        self.ss_anim_job = None
        self.ss_frame = None
        self.ss_image_label = None
        self.ss_photo = None
        self.ss_mouse_x = None
        self.ss_mouse_y = None
        self._paused = False
        
        # Bind global input events to reset screensaver timer
        self.window.bind_all("<Any-KeyPress>", self.reset_timer)
        self.window.bind_all("<Any-Button>", self.reset_timer)
        self.window.bind_all("<Motion>", self.reset_timer)
        
        self.reset_timer()

    def reset_timer(self, event=None):
        if self._paused:
            return
        if self.screensaver_active:
            return
            
        self.cancel_timers()
            
        # Jadwalkan kemunculan screensaver setelah 60 detik (60000 milidetik) idle
        self.ss_timer_job = self.window.after(60000, self.show_screensaver)
        # Jadwalkan kemunculan layar blank hitam setelah 5 menit (300000 milidetik) idle
        self.ss_blank_job = self.window.after(300000, self.show_blank_screensaver)

    def cancel_timers(self):
        if self.ss_timer_job:
            self.window.after_cancel(self.ss_timer_job)
            self.ss_timer_job = None
        if self.ss_blank_job:
            self.window.after_cancel(self.ss_blank_job)
            self.ss_blank_job = None

    def stop_timer(self):
        self._paused = True
        self.cancel_timers()

    def start_timer(self):
        self._paused = False
        self.reset_timer()

    def show_screensaver(self):
        self.screensaver_active = True
        
        # Buat overlay Frame hitam penuh jika belum ada
        if not self.ss_frame or not self.ss_frame.winfo_exists():
            self.ss_frame = tk.Frame(self.window, bg="#020617")
            self.ss_frame.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            
            # Label untuk menampilkan gambar
            self.ss_image_label = tk.Label(self.ss_frame, bg="#020617")
            self.ss_image_label.pack(fill="both", expand=True)
            
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
        if self.ss_anim_job:
            self.window.after_cancel(self.ss_anim_job)
            self.ss_anim_job = None
            
        # Buat/ubah overlay Frame menjadi hitam penuh tanpa gambar
        if not self.ss_frame or not self.ss_frame.winfo_exists():
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
        if not self.screensaver_active:
            return
            
        script_dir = os.path.dirname(os.path.abspath(__file__))
        jpg_files = [os.path.join(script_dir, f) for f in os.listdir(script_dir) if f.lower().endswith('.jpg') or f.lower().endswith('.jpeg')]
        
        if jpg_files:
            chosen_img = random.choice(jpg_files)
            try:
                w = self.window.winfo_width()
                h = self.window.winfo_height()
                if w < 10: w = 480
                if h < 10: h = 320
                
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
        
        if self.ss_anim_job:
            self.window.after_cancel(self.ss_anim_job)
            self.ss_anim_job = None
            
        self.cancel_timers()
            
        if self.ss_frame:
            try:
                self.ss_frame.destroy()
            except Exception:
                pass
            self.ss_frame = None
            
        self.reset_timer()
