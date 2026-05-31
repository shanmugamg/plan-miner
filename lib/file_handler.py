import os
import threading
import time
import fitz
import cv2
import numpy as np
from tkinter import filedialog
from PIL import Image, ImageTk

class FileHandlerMixin:
    def load_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.input_dir,
            title="Select PDF or Image",
            filetypes=[("PDF/Images", "*.pdf;*.png;*.jpg;*.jpeg;*.bmp"), ("PDF files", "*.pdf"), ("Image files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not file_path:
            return

        if not self.validate_input_file(file_path):
            return
            
        self.document_path = file_path
        self.lbl_file_info.configure(text=os.path.basename(file_path))
        self.set_status("Loading document...")
        
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2,
            text="Loading Document... Please Wait...", fill="#95a5a6",
            font=("Arial", 16, "bold"), tags="loading"
        )
        self.update_idletasks()
        
        # Security Audit Fix: Sanitize filename in logs to protect PII
        import hashlib
        safe_name_hash = hashlib.sha256(os.path.basename(file_path).encode()).hexdigest()[:8]
        ext = os.path.splitext(file_path)[1].lower()
        self.logger.info("file_load sanitized_name=doc_%s%s", safe_name_hash, ext)
        
        if self.pdf_doc:
            try:
                self.pdf_doc.close()
            except Exception as e:
                self.logger.warning("Error closing PDF document: %s", e)
            self.pdf_doc = None
            
        self.page_detections = {}
        self.page_manual_added = {}
        self.page_manual_deleted_ids = {}
            
        self.current_page_idx = 0
        self.dpi = int(self.dpi_var.get())
        
        ext = os.path.splitext(self.document_path)[1].lower()
        if ext == ".pdf":
            try:
                self.pdf_doc = fitz.open(self.document_path)
                self.total_pages = len(self.pdf_doc)
                self.doc_pages = [None] * self.total_pages
                self.set_status("PDF loaded. Rendering page 1...")
                self.show_page(0)
            except Exception as e:
                self.set_status("Error loading PDF.", is_error=True)
                self.show_error("Error Loading PDF", str(e))
                self.logger.exception("pdf_load_failed sanitized_name=doc_%s%s", safe_name_hash, ext)
        else:
            self.total_pages = 1
            self.doc_pages = [None]
            self.set_status("Loading image...")
            self.show_page(0)

    def show_page(self, index):
        if self.total_pages == 0:
            return
            
        # Performance Audit Fix: Release memory from previously cached pages
        for i in range(self.total_pages):
            if i != index and self.doc_pages[i] is not None:
                self.doc_pages[i] = None
        import gc
        gc.collect()
        
        self.current_page_idx = index
        self.lbl_page.configure(text=f"Page {index + 1} / {self.total_pages}")
        
        if self.doc_pages[index] is not None:
            self.display_rendered_page(index)
        else:
            if self.is_loading_page:
                return
            self.is_loading_page = True
            
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2,
                text="Loading Page... Please Wait...", fill="#95a5a6",
                font=("Arial", 16, "bold"), tags="loading"
            )
            self.set_status("Rendering page layout...")
            
            thread = threading.Thread(target=self.async_render_page, args=(index,))
            thread.daemon = True
            thread.start()

        self.logger.info("page_show index=%s", index)

    def async_render_page(self, index):
        start = time.time()
        try:
            if self.pdf_doc:
                page = self.pdf_doc[index]
                zoom = self.dpi / 72.0
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)
                img_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            else:
                img_bgr = cv2.imread(self.document_path)
                if img_bgr is None:
                    raise ValueError("Failed to read image via OpenCV.")
            
            self.doc_pages[index] = img_bgr
            elapsed_ms = int((time.time() - start) * 1000)
            self.logger.info("page_rendered index=%s dpi=%s ms=%s", index, self.dpi, elapsed_ms)
            self.after(0, lambda: self.finish_page_load(index))
        except Exception as e:
            self.logger.exception("page_render_failed index=%s", index)
            self.after(0, lambda: self.on_page_load_failed(str(e)))

    def finish_page_load(self, index):
        self.is_loading_page = False
        self.set_status("Page rendered.")
        self.display_rendered_page(index)

    def on_page_load_failed(self, err_msg):
        self.is_loading_page = False
        self.set_status("Rendering failed.", is_error=True)
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2,
            text=f"Failed to load: {err_msg}", fill="#e74c3c",
            font=("Arial", 14, "bold")
        )

    def display_rendered_page(self, index):
        img_bgr = self.doc_pages[index]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        self.orig_image = Image.fromarray(img_rgb)
        
        self.reset_zoom()
        
        self.select_click_coords = None
        self.live_mask = None
        self.live_mask_signature = None
        self.live_overlay_rgb = None
        self.live_overlay_pil = None
        self._image_cache = {}
        self._image_cache_order = []
        self._canvas_image_id = None
        self._hq_after_id = None
        self._last_hq_key = None
        self.redraw_canvas()

    def prev_page(self):
        if self.current_page_idx > 0:
            self.show_page(self.current_page_idx - 1)

    def next_page(self):
        if self.current_page_idx < self.total_pages - 1:
            self.show_page(self.current_page_idx + 1)

    def on_dpi_changed(self, value):
        if self.document_path:
            self.set_status("Reloading page DPI...")
            self.dpi = int(value)
            self.doc_pages = [None] * self.total_pages
            self.show_page(self.current_page_idx)

    def validate_input_file(self, file_path):
        warn_max_mb = 200
        hard_max_mb = 300
        if not os.path.exists(file_path):
            self.show_error("Invalid File", "File does not exist.")
            return False
        if os.path.isdir(file_path):
            self.show_error("Invalid File", "Folders are not supported.")
            return False
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > hard_max_mb:
            self.show_error("File Too Large", f"File is {size_mb:.1f} MB. Files larger than {hard_max_mb} MB are not supported to prevent system instability.")
            return False
        elif size_mb > warn_max_mb:
            self.show_warning("Large File", f"File is {size_mb:.1f} MB. Loading may be slow.")
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".pdf", ".png", ".jpg", ".jpeg", ".bmp"]:
            self.show_error("Unsupported File", "Supported types: PDF, PNG, JPG, JPEG, BMP.")
            return False
            
        # Magic number check
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                if ext == ".pdf" and not header.startswith(b"%PDF"):
                    self.show_error("Invalid Content", "File extension is PDF but contents do not match.")
                    return False
                elif ext in [".png"] and not header.startswith(b"\x89PNG"):
                    self.show_error("Invalid Content", "File extension is PNG but contents do not match.")
                    return False
                elif ext in [".jpg", ".jpeg"] and not header.startswith(b"\xFF\xD8"):
                    self.show_error("Invalid Content", "File extension is JPG but contents do not match.")
                    return False
        except Exception as e:
            self.show_error("Error Reading File", f"Could not read file contents: {e}")
            return False
            
        return True

    def reset_to_clean_state(self):
        if not self.ask_yes_no("Confirm Reset", "Are you sure you want to reset the current document and settings?"):
            return
        # 1. Close open PDF/document
        if self.pdf_doc:
            try:
                self.pdf_doc.close()
            except:
                pass
            self.pdf_doc = None
            
        # 2. Reset model/logic variables
        self.document_path = None
        self.doc_pages = []
        self.total_pages = 0
        self.current_page_idx = 0
        self.orig_image = None
        self.disp_image = None
        self.tk_image = None
        
        self.template_info = None
        self.select_click_coords = None
        self.page_detections = {}
        self.page_manual_added = {}
        self.page_manual_deleted_ids = {}
        
        self.live_mask = None
        self.live_mask_signature = None
        self.live_overlay_rgb = None
        self.live_overlay_pil = None
        self._image_cache = {}
        self._image_cache_order = []
        self._canvas_image_id = None
        self._hq_after_id = None
        self._last_hq_key = None
        
        # 3. Reset UI element states
        self.lbl_file_info.configure(text="No document loaded")
        self.lbl_page.configure(text="Page 0 / 0")
        self.lbl_count_stats.configure(text="Count: 0 objects")
        
        if hasattr(self, "preset_var"):
            self.preset_var.set("None")
            
        if hasattr(self, "slider_tolerance"):
            self.slider_tolerance.set(self.def_tolerance)
        if hasattr(self, "slider_min_area"):
            self.slider_min_area.set(self.def_min_area)
        if hasattr(self, "slider_max_area"):
            self.slider_max_area.set(self.def_max_area)
        if hasattr(self, "slider_proximity"):
            self.slider_proximity.set(self.def_proximity)
            
        # Update slider label texts
        if hasattr(self, "on_param_changed"):
            try:
                self.on_param_changed(None)
            except Exception as e:
                self.logger.warning("Error calling on_param_changed during reset: %s", e)
                
        if hasattr(self, "switch_live_preview"):
            try:
                self.switch_live_preview.deselect()
            except Exception as e:
                self.logger.warning("Error deselecting live preview during reset: %s", e)

        if hasattr(self, "legend_var"):
            self.legend_var.set(self.def_legend)
        if hasattr(self, "switch_legend"):
            try:
                if self.def_legend:
                    self.switch_legend.select()
                else:
                    self.switch_legend.deselect()
            except Exception as e:
                self.logger.warning("Error resetting legend switch during reset: %s", e)
                
        # Clear crop and mask preview canvases
        if hasattr(self, "canvas_crop"):
            self.canvas_crop.delete("all")
        if hasattr(self, "canvas_mask"):
            self.canvas_mask.delete("all")
            
        # Reset mode states
        self.select_mode_active = False
        if hasattr(self, "btn_select_target"):
            self.btn_select_target.configure(text="🎯 Click to Select Target Object", fg_color="#d35400")
            
        self.add_mode_active = False
        if hasattr(self, "btn_obj_add"):
            self.btn_obj_add.configure(fg_color="#2c3e50", hover_color="#34495e")
            
        self.remove_mode_active = False
        if hasattr(self, "btn_obj_remove"):
            self.btn_obj_remove.configure(fg_color="#2c3e50", hover_color="#34495e")

        self.mouse_pan_active = False
        if hasattr(self, "btn_mouse_pan"):
            self.btn_mouse_pan.configure(fg_color="#138d75")
            
        self.zoom_window_active = False
        if hasattr(self, "btn_zoom_window"):
            self.btn_zoom_window.configure(fg_color="#b7770d")
            
        # Clear main canvas
        self.canvas.delete("all")
        
        self.set_status("Application reset. Ready to load new document.")
        self.logger.info("application_reset")
