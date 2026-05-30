import tkinter as tk
import cv2
import numpy as np
from PIL import Image, ImageTk
from lib.detector_engine import ColorDetectorEngine

class CanvasEventsMixin:
    def toggle_mouse_pan(self):
        self.mouse_pan_active = not self.mouse_pan_active
        if self.mouse_pan_active:
            self.btn_mouse_pan.configure(fg_color="#d35400", text="🖐 Panning")
            self.set_status("Mouse Pan active. Left-click drag to pan.")
            # Deactivate conflicting modes
            if self.select_mode_active:
                self.toggle_select_mode()
            if self.zoom_window_active:
                self.toggle_zoom_window_mode()
        else:
            self.btn_mouse_pan.configure(fg_color="#138d75", text="🖐 Pan")
            self.set_status("Mouse Pan off.")

    def toggle_select_mode(self):
        if self.total_pages == 0:
            self.show_warning("Warning", "Please load a PDF or Image document first.")
            return
            
        self.select_mode_active = not self.select_mode_active
        if self.select_mode_active:
            self.btn_select_target.configure(text="🎯 Click symbol in canvas...", fg_color="#e74c3c")
            self.set_status("Click-to-Select active. Choose object center.")
            if self.zoom_window_active:
                self.toggle_zoom_window_mode()
            if self.mouse_pan_active:
                self.toggle_mouse_pan()
        else:
            self.btn_select_target.configure(text="🎯 Click to Select Target Object", fg_color="#d35400")
            self.set_status("Select mode off.")

    def on_left_click(self, event):
        if not self.orig_image:
            return

        if self.mouse_pan_active:
            self.pan_last_x = event.x
            self.pan_last_y = event.y
            return
            
        if self.zoom_window_active:
            self.zoom_box_start = (event.x, event.y)
            return
            
        ix, iy = self.canvas_to_image_coords(event.x, event.y)
        
        if self.select_mode_active:
            self.select_mode_active = False
            self.btn_select_target.configure(text="🎯 Click to Select Target Object", fg_color="#d35400")
            self.set_status("Extracting color properties...")
            
            img_bgr = self.doc_pages[self.current_page_idx]
            try:
                self.template_info = ColorDetectorEngine.extract_template_from_click(img_bgr, ix, iy)
                self.select_click_coords = (ix, iy)
                self.update_previews()
                self.page_detections = {}
                self.page_manual_added = {}
                self.page_manual_deleted_ids = {}
                self.live_mask = None
                self.live_mask_signature = None
                self.live_overlay_rgb = None
                
                # Auto-calibrate clustering proximity to 1.25x of target dimensions
                max_dim = max(self.template_info["width"], self.template_info["height"])
                auto_prox = max(5.0, min(300.0, max_dim * 1.25))
                self.slider_proximity.set(auto_prox)
                self.on_param_changed(None)
                
                self.set_status("Template color extracted. Proximity auto-scaled. Click 'Run Object Detection' to scan.")
                self.redraw_canvas()
                self.logger.info("template_extracted")
            except Exception as e:
                self.set_status("Extraction failed.", is_error=True)
                self.show_error("Extraction Error", str(e))
                self.logger.exception("template_extract_failed")
            return
            
        # Deleting standard detection
        clicked_det_id = None
        for det in self.detections:
            if det["id"] in self.manual_deleted_ids:
                continue
            x, y, w, h = det["bbox"]
            if x <= ix <= x + w and y <= iy <= y + h:
                clicked_det_id = det["id"]
                break
                
        if clicked_det_id is not None:
            self.manual_deleted_ids.add(clicked_det_id)
            self.redraw_canvas()
            self.set_status(f"Removed detection #{clicked_det_id}.")
            self.logger.info("manual_box_removed id=%s", clicked_det_id)
            return
            
        # Deleting user added boxes
        clicked_added_idx = None
        for idx, man in enumerate(self.manual_added):
            x, y, w, h = man["bbox"]
            if x <= ix <= x + w and y <= iy <= y + h:
                clicked_added_idx = idx
                break
                
        if clicked_added_idx is not None:
            self.manual_added.pop(clicked_added_idx)
            self.redraw_canvas()
            self.set_status("Removed manual detection box.")
            self.logger.info("manual_box_removed_manual index=%s", clicked_added_idx)

    def on_left_drag(self, event):
        if self.mouse_pan_active:
            dx = event.x - self.pan_last_x
            dy = event.y - self.pan_last_y
            self.pan_canvas(dx, dy)
            self.pan_last_x = event.x
            self.pan_last_y = event.y
            return

        if self.zoom_window_active and self.zoom_box_start:
            x0, y0 = self.zoom_box_start
            x1, y1 = event.x, event.y
            
            self.canvas.delete("zoom_box")
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                outline="#ff3d00", width=2, dash=(4, 4), tags="zoom_box"
            )

    def on_left_release(self, event):
        if self.zoom_window_active and self.zoom_box_start:
            x0, y0 = self.zoom_box_start
            x1, y1 = event.x, event.y
            self.canvas.delete("zoom_box")
            
            w = abs(x1 - x0)
            h = abs(y1 - y0)
            
            if w > 5 and h > 5:
                ix0, iy0 = self.canvas_to_image_coords(x0, y0)
                ix1, iy1 = self.canvas_to_image_coords(x1, y1)
                
                img_x1 = min(ix0, ix1)
                img_y1 = min(iy0, iy1)
                img_x2 = max(ix0, ix1)
                img_y2 = max(iy0, iy1)
                
                iw = img_x2 - img_x1
                ih = img_y2 - img_y1
                
                cw = self.canvas.winfo_width()
                ch = self.canvas.winfo_height()
                
                scale_w = cw / iw
                scale_h = ch / ih
                self.zoom_scale = max(0.05, min(scale_w, scale_h, 8.0))
                
                icx = (img_x1 + img_x2) / 2
                icy = (img_y1 + img_y2) / 2
                
                self.pan_x = (cw / 2) - icx * self.zoom_scale
                self.pan_y = (ch / 2) - icy * self.zoom_scale
                
            self.zoom_box_start = None
            self.toggle_zoom_window_mode()
            self.redraw_canvas()

    def on_right_click(self, event):
        if self.template_info is None or not self.orig_image:
            return
            
        ix, iy = self.canvas_to_image_coords(event.x, event.y)
        
        tw = self.template_info["width"]
        th = self.template_info["height"]
        
        new_box = {
            "bbox": (int(ix - tw // 2), int(iy - th // 2), int(tw), int(th)),
            "centroid": (int(ix), int(iy))
        }
        self.manual_added.append(new_box)
        self.redraw_canvas()
        self.set_status("Manually placed object box.")
        self.logger.info("manual_box_added")

    def update_previews(self):
        if self.template_info is None:
            return
            
        patch_bgr = self.template_info["patch_bgr"]
        patch_rgb = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2RGB)
        pil_patch = Image.fromarray(patch_rgb).resize((90, 90), Image.Resampling.NEAREST)
        self.tk_patch = ImageTk.PhotoImage(pil_patch)
        self.canvas_crop.delete("all")
        self.canvas_crop.create_image(0, 0, anchor=tk.NW, image=self.tk_patch)
        
        mask = self.template_info["patch_mask"]
        pil_mask = Image.fromarray(mask).resize((90, 90), Image.Resampling.NEAREST)
        self.tk_mask = ImageTk.PhotoImage(pil_mask)
        self.canvas_mask.delete("all")
        self.canvas_mask.create_image(0, 0, anchor=tk.NW, image=self.tk_mask)

    def on_param_changed(self, event):
        self.lbl_tolerance.configure(text=f"Color Tolerance (Range Extension): {self.slider_tolerance.get():.2f}")
        self.lbl_min_area.configure(text=f"Min Object Size Filter: {self.slider_min_area.get():.2f}x")
        self.lbl_max_area.configure(text=f"Max Object Size Filter: {self.slider_max_area.get():.2f}x")
        self.lbl_proximity.configure(text=f"Proximity Clustering: {int(self.slider_proximity.get())} px")
        
        if self.template_info is not None:
            if self.switch_live_preview.get():
                self.update_live_preview()
                self.redraw_canvas()

    def on_live_toggle(self):
        if self.switch_live_preview.get():
            self.update_live_preview()
        self.redraw_canvas()

    def run_detection(self):
        if self.total_pages == 0 or self.template_info is None:
            return
            
        img_bgr = self.doc_pages[self.current_page_idx]
        self.set_status("Running detection...")
        
        try:
            self.detections, _ = ColorDetectorEngine.detect_objects(
                img_bgr, self.template_info,
                tolerance=self.slider_tolerance.get(),
                proximity=self.slider_proximity.get(),
                min_area_scale=self.slider_min_area.get(),
                max_area_scale=self.slider_max_area.get()
            )
            self.logger.info("detection_complete count=%s", len(self.detections))
            self.set_status("Detection completed.")
            self.redraw_canvas()
        except Exception as e:
            self.set_status("Detection failed.", is_error=True)
            self.show_error("Detection Error", str(e))
            self.logger.exception("detection_failed")

    def update_live_preview(self):
        if self.template_info is None or not self.orig_image:
            self.live_mask = None
            self.live_mask_signature = None
            self.live_overlay_rgb = None
            self.live_overlay_pil = None
            return

        signature = (
            self.current_page_idx,
            tuple(self.template_info["lower_bound"]),
            tuple(self.template_info["upper_bound"]),
            float(self.slider_tolerance.get()),
            float(self.slider_proximity.get()),
            float(self.slider_min_area.get()),
            float(self.slider_max_area.get())
        )

        if self.live_mask_signature == signature and self.live_overlay_rgb is not None:
            return

        img_bgr = self.doc_pages[self.current_page_idx]
        _, mask = ColorDetectorEngine.detect_objects(
            img_bgr, self.template_info,
            tolerance=self.slider_tolerance.get(),
            proximity=self.slider_proximity.get(),
            min_area_scale=self.slider_min_area.get(),
            max_area_scale=self.slider_max_area.get()
        )
        overlay = np.zeros_like(img_bgr)
        overlay[mask > 0] = [230, 126, 34]
        blended = cv2.addWeighted(img_bgr, 0.7, overlay, 0.3, 0)
        self.live_overlay_rgb = cv2.cvtColor(blended, cv2.COLOR_BGR2RGB)
        self.live_overlay_pil = Image.fromarray(self.live_overlay_rgb)
        self.live_mask = mask
        self.live_mask_signature = signature
