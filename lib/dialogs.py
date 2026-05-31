import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from lib.utils import apply_window_icon

# Custom themed modal dialog class for CustomTkinter
class CTkMessageDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, dialog_type="info"):
        super().__init__(parent)
        self.withdraw()
        self.attributes("-alpha", 0.0)
        self.title(parent.app_name)
        self.resizable(False, False)
        
        # Center dialog relative to parent frame window in a single geometry setting
        width, height = 450, 220
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - width) // 2
        y = py + (ph - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make modal & transient
        self.transient(parent)
        self.grab_set()
        apply_window_icon(self, parent.ico_path)
        
        self.result = None
        
        # UI color scheme configurations based on dialog style
        if dialog_type == "error":
            hdr_color = "#c0392b"
            icon = "❌"
        elif dialog_type == "warning":
            hdr_color = "#d35400"
            icon = "⚠️"
        elif dialog_type == "yesno":
            hdr_color = "#2980b9"
            icon = "❓"
        else:
            hdr_color = "#16a085"
            icon = "ℹ️"
            
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header banner frame
        hdr_frame = ctk.CTkFrame(self, height=45, fg_color=hdr_color, corner_radius=0)
        hdr_frame.grid(row=0, column=0, sticky="ew")
        hdr_frame.pack_propagate(False)
        
        lbl_title = ctk.CTkLabel(
            hdr_frame, text=f"{icon}  {title}", 
            font=ctk.CTkFont(family=parent.font_family, size=14, weight="bold"),
            text_color="#ffffff"
        )
        lbl_title.pack(side="left", padx=15, pady=8)
        
        # Content frame message details
        msg_frame = ctk.CTkFrame(self, fg_color="transparent")
        msg_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)
        
        lbl_msg = ctk.CTkLabel(
            msg_frame, text=message, justify="left", wraplength=410,
            font=ctk.CTkFont(family=parent.font_family, size=13)
        )
        lbl_msg.pack(anchor="w", expand=True, fill="both")
        
        # Buttons frame row
        btn_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))
        
        if dialog_type == "yesno":
            btn_yes = ctk.CTkButton(
                btn_frame, text="Yes", width=95, fg_color="#27ae60", hover_color="#2ecc71",
                font=ctk.CTkFont(family=parent.font_family, size=12, weight="bold"),
                command=self.on_yes
            )
            btn_yes.pack(side="right", padx=5)
            
            btn_no = ctk.CTkButton(
                btn_frame, text="No", width=95, fg_color="#c0392b", hover_color="#e74c3c",
                font=ctk.CTkFont(family=parent.font_family, size=12, weight="bold"),
                command=self.on_no
            )
            btn_no.pack(side="right", padx=5)
        else:
            btn_ok = ctk.CTkButton(
                btn_frame, text="OK", width=105,
                font=ctk.CTkFont(family=parent.font_family, size=12, weight="bold"),
                command=self.on_ok
            )
            btn_ok.pack(side="right")
            
        self.deiconify()
        self._fade_in()
        self.wait_window(self)
        
    def _fade_in(self, alpha=0.0):
        if not self.winfo_exists():
            return
        if alpha < 1.0:
            alpha = min(1.0, alpha + 0.2)
            self.attributes("-alpha", alpha)
            self.after(10, lambda: self._fade_in(alpha))
            
    def on_ok(self):
        self.result = True
        self.destroy()
        
    def on_yes(self):
        self.result = True
        self.destroy()
        
    def on_no(self):
        self.result = False
        self.destroy()


class CTkInputDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.withdraw()
        self.attributes("-alpha", 0.0)
        self.title(parent.app_name)
        self.resizable(False, False)
        
        # Center dialog relative to parent frame window in a single geometry setting
        width, height = 400, 200
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - width) // 2
        y = py + (ph - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make modal & transient
        self.transient(parent)
        self.grab_set()
        apply_window_icon(self, parent.ico_path)
        
        self.result = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header banner frame
        hdr_frame = ctk.CTkFrame(self, height=45, fg_color="#16a085", corner_radius=0)
        hdr_frame.grid(row=0, column=0, sticky="ew")
        hdr_frame.pack_propagate(False)
        
        lbl_title = ctk.CTkLabel(
            hdr_frame, text=f"💾  {title}", 
            font=ctk.CTkFont(family=parent.font_family, size=14, weight="bold"),
            text_color="#ffffff"
        )
        lbl_title.pack(side="left", padx=15, pady=8)
        
        # Content frame
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)
        content_frame.grid_columnconfigure(0, weight=1)
        
        lbl_text = ctk.CTkLabel(
            content_frame, text=text, justify="left",
            font=ctk.CTkFont(family=parent.font_family, size=13)
        )
        lbl_text.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.entry = ctk.CTkEntry(
            content_frame, width=360,
            font=ctk.CTkFont(family=parent.font_family, size=13)
        )
        self.entry.grid(row=1, column=0, sticky="ew", pady=(5, 5))
        self.entry.focus()
        
        # Bind enter key
        self.entry.bind("<Return>", lambda e: self.on_ok())
        self.entry.bind("<Escape>", lambda e: self.on_cancel())
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, height=50, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 15))
        
        btn_ok = ctk.CTkButton(
            btn_frame, text="OK", width=95, fg_color="#27ae60", hover_color="#2ecc71",
            font=ctk.CTkFont(family=parent.font_family, size=12, weight="bold"),
            command=self.on_ok
        )
        btn_ok.pack(side="right", padx=5)
        
        btn_cancel = ctk.CTkButton(
            btn_frame, text="Cancel", width=95, fg_color="#7f8c8d", hover_color="#95a5a6",
            font=ctk.CTkFont(family=parent.font_family, size=12, weight="bold"),
            command=self.on_cancel
        )
        btn_cancel.pack(side="right", padx=5)
        
        self.deiconify()
        self._fade_in()
        self.wait_window(self)
        
    def _fade_in(self, alpha=0.0):
        if not self.winfo_exists():
            return
        if alpha < 1.0:
            alpha = min(1.0, alpha + 0.2)
            self.attributes("-alpha", alpha)
            self.after(10, lambda: self._fade_in(alpha))
            
    def on_ok(self):
        self.result = self.entry.get().strip()
        self.destroy()
        
    def on_cancel(self):
        self.result = None
        self.destroy()
        
    def get_input(self):
        return self.result
