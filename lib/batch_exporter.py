import os
import csv
import cv2
import threading
import customtkinter as ctk
from lib.detector_engine import ColorDetectorEngine
from lib.utils import apply_window_icon

class BatchExporterMixin:
    def run_batch_export(self):
        if self.total_pages == 0:
            self.show_warning("Warning", "Please load a document first.")
            return
        if self.template_info is None:
            self.show_warning("Warning", "Please click/select a target object first.")
            return
        if self.is_batch_running:
            self.show_warning("Warning", "Batch export is already running.")
            return
            
        from tkinter import filedialog
        
        base_name = os.path.splitext(os.path.basename(self.document_path))[0]
        
        # Prompt user to choose custom output directory to resolve data location exposure findings
        chosen_dir = filedialog.askdirectory(
            initialdir=self.output_dir,
            title="Select Output Directory for summary and images"
        )
        if not chosen_dir:
            return
            
        run_output_dir = os.path.join(chosen_dir, f"{base_name}_Output")
        os.makedirs(run_output_dir, exist_ok=True)
        
        confirm = self.ask_yes_no("Confirm Batch Run", 
                                      f"Do you want to run object detection across all {self.total_pages} pages and save results to:\n{run_output_dir}?")
        if not confirm:
            return
            
        self.set_status("Running batch processing...")
        self.is_batch_running = True
        self.logger.info("batch_export_start pages=%s", self.total_pages)
        
        csv_rows = []
        csv_path = os.path.join(run_output_dir, f"{base_name}_summary.csv")
        
        progress_win = ctk.CTkToplevel(self)
        progress_win.title("Processing Pages")
        progress_win.geometry("400x150")
        progress_win.transient(self)
        progress_win.grab_set()
        apply_window_icon(progress_win, self.ico_path)
        
        # Center dialog relative to parent frame window
        progress_win.update_idletasks()
        px = self.winfo_x()
        py = self.winfo_y()
        pw = self.winfo_width()
        ph = self.winfo_height()
        x = px + (pw - 400) // 2
        y = py + (ph - 150) // 2
        progress_win.geometry(f"+{x}+{y}")
        
        lbl_p = ctk.CTkLabel(progress_win, text="Initializing...", font=ctk.CTkFont(family=self.font_family, size=14))
        lbl_p.pack(pady=20)
        
        pbar = ctk.CTkProgressBar(progress_win, width=300)
        pbar.pack(pady=10)
        pbar.set(0)
        
        self.update_idletasks()
        
        def _run_batch():
            try:
                for idx in range(self.total_pages):
                    self.after(0, lambda i=idx: lbl_p.configure(text=f"Processing Page {i + 1} of {self.total_pages}..."))
                    self.after(0, lambda i=idx: pbar.set((i + 1) / self.total_pages))

                    if self.doc_pages[idx] is None:
                        import fitz
                        if self.pdf_doc:
                            page = self.pdf_doc[idx]
                            zoom = self.dpi / 72.0
                            matrix = fitz.Matrix(zoom, zoom)
                            pix = page.get_pixmap(matrix=matrix, alpha=False)
                            import numpy as np
                            img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)
                            self.doc_pages[idx] = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
                        else:
                            self.doc_pages[idx] = cv2.imread(self.document_path)

                    img_bgr = self.doc_pages[idx]

                    dets, _ = ColorDetectorEngine.detect_objects(
                        img_bgr, self.template_info,
                        tolerance=self.slider_tolerance.get(),
                        proximity=self.slider_proximity.get(),
                        min_area_scale=self.slider_min_area.get(),
                        max_area_scale=self.slider_max_area.get()
                    )

                    page_deleted = self.page_manual_deleted_ids.get(idx, set())
                    page_added = self.page_manual_added.get(idx, [])

                    visible_dets = [d for d in dets if d["id"] not in page_deleted]
                    visible_count = len(visible_dets) + len(page_added)

                    # Cache detections back to page dictionary
                    self.page_detections[idx] = dets

                    vis_img = img_bgr.copy()

                    for det in visible_dets:
                        x, y, w, h = det["bbox"]
                        text_str = f"#{det['id']}"
                        (tw, th), _ = cv2.getTextSize(text_str, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                        cv2.rectangle(vis_img, (x, y), (x + w, y + h), (96, 204, 46), 2)
                        cv2.rectangle(vis_img, (x, y - 18), (x + tw + 4, y), (96, 204, 46), -1)
                        cv2.putText(vis_img, text_str, (x + 2, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

                    for midx, man in enumerate(page_added):
                        x, y, w, h = man["bbox"]
                        text_str = f"+#{midx+1}"
                        (tw, th), _ = cv2.getTextSize(text_str, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                        cv2.rectangle(vis_img, (x, y), (x + w, y + h), (60, 76, 231), 2)
                        cv2.rectangle(vis_img, (x, y - 18), (x + tw + 4, y), (60, 76, 231), -1)
                        cv2.putText(vis_img, text_str, (x + 2, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

                    page_img_path = os.path.join(run_output_dir, f"Page_{idx + 1:03d}_Detected.png")
                    cv2.imwrite(page_img_path, vis_img)

                    # Performance Audit Fix: Free memory for processed page if not currently viewed
                    if idx != self.current_page_idx:
                        self.doc_pages[idx] = None
                        import gc
                        gc.collect()

                    # Counting Contract:
                    # 'visible_count' represents raw detected components in the page.
                    # 'legend_count' reserves 1 count for the reference template if present.
                    # 'total' computes the net count of objects actually detected in the wild.
                    has_legend = getattr(self, "legend_var", None) is None or self.legend_var.get()
                    
                    detected_count = len(visible_dets)
                    added_count = len(page_added)
                    added_str = str(added_count) if added_count > 0 else ""

                    if has_legend:
                        legend_count = 1 if (detected_count + added_count) > 0 else 0
                        total = detected_count + added_count - legend_count
                        csv_rows.append({
                            "Page": idx + 1,
                            "File_Path": os.path.basename(page_img_path),
                            "Detected_Object": detected_count,
                            "Added_Object": added_str,
                            "Legend_Count": legend_count,
                            "Total": total
                        })
                    else:
                        total = detected_count + added_count
                        csv_rows.append({
                            "Page": idx + 1,
                            "File_Path": os.path.basename(page_img_path),
                            "Detected_Object": detected_count,
                            "Added_Object": added_str,
                            "Total": total
                        })

                total_detected = sum(row["Detected_Object"] for row in csv_rows)
                total_overall = sum(row["Total"] for row in csv_rows)
                
                total_added = sum(int(row["Added_Object"]) for row in csv_rows if row["Added_Object"] != "")
                total_added_str = str(total_added) if total_added > 0 else ""

                if has_legend:
                    total_legend = sum(row["Legend_Count"] for row in csv_rows)
                    csv_rows.append({
                        "Page": "SUM",
                        "File_Path": "",
                        "Detected_Object": total_detected,
                        "Added_Object": total_added_str,
                        "Legend_Count": total_legend,
                        "Total": total_overall
                    })
                    fieldnames = ["Page", "File_Path", "Detected_Object", "Added_Object", "Legend_Count", "Total"]
                else:
                    csv_rows.append({
                        "Page": "SUM",
                        "File_Path": "",
                        "Detected_Object": total_detected,
                        "Added_Object": total_added_str,
                        "Total": total_overall
                    })
                    fieldnames = ["Page", "File_Path", "Detected_Object", "Added_Object", "Total"]

                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_rows)

                def _on_done():
                    progress_win.destroy()
                    self.is_batch_running = False
                    self.set_status("Batch export completed successfully.")
                    self.logger.info("batch_export_complete pages=%s", self.total_pages)
                    self.show_info("Export Successful", f"Completed detection on {self.total_pages} pages.\nCSV summary and images exported to:\n{run_output_dir}")

                self.after(0, _on_done)
            except Exception:
                def _on_fail():
                    progress_win.destroy()
                    self.is_batch_running = False
                    self.set_status("Batch export failed.", is_error=True)
                    self.show_error("Export Failed", "Batch export failed. Check logs for details.")
                self.logger.exception("batch_export_failed")
                self.after(0, _on_fail)

        thread = threading.Thread(target=_run_batch)
        thread.daemon = True
        thread.start()
