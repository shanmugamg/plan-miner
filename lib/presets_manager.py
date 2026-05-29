import os
import json
import base64
import cv2
import numpy as np
import customtkinter as ctk
from lib.dialogs import CTkInputDialog

class PresetManagerMixin:
    def load_presets(self):
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_preset_dialog(self):
        if self.template_info is None:
            self.show_warning("Warning", "Please click/select an object first to save a preset.")
            return
            
        name = CTkInputDialog(self, title="Save Preset", text="Enter preset name (e.g. Red Sprinkler):").get_input()
        if not name:
            return
            
        # Base64 encode the patch image & mask to save them inside the presets file
        patch_bgr_b64 = ""
        patch_mask_b64 = ""
        try:
            _, buffer_bgr = cv2.imencode('.png', self.template_info["patch_bgr"])
            patch_bgr_b64 = base64.b64encode(buffer_bgr).decode('utf-8')
            
            _, buffer_mask = cv2.imencode('.png', self.template_info["patch_mask"])
            patch_mask_b64 = base64.b64encode(buffer_mask).decode('utf-8')
        except Exception as e:
            print(f"Error encoding patch template for preset: {e}")

        self.presets[name] = {
            "lower_bound": self.template_info["lower_bound"],
            "upper_bound": self.template_info["upper_bound"],
            "width": self.template_info["width"],
            "height": self.template_info["height"],
            "area": self.template_info["area"],
            "patch_bgr_b64": patch_bgr_b64,
            "patch_mask_b64": patch_mask_b64,
            "tolerance": self.slider_tolerance.get(),
            "min_area": self.slider_min_area.get(),
            "max_area": self.slider_max_area.get(),
            "proximity": self.slider_proximity.get()
        }
        
        try:
            with open(self.presets_file, 'w') as f:
                json.dump(self.presets, f, indent=4)
            self.update_preset_menu()
            self.preset_var.set(name)
            self.set_status(f"Preset '{name}' saved.")
            self.logger.info("preset_saved name=%s", name)
        except Exception as e:
            self.show_error("Error", f"Failed to save preset: {e}")
            self.logger.exception("preset_save_failed name=%s", name)

    def update_preset_menu(self):
        menu_items = ["None"] + list(self.presets.keys())
        self.preset_menu.configure(values=menu_items)

    def apply_preset(self, name):
        if name == "None" or name not in self.presets:
            return
            
        preset_data = self.presets[name]

        if not self.validate_preset(preset_data):
            self.show_error("Invalid Preset", "Preset data is malformed or incomplete.")
            self.logger.warning("preset_invalid name=%s", name)
            return
        
        # Attempt to decode base64 patch image & mask, fallback to placeholder green box if missing
        patch_bgr = None
        patch_mask = None
        if "patch_bgr_b64" in preset_data and preset_data["patch_bgr_b64"]:
            try:
                dec_bgr = base64.b64decode(preset_data["patch_bgr_b64"])
                np_bgr = np.frombuffer(dec_bgr, dtype=np.uint8)
                patch_bgr = cv2.imdecode(np_bgr, cv2.IMREAD_COLOR)
                
                dec_mask = base64.b64decode(preset_data["patch_mask_b64"])
                np_mask = np.frombuffer(dec_mask, dtype=np.uint8)
                patch_mask = cv2.imdecode(np_mask, cv2.IMREAD_GRAYSCALE)
            except Exception as e:
                print(f"Error decoding template patch from preset: {e}")
                
        if patch_bgr is None or patch_mask is None:
            patch_bgr = np.zeros((90, 90, 3), dtype=np.uint8)
            cv2.rectangle(patch_bgr, (10, 10), (80, 80), (128, 255, 128), -1)
            patch_mask = np.zeros((90, 90), dtype=np.uint8)

        self.template_info = {
            "lower_bound": preset_data["lower_bound"],
            "upper_bound": preset_data["upper_bound"],
            "width": preset_data["width"],
            "height": preset_data["height"],
            "area": preset_data["area"],
            "patch_bgr": patch_bgr,
            "patch_mask": patch_mask
        }
        self.select_click_coords = None
        
        self.update_previews()
        
        self.slider_tolerance.set(preset_data.get("tolerance", 0.5))
        self.slider_min_area.set(preset_data.get("min_area", 0.2))
        self.slider_max_area.set(preset_data.get("max_area", 4.0))
        self.slider_proximity.set(preset_data.get("proximity", 100.0))
        
        self.on_param_changed(None)
        
        self.detections = []
        self.manual_added = []
        self.manual_deleted_ids = set()
        self.set_status(f"Preset '{name}' applied. Click 'Run Object Detection' to scan.")
        self.redraw_canvas()
        self.logger.info("preset_applied name=%s", name)

    def validate_preset(self, preset_data):
        required_keys = [
            "lower_bound", "upper_bound", "width", "height", "area",
            "tolerance", "min_area", "max_area", "proximity"
        ]
        for key in required_keys:
            if key not in preset_data:
                return False
        if not isinstance(preset_data["lower_bound"], list) or not isinstance(preset_data["upper_bound"], list):
            return False
        return True
