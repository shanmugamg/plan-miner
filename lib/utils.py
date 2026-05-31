import os
import sys
import ctypes
import tkinter as tk
from PIL import Image, ImageTk

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_writable_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def register_custom_font(font_path):
    if sys.platform.startswith("win"):
        path_w = os.path.abspath(font_path)
        if os.path.exists(path_w):
            res = ctypes.windll.gdi32.AddFontResourceW(path_w)
            if res > 0:
                return True
    return False

def apply_window_icon(window, ico_path, delay_ms=150):
    """Apply a custom .ico to a CTkToplevel window.

    CustomTkinter resets the Toplevel icon shortly after creation, so we
    schedule the iconbitmap call via after() to run after that reset.
    """
    if not ico_path or not os.path.exists(ico_path):
        return
    ico_path = os.path.abspath(ico_path)

    def _apply():
        if not window.winfo_exists():
            return
        try:
            # Try native Windows iconbitmap API first
            window.iconbitmap(ico_path)
        except Exception:
            try:
                # Fallback to iconphoto only if iconbitmap fails
                img = Image.open(ico_path)
                photo = ImageTk.PhotoImage(img)
                window._icon_photo = photo
                window.iconphoto(True, photo)
            except Exception:
                pass

    # Schedule once after delay to let CTkToplevel initial layout settle
    window.after(delay_ms, _apply)

def load_svg_icon(name, size=(20, 20)):
    path = get_resource_path(os.path.join("assets", "icons", f"{name}.svg"))
    if not os.path.exists(path):
        return None
    import fitz
    import customtkinter as ctk
    doc = fitz.open(path)
    page = doc[0]
    rect = page.rect
    w, h = rect.width, rect.height
    scale_x = size[0] / w
    scale_y = size[1] / h
    matrix = fitz.Matrix(scale_x, scale_y)
    pix = page.get_pixmap(matrix=matrix, alpha=True)
    img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 5
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#2c3e50", foreground="#ffffff",
                         relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 9, "normal"), padx=6, pady=3)
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()
