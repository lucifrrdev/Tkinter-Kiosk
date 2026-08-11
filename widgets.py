import tkinter as tk
import os

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
        # Hitung panjang fill line berdasarkan persentase
        if pct == 0:
            new_x = self.r
        else:
            new_x = self.r + (pct / 100.0) * (self.width - 2 * self.r)
        
        self.coords(self.fill_line, self.r, self.y, new_x, self.y)

class CardButton(tk.Frame):
    def __init__(self, parent, icon, title, subtitle, bg_color, hover_color, command, **kwargs):
        super().__init__(parent, bg=bg_color, highlightthickness=0, bd=0, cursor="hand2", **kwargs)
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.command = command
        
        # Grid Configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Bind events ke frame itu sendiri
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
        # Icon Label
        self.lbl_icon = tk.Label(self, text=icon, font=(FONT_FAMILY, 24), bg=bg_color, fg="white")
        self.lbl_icon.grid(row=1, column=0, pady=(0, 2), sticky="s")
        
        # Title Label
        self.lbl_title = tk.Label(self, text=title, font=(FONT_FAMILY, 10, "bold"), bg=bg_color, fg="white")
        self.lbl_title.grid(row=2, column=0, sticky="n")
        
        # Subtitle Label
        self.lbl_sub = tk.Label(self, text=subtitle, font=(FONT_FAMILY, 8), bg=bg_color, fg="#cbd5e1")
        self.lbl_sub.grid(row=3, column=0, pady=(0, 10), sticky="n")
        
        # Bind events ke seluruh anak widget agar hover & klik bekerja mulus
        for child in (self.lbl_icon, self.lbl_title, self.lbl_sub):
            child.bind("<Enter>", self.on_enter)
            child.bind("<Leave>", self.on_leave)
            child.bind("<Button-1>", self.on_click)

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
