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

def apply_window_icon(window, ico_path, delay_ms=50):
    """Apply a custom .ico to a CTkToplevel window.

    CustomTkinter resets the Toplevel icon shortly after creation, so we
    schedule the iconbitmap call via after() to run after that reset.
    """
    if not ico_path or not os.path.exists(ico_path):
        return
    ico_path = os.path.abspath(ico_path)

    def _apply():
        try:
            window.iconbitmap(ico_path)
        except Exception:
            pass
        try:
            img = Image.open(ico_path)
            photo = ImageTk.PhotoImage(img)
            window._icon_photo = photo
            window.iconphoto(True, photo)
        except Exception:
            pass

    _apply()
    window.after(delay_ms, _apply)
    window.after(delay_ms * 4, _apply)
