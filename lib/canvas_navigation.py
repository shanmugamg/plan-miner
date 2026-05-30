import tkinter as tk
from PIL import Image, ImageTk

class CanvasNavigationMixin:
    def get_image_source(self):
        if self.switch_live_preview.get() and self.template_info is not None:
            if self.live_overlay_pil is None:
                self.update_live_preview()
            if self.live_overlay_pil is not None:
                return self.live_overlay_pil
        return self.orig_image

    def cache_get(self, key):
        return self._image_cache.get(key)

    def cache_put(self, key, image):
        if key in self._image_cache:
            return
        self._image_cache[key] = image
        self._image_cache_order.append(key)
        if len(self._image_cache_order) > 6:
            old_key = self._image_cache_order.pop(0)
            self._image_cache.pop(old_key, None)

    def schedule_hq_render(self, key, img_src, size, crop_box=None):
        if self._hq_after_id:
            try:
                self.after_cancel(self._hq_after_id)
            except Exception:
                pass
        def _render():
            if self._last_hq_key != key:
                return
            if crop_box:
                hq_image = img_src.crop(crop_box).resize(size, Image.Resampling.LANCZOS)
            else:
                hq_image = img_src.resize(size, Image.Resampling.LANCZOS)
            self.cache_put(key, hq_image)
            self.disp_image = hq_image
            self.tk_image = ImageTk.PhotoImage(self.disp_image)
            if self._canvas_image_id is not None:
                self.canvas.itemconfig(self._canvas_image_id, image=self.tk_image)
        self._hq_after_id = self.after(150, _render)

    def on_canvas_resize(self, event):
        if hasattr(self, "_resize_after_id") and self._resize_after_id:
            try:
                self.after_cancel(self._resize_after_id)
            except Exception:
                pass
        self._resize_after_id = self.after(120, self.redraw_canvas)
    def reset_zoom(self):
        if not self.orig_image:
            return
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1: canvas_w = 800
        if canvas_h <= 1: canvas_h = 600
        
        img_w, img_h = self.orig_image.size
        
        scale_w = (canvas_w - 40) / img_w
        scale_h = (canvas_h - 40) / img_h
        self.zoom_scale = min(scale_w, scale_h, 1.0)
        
        self.pan_x = (canvas_w - img_w * self.zoom_scale) / 2
        self.pan_y = (canvas_h - img_h * self.zoom_scale) / 2

    def reset_zoom_button(self):
        self.reset_zoom()
        self.redraw_canvas()

    def adjust_zoom_fixed(self, factor):
        if not self.orig_image:
            return
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        ix, iy = self.canvas_to_image_coords(cx, cy)
        
        self.zoom_scale = max(0.05, min(10.0, self.zoom_scale * factor))
        self.pan_x = cx - ix * self.zoom_scale
        self.pan_y = cy - iy * self.zoom_scale
        self.redraw_canvas()

    def toggle_zoom_window_mode(self):
        if not self.orig_image:
            return
        self.zoom_window_active = not self.zoom_window_active
        if self.zoom_window_active:
            self.btn_zoom_window.configure(fg_color="#d35400")
            self.set_status("Drag a box on the canvas to zoom into that region.")
            if self.select_mode_active:
                self.toggle_select_mode()
            if self.mouse_pan_active:
                self.toggle_mouse_pan()
            if getattr(self, "add_mode_active", False):
                self.toggle_add_mode()
            if getattr(self, "remove_mode_active", False):
                self.toggle_remove_mode()
        else:
            self.btn_zoom_window.configure(fg_color="#b7770d")
            self.set_status("Box Zoom off.")

    def on_pan_start(self, event):
        self.pan_last_x = event.x
        self.pan_last_y = event.y

    def on_pan_drag(self, event):
        dx = event.x - self.pan_last_x
        dy = event.y - self.pan_last_y
        self.pan_canvas(dx, dy)
        self.pan_last_x = event.x
        self.pan_last_y = event.y

    def pan_canvas(self, dx, dy):
        self.pan_x += dx
        self.pan_y += dy
        self.redraw_canvas()

    def pan_fixed(self, direction):
        if not self.orig_image:
            return
        amount = 150
        if direction == "up":
            self.pan_canvas(0, amount)
        elif direction == "down":
            self.pan_canvas(0, -amount)
        elif direction == "left":
            self.pan_canvas(amount, 0)
        elif direction == "right":
            self.pan_canvas(-amount, 0)

    def on_zoom_scroll(self, event):
        if not self.orig_image:
            return
            
        cx, cy = event.x, event.y
        ix, iy = self.canvas_to_image_coords(cx, cy)
        
        if event.delta > 0 or event.num == 4:
            factor = 1.15
        else:
            factor = 0.85
            
        self.zoom_scale = max(0.05, min(10.0, self.zoom_scale * factor))
        self.pan_x = cx - ix * self.zoom_scale
        self.pan_y = cy - iy * self.zoom_scale
        
        self.redraw_canvas()

    def redraw_canvas(self):
        if not self.orig_image:
            return
            
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        img_w, img_h = self.orig_image.size
        img_src = self.get_image_source()

        # Performance Audit Fix: Viewport Cropping
        x_min = max(0, int(-self.pan_x / self.zoom_scale))
        y_min = max(0, int(-self.pan_y / self.zoom_scale))
        x_max = min(img_w, int((canvas_w - self.pan_x) / self.zoom_scale))
        y_max = min(img_h, int((canvas_h - self.pan_y) / self.zoom_scale))
        
        if x_max <= x_min or y_max <= y_min:
            return
            
        crop_box = (x_min, y_min, x_max, y_max)
        
        draw_w = int((x_max - x_min) * self.zoom_scale)
        draw_h = int((y_max - y_min) * self.zoom_scale)
        draw_w = max(1, draw_w)
        draw_h = max(1, draw_h)
        
        draw_pan_x = self.pan_x + (x_min * self.zoom_scale)
        draw_pan_y = self.pan_y + (y_min * self.zoom_scale)
            
        key = (id(img_src), draw_w, draw_h, crop_box)
        cached = self.cache_get(key)
        if cached is not None:
            self.disp_image = cached
            self.tk_image = ImageTk.PhotoImage(self.disp_image)
        else:
            self.disp_image = img_src.crop(crop_box).resize((draw_w, draw_h), Image.Resampling.NEAREST)
            self.tk_image = ImageTk.PhotoImage(self.disp_image)
            self._last_hq_key = key
            self.schedule_hq_render(key, img_src, (draw_w, draw_h), crop_box)
        
        if not hasattr(self, "_canvas_image_id") or self._canvas_image_id is None:
            self.canvas.delete("all")
            self._canvas_image_id = self.canvas.create_image(
                draw_pan_x, draw_pan_y, anchor=tk.NW, image=self.tk_image, tags="page_image"
            )
        else:
            self.canvas.coords(self._canvas_image_id, draw_pan_x, draw_pan_y)
            self.canvas.itemconfig(self._canvas_image_id, image=self.tk_image)

        self.canvas.delete("detection_box")
        self.canvas.delete("detection_label")
        self.canvas.delete("detection_text")
        self.canvas.delete("click_marker")
        
        # Draw detections
        active_count = 0
        for det in self.detections:
            if det["id"] in self.manual_deleted_ids:
                continue
            
            active_count += 1
            x, y, w, h = det["bbox"]
            
            sx = x * self.zoom_scale + self.pan_x
            sy = y * self.zoom_scale + self.pan_y
            sw = w * self.zoom_scale
            sh = h * self.zoom_scale
            
            text_str = f"#{det['id']}"
            lbl_w = len(text_str) * 8 + 10
            
            self.canvas.create_rectangle(sx, sy, sx + sw, sy + sh, outline="#2ecc71", width=2, tags="detection_box")
            self.canvas.create_rectangle(sx, sy - 15, sx + lbl_w, sy, fill="#2ecc71", width=0, tags="detection_label")
            self.canvas.create_text(sx + 3, sy - 8, text=text_str, fill="#000000", font=("Arial", 9, "bold"), anchor="w", tags="detection_text")
            
        # Draw manual added detections
        for idx, man in enumerate(self.manual_added):
            active_count += 1
            x, y, w, h = man["bbox"]
            sx = x * self.zoom_scale + self.pan_x
            sy = y * self.zoom_scale + self.pan_y
            sw = w * self.zoom_scale
            sh = h * self.zoom_scale
            
            man_text = f"+#{idx+1}"
            lbl_w = len(man_text) * 8 + 10
            
            self.canvas.create_rectangle(sx, sy, sx + sw, sy + sh, outline="#e74c3c", width=2, tags="detection_box")
            self.canvas.create_rectangle(sx, sy - 15, sx + lbl_w, sy, fill="#e74c3c", width=0, tags="detection_label")
            self.canvas.create_text(sx + 3, sy - 8, text=man_text, fill="#000000", font=("Arial", 9, "bold"), anchor="w", tags="detection_text")
            
        # Draw target selection click marker
        if hasattr(self, "select_click_coords") and self.select_click_coords is not None:
            ix, iy = self.select_click_coords
            sx = ix * self.zoom_scale + self.pan_x
            sy = iy * self.zoom_scale + self.pan_y
            size = 15
            self.canvas.create_line(sx - size, sy, sx + size, sy, fill="#e74c3c", width=2, tags="click_marker")
            self.canvas.create_line(sx, sy - size, sx, sy + size, fill="#e74c3c", width=2, tags="click_marker")
            self.canvas.create_oval(sx - 6, sy - 6, sx + 6, sy + 6, outline="#e74c3c", width=2, tags="click_marker")
            
        self.lbl_count_stats.configure(text=f"Count: {active_count} objects")

    def canvas_to_image_coords(self, cx, cy):
        ix = (cx - self.pan_x) / self.zoom_scale
        iy = (cy - self.pan_y) / self.zoom_scale
        return int(ix), int(iy)
