import os
import sys
import ctypes
import yaml
import tkinter as tk
import customtkinter as ctk

from lib.utils import get_resource_path, get_writable_path, register_custom_font
from lib.logger import setup_logger, get_logger
from lib.dialogs import CTkMessageDialog
from lib.about_dialog import CTkAboutDialog
from lib.layout import LayoutMixin
from lib.file_handler import FileHandlerMixin
from lib.canvas_navigation import CanvasNavigationMixin
from lib.canvas_events import CanvasEventsMixin
from lib.presets_manager import PresetManagerMixin
from lib.batch_exporter import BatchExporterMixin

# Set Windows DPI Awareness at the very beginning
try:
    # 1 = System DPI Aware (prevents Tkinter crashes/hangs when moving between monitors)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Set application appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PlanMinerApp(
    ctk.CTk, 
    LayoutMixin, 
    FileHandlerMixin, 
    CanvasNavigationMixin, 
    CanvasEventsMixin, 
    PresetManagerMixin, 
    BatchExporterMixin
):
    def __init__(self):
        super().__init__()

        log_dir = get_writable_path("logs")
        setup_logger(log_dir)
        self.logger = get_logger()
        self.logger.info("app_start")
        
        self.config_path = get_resource_path(os.path.join("assets", "config.yaml"))
        self.load_configuration()
        self.load_app_fonts()
        
        self.title(self.app_name)
        self.geometry("1400x900")
        self.minsize(1200, 800)
        
        # Defer maximize so it reliably applies after the window is drawn
        def maximize_window():
            try:
                self.state("zoomed")
            except Exception as e:
                self.logger.warning("Failed to maximize window: %s", e)
        self.after(200, maximize_window)
        
        self.set_app_icon()
        
        # Handle close confirmation
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.document_path = None
        self.pdf_doc = None
        self.doc_pages = []          
        self.total_pages = 0
        self.current_page_idx = 0
        self.dpi = 150
        self.is_loading_page = False 
        self.is_batch_running = False

        self.live_mask = None
        self.live_mask_signature = None
        self.live_overlay_rgb = None
        self.live_overlay_pil = None
        self._image_cache = {}
        self._image_cache_order = []
        self._canvas_image_id = None
        self._hq_after_id = None
        self._last_hq_key = None
        
        self.template_info = None  
        self.select_click_coords = None
        self.page_detections = {}
        self.page_manual_added = {}
        self.page_manual_deleted_ids = {} 
        
        self.sidebar_visible = True
        self.select_mode_active = False
        self.add_mode_active = False
        self.remove_mode_active = False
        self.zoom_window_active = False
        self.zoom_box_start = None
        self.mouse_pan_active = False
        self.pan_last_x = 0
        self.pan_last_y = 0
        
        self.zoom_scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.orig_image = None  
        self.disp_image = None  
        self.tk_image = None    
        
        self.presets_file = get_writable_path(os.path.join("assets", "presets", "presets.json"))
        os.makedirs(os.path.dirname(self.presets_file), exist_ok=True)
        self.presets = self.load_presets()
        
        self.input_dir = get_writable_path("input")
        self.output_dir = get_writable_path("output")
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.create_layout()
        self.update_preset_menu()
        self.check_expiry()

    def check_expiry(self):
        from lib.date_check import check_license
        from datetime import datetime, timezone, timedelta
        
        build_date_file = get_resource_path("BUILD_DATE")
        build_date = datetime.now(timezone.utc)
        if os.path.exists(build_date_file):
            try:
                with open(build_date_file, 'r') as bf:
                    build_date = datetime.strptime(bf.read().strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception as e:
                self.logger.warning("Failed to parse build date: %s", e)

        last_run_file = get_writable_path(os.path.join("assets", ".run_info"))
        is_valid, msg = check_license(build_date, self.expiry_days, last_run_file)
        self.logger.info("License check: %s", msg)

        # Calculate expiry_date and self.days_left for About dialog
        exp_date = build_date + timedelta(days=self.expiry_days)
        self.expiry_date = exp_date.strftime("%Y-%m-%d")
        
        # Extract remaining days from the message or fallback
        self.days_left = 0
        try:
            parts = msg.split()
            for i, part in enumerate(parts):
                if "day(s)" in part and i > 0:
                    self.days_left = int(parts[i-1])
                    break
        except Exception:
            self.days_left = (exp_date.date() - datetime.now().date()).days

        if not is_valid:
            self.show_error("License Verification Failed", msg)
            self.destroy()
            sys.exit(0)

    # ── CUSTOM DIALOG HELPER WRAPPERS ────────────────────────────────────────
    def show_info(self, title, message):
        CTkMessageDialog(self, title, message, "info")

    def show_warning(self, title, message):
        CTkMessageDialog(self, title, message, "warning")

    def show_error(self, title, message):
        CTkMessageDialog(self, title, message, "error")

    def ask_yes_no(self, title, message):
        dialog = CTkMessageDialog(self, title, message, "yesno")
        return dialog.result

    def load_configuration(self):
        self.app_name = "PlanMiner"
        self.app_url = "https://www.geoicon.com"
        self.company_name = "PlanMiner"
        self.company_url = "https://www.geoicon.com"
        self.logo_path = get_resource_path(os.path.join("assets", "logo", "logo.png"))
        self.ico_path = get_resource_path(os.path.join("assets", "logo", "favicon.ico"))
        self.copyright_notice = "Copyright © 2026. All rights reserved."
        self.licensed_to = "Internal Testing"
        self.expiry_date = "2027-12-31"
        self.days_left = 60
        self.expiry_days = 60
        
        self.def_tolerance = 0.5
        self.def_min_area = 0.2
        self.def_max_area = 4.0
        self.def_proximity = 100.0
        self.def_legend = True
        self.app_version = "0.5.3"
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                    if cfg:
                        branding = cfg.get("branding", {})
                        self.app_name = branding.get("app_name", self.app_name)
                        self.app_url = branding.get("app_url", self.app_url)
                        self.logo_path = get_resource_path(branding.get("logo_path", "assets/logo/logo.png"))
                        self.ico_path = get_resource_path(branding.get("ico_path", "assets/logo/favicon.ico"))
                        self.company_name = branding.get("company_name", self.company_name)
                        self.company_url = branding.get("company_url", self.company_url)
                        self.copyright_notice = branding.get("copyright_notice", self.copyright_notice)
                        
                        licensing = cfg.get("licensing", {})
                        self.licensed_to = licensing.get("licensed_to", self.licensed_to)
                        self.expiry_days = int(licensing.get("expiry_days", 60))
                        
                        version_file = branding.get("version_file", "VERSION")
                        version_file_path = get_resource_path(version_file)
                        if os.path.exists(version_file_path):
                            with open(version_file_path, 'r') as vf:
                                self.app_version = vf.read().strip()
                        
                        thresholds = cfg.get("thresholds", {})
                        self.def_tolerance = float(thresholds.get("tolerance", self.def_tolerance))
                        self.def_min_area = float(thresholds.get("min_area", self.def_min_area))
                        self.def_max_area = float(thresholds.get("max_area", self.def_max_area))
                        self.def_proximity = float(thresholds.get("proximity", self.def_proximity))
                        self.def_legend = bool(thresholds.get("legend", self.def_legend))
            except Exception as e:
                self.logger.warning("Failed to load config.yaml: %s", e)

    def load_app_fonts(self):
        font_dir = get_resource_path(os.path.join("assets", "fonts"))
        if os.path.exists(font_dir):
            for file in os.listdir(font_dir):
                if file.endswith(".ttf"):
                    register_custom_font(os.path.join(font_dir, file))
        self.font_family = "Noto Sans Display SemiCondensed"

    def set_app_icon(self):
        if os.path.exists(self.ico_path):
            try:
                self.iconbitmap(self.ico_path)
            except Exception as e:
                self.logger.warning("Could not load icon bitmap: %s", e)

    # ── SIDEBAR TOGGLE & ABOUT DIALOG ────────────────────────────────────────
    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.grid_forget()
            self.btn_toggle_sidebar.configure(text="▶ Show Sidebar")
            self.sidebar_visible = False
        else:
            self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            self.btn_toggle_sidebar.configure(text="◀ Hide Sidebar")
            self.sidebar_visible = True

    def show_about_dialog(self):
        CTkAboutDialog(self)

    # ── STATUS HELPERS ───────────────────────────────────────────────────────
    def set_status(self, text, is_error=False):
        color = "#e74c3c" if is_error else "#2ecc71"
        self.lbl_status.configure(text=text, text_color=color)

    def on_closing(self):
        if self.ask_yes_no("Confirm Exit", "Are you sure you want to close the application?"):
            self.destroy()
            sys.exit(0)

    @property
    def detections(self):
        if self.current_page_idx not in self.page_detections:
            self.page_detections[self.current_page_idx] = []
        return self.page_detections[self.current_page_idx]

    @detections.setter
    def detections(self, value):
        self.page_detections[self.current_page_idx] = value

    @property
    def manual_added(self):
        if self.current_page_idx not in self.page_manual_added:
            self.page_manual_added[self.current_page_idx] = []
        return self.page_manual_added[self.current_page_idx]

    @manual_added.setter
    def manual_added(self, value):
        self.page_manual_added[self.current_page_idx] = value

    @property
    def manual_deleted_ids(self):
        if self.current_page_idx not in self.page_manual_deleted_ids:
            self.page_manual_deleted_ids[self.current_page_idx] = set()
        return self.page_manual_deleted_ids[self.current_page_idx]

    @manual_deleted_ids.setter
    def manual_deleted_ids(self, value):
        self.page_manual_deleted_ids[self.current_page_idx] = value

if __name__ == "__main__":
    app = PlanMinerApp()
    app.mainloop()
