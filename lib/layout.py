import tkinter as tk
import customtkinter as ctk

class LayoutMixin:
    def create_layout(self):
        from lib.utils import load_svg_icon, ToolTip
        self.icon_about = load_svg_icon("about", (16, 16))
        self.icon_zoom_all = load_svg_icon("zoom-all", (16, 16))
        self.icon_zoom_plus = load_svg_icon("zoom-plus", (16, 16))
        self.icon_zoom_minus = load_svg_icon("zoom-minus", (16, 16))
        self.icon_pan = load_svg_icon("pan", (16, 16))
        self.icon_add = load_svg_icon("plus", (16, 16))
        self.icon_remove = load_svg_icon("minus", (16, 16))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        
        # ── LEFT SIDEBAR ──────────────────────────────────────────────────────
        self.sidebar = ctk.CTkScrollableFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_columnconfigure(0, weight=1)
        
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=12, pady=(20, 6), sticky="w")

        import webbrowser
        title_label = ctk.CTkLabel(
            title_frame, text=self.app_name,
            font=ctk.CTkFont(family=self.font_family, size=22, weight="bold"),
            cursor="hand2"
        )
        title_label.pack(side=tk.LEFT)
        title_label.bind("<Button-1>", lambda e: webbrowser.open_new_tab(self.app_url))

        version_label = ctk.CTkLabel(
            title_frame, text=f"v{self.app_version}",
            font=ctk.CTkFont(family=self.font_family, size=12),
            text_color="gray"
        )
        version_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # File Loader
        file_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        file_frame.grid(row=1, column=0, padx=12, pady=10, sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)
        
        self.btn_open = ctk.CTkButton(
            file_frame, text="Load PDF / Image", command=self.load_file, 
            font=ctk.CTkFont(family=self.font_family, size=13, weight="bold")
        )
        self.btn_open.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")
        
        self.dpi_var = ctk.StringVar(value="150")
        self.dpi_menu = ctk.CTkOptionMenu(
            file_frame, values=["150", "300", "450", "600"], 
            width=80, variable=self.dpi_var, command=self.on_dpi_changed,
            font=ctk.CTkFont(family=self.font_family, size=12)
        )
        self.dpi_menu.grid(row=0, column=1, padx=0, pady=0, sticky="e")
        
        self.lbl_file_info = ctk.CTkLabel(
            self.sidebar, text="No document loaded", 
            font=ctk.CTkFont(family=self.font_family, size=12, slant="italic"), 
            text_color="gray", wraplength=250
        )
        self.lbl_file_info.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="w")
        
        # Page Navigator
        self.nav_frame = ctk.CTkFrame(self.sidebar)
        self.nav_frame.grid(row=3, column=0, padx=12, pady=5, sticky="ew")
        self.nav_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_prev = ctk.CTkButton(
            self.nav_frame, text="◀", width=40, command=self.prev_page,
            font=ctk.CTkFont(family=self.font_family, size=12, weight="bold")
        )
        self.btn_prev.grid(row=0, column=0, padx=5, pady=5)
        
        self.lbl_page = ctk.CTkLabel(
            self.nav_frame, text="Page 0 / 0", 
            font=ctk.CTkFont(family=self.font_family, size=13, weight="bold")
        )
        self.lbl_page.grid(row=0, column=1, padx=5, pady=5)
        
        self.btn_next = ctk.CTkButton(
            self.nav_frame, text="▶", width=40, command=self.next_page,
            font=ctk.CTkFont(family=self.font_family, size=12, weight="bold")
        )
        self.btn_next.grid(row=0, column=2, padx=5, pady=5)
        
        # Target Selector
        self.btn_select_target = ctk.CTkButton(
            self.sidebar, text="🎯 Click to Select Target Object", 
            fg_color="#d35400", hover_color="#e67e22",
            font=ctk.CTkFont(family=self.font_family, size=13, weight="bold"),
            command=self.toggle_select_mode
        )
        self.btn_select_target.grid(row=4, column=0, padx=12, pady=10, sticky="ew")
        
        # Preview Pane
        self.preview_frame = ctk.CTkFrame(self.sidebar)
        self.preview_frame.grid(row=5, column=0, padx=12, pady=5, sticky="ew")
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_columnconfigure(1, weight=1)
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame, text="Selected Object Preview", 
            font=ctk.CTkFont(family=self.font_family, size=12, weight="bold")
        )
        self.preview_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 2))
        
        self.canvas_crop = tk.Canvas(self.preview_frame, width=90, height=90, bg="#2b2b2b", highlightthickness=0)
        self.canvas_crop.grid(row=1, column=0, padx=10, pady=5)
        
        self.canvas_mask = tk.Canvas(self.preview_frame, width=90, height=90, bg="#2b2b2b", highlightthickness=0)
        self.canvas_mask.grid(row=1, column=1, padx=10, pady=5)
        
        # Presets Section
        preset_frame = ctk.CTkFrame(self.sidebar)
        preset_frame.grid(row=6, column=0, padx=12, pady=10, sticky="ew")
        preset_frame.grid_columnconfigure(0, weight=1)
        
        preset_lbl = ctk.CTkLabel(
            preset_frame, text="Settings Profile / Preset", 
            font=ctk.CTkFont(family=self.font_family, size=12, weight="bold")
        )
        preset_lbl.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 2), sticky="w")
        
        self.preset_var = ctk.StringVar(value="None")
        self.preset_menu = ctk.CTkOptionMenu(
            preset_frame, variable=self.preset_var, command=self.apply_preset,
            font=ctk.CTkFont(family=self.font_family, size=12)
        )
        self.preset_menu.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="ew")
        
        self.btn_save_preset = ctk.CTkButton(
            preset_frame, text="Save As...", width=80, command=self.save_preset_dialog,
            font=ctk.CTkFont(family=self.font_family, size=12, weight="bold")
        )
        self.btn_save_preset.grid(row=1, column=1, padx=(5, 10), pady=5)
        
        # Sliders Section
        sliders_frame = ctk.CTkFrame(self.sidebar)
        sliders_frame.grid(row=7, column=0, padx=12, pady=5, sticky="ew")
        sliders_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_tolerance = ctk.CTkLabel(
            sliders_frame, text=f"Color Tolerance (Range Extension): {self.def_tolerance:.2f}",
            font=ctk.CTkFont(family=self.font_family, size=12)
        )
        self.lbl_tolerance.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")
        self.slider_tolerance = ctk.CTkSlider(sliders_frame, from_=0.0, to=1.0, command=self.on_param_changed)
        self.slider_tolerance.set(self.def_tolerance)
        self.slider_tolerance.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        
        self.lbl_min_area = ctk.CTkLabel(
            sliders_frame, text=f"Min Object Size Filter: {self.def_min_area:.2f}x",
            font=ctk.CTkFont(family=self.font_family, size=12)
        )
        self.lbl_min_area.grid(row=2, column=0, padx=10, pady=(5, 0), sticky="w")
        self.slider_min_area = ctk.CTkSlider(sliders_frame, from_=0.01, to=1.5, command=self.on_param_changed)
        self.slider_min_area.set(self.def_min_area)
        self.slider_min_area.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="ew")
        
        self.lbl_max_area = ctk.CTkLabel(
            sliders_frame, text=f"Max Object Size Filter: {self.def_max_area:.2f}x",
            font=ctk.CTkFont(family=self.font_family, size=12)
        )
        self.lbl_max_area.grid(row=4, column=0, padx=10, pady=(5, 0), sticky="w")
        self.slider_max_area = ctk.CTkSlider(sliders_frame, from_=1.0, to=15.0, command=self.on_param_changed)
        self.slider_max_area.set(self.def_max_area)
        self.slider_max_area.grid(row=5, column=0, padx=10, pady=(0, 5), sticky="ew")
        
        self.lbl_proximity = ctk.CTkLabel(
            sliders_frame, text=f"Proximity Clustering: {int(self.def_proximity)} px",
            font=ctk.CTkFont(family=self.font_family, size=12)
        )
        self.lbl_proximity.grid(row=6, column=0, padx=10, pady=(5, 0), sticky="w")
        self.slider_proximity = ctk.CTkSlider(sliders_frame, from_=5.0, to=300.0, command=self.on_param_changed)
        self.slider_proximity.set(self.def_proximity)
        self.slider_proximity.grid(row=7, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        self.switch_live_preview = ctk.CTkSwitch(
            self.sidebar, text="Live Color Mask Overlay", command=self.on_live_toggle,
            font=ctk.CTkFont(family=self.font_family, size=12)
        )
        self.switch_live_preview.grid(row=8, column=0, padx=12, pady=10, sticky="w")
        
        self.btn_run_count = ctk.CTkButton(
            self.sidebar, text="⚡ Run Object Detection", 
            fg_color="#27ae60", hover_color="#2ecc71", 
            font=ctk.CTkFont(family=self.font_family, size=14, weight="bold"),
            command=self.run_detection
        )
        self.btn_run_count.grid(row=9, column=0, padx=12, pady=10, sticky="ew")
        
        self.btn_batch = ctk.CTkButton(
            self.sidebar, text="📦 Export Batch Results (All Pages)", 
            command=self.run_batch_export,
            font=ctk.CTkFont(family=self.font_family, size=13, weight="bold")
        )
        self.btn_batch.grid(row=10, column=0, padx=12, pady=5, sticky="ew")
        
        self.legend_var = tk.BooleanVar(value=self.def_legend)
        self.switch_legend = ctk.CTkSwitch(
            self.sidebar, text="Legend", variable=self.legend_var,
            font=ctk.CTkFont(family=self.font_family, size=12)
        )
        self.switch_legend.grid(row=11, column=0, padx=12, pady=10, sticky="w")
        
        self.lbl_count_stats = ctk.CTkLabel(
            self.sidebar, text="Count: 0 objects", 
            font=ctk.CTkFont(family=self.font_family, size=16, weight="bold")
        )
        self.lbl_count_stats.grid(row=12, column=0, padx=12, pady=10, sticky="w")
        
        # Footer — status only (About moved to top bar)
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.grid(row=13, column=0, padx=12, pady=(15, 10), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)
        
        self.lbl_status = ctk.CTkLabel(
            footer_frame, text="App Ready.", 
            font=ctk.CTkFont(family=self.font_family, size=11), 
            text_color="#2ecc71", wraplength=230, justify="left"
        )
        self.lbl_status.grid(row=0, column=0, pady=5, sticky="w")
        
        # ── MAIN CANVAS WORKSPACE ─────────────────────────────────────────────
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#1e1e1e")
        self.canvas_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # ── TOP HEADER BAR ────────────────────────────────────────────────────
        self.header_bar = ctk.CTkFrame(self.canvas_frame, height=40, fg_color="transparent")
        self.header_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(5, 0))
        
        # 1. About button — far right
        self.btn_about = ctk.CTkButton(
            self.header_bar, text="", image=self.icon_about, width=28, height=28, 
            fg_color="#6c3483", hover_color="#7d3c98",
            command=self.show_about_dialog
        )
        self.btn_about.pack(side=tk.RIGHT, padx=(6, 0))
        ToolTip(self.btn_about, "About PlanMiner")

        # 2. Reset button - next on the right
        self.btn_reset = ctk.CTkButton(
            self.header_bar, text="🗑", width=28, height=28, 
            fg_color="#c0392b", hover_color="#cd6155",
            font=ctk.CTkFont(family=self.font_family, size=14, weight="bold"),
            command=self.reset_to_clean_state
        )
        self.btn_reset.pack(side=tk.RIGHT, padx=(2, 0))
        ToolTip(self.btn_reset, "Reset Document & Settings")

        # 3. Sidebar toggle - far left
        self.btn_toggle_sidebar = ctk.CTkButton(
            self.header_bar, text="◀ Hide Sidebar", width=110, height=28, 
            fg_color="#2c3e50", hover_color="#34495e",
            font=ctk.CTkFont(family=self.font_family, size=12, weight="bold"),
            command=self.toggle_sidebar
        )
        self.btn_toggle_sidebar.pack(side=tk.LEFT)

        # 4. Separator
        sep1 = ctk.CTkLabel(self.header_bar, text="|", text_color="#555555", width=6)
        sep1.pack(side=tk.LEFT, padx=6)

        # 5. Zoom Group (Zoom In, Zoom Out, Box Zoom)
        self.btn_zoom_in = ctk.CTkButton(
            self.header_bar, text="", image=self.icon_zoom_plus, width=28, height=28, 
            fg_color="#1e8449", hover_color="#27ae60",
            command=lambda: self.adjust_zoom_fixed(1.2)
        )
        self.btn_zoom_in.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_zoom_in, "Zoom In")
        
        self.btn_zoom_out = ctk.CTkButton(
            self.header_bar, text="", image=self.icon_zoom_minus, width=28, height=28, 
            fg_color="#922b21", hover_color="#c0392b",
            command=lambda: self.adjust_zoom_fixed(0.8)
        )
        self.btn_zoom_out.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_zoom_out, "Zoom Out")
        
        self.btn_zoom_window = ctk.CTkButton(
            self.header_bar, text="🔍", width=28, height=28, 
            fg_color="#b7770d", hover_color="#d4a017",
            font=ctk.CTkFont(family=self.font_family, size=13, weight="bold"),
            command=self.toggle_zoom_window_mode
        )
        self.btn_zoom_window.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_zoom_window, "Box Zoom")

        # 6. Separator
        sep2 = ctk.CTkLabel(self.header_bar, text="|", text_color="#555555", width=6)
        sep2.pack(side=tk.LEFT, padx=6)

        # 7. Mouse pan button
        self.mouse_pan_active = False
        self.btn_mouse_pan = ctk.CTkButton(
            self.header_bar, text="", image=self.icon_pan, width=28, height=28, 
            fg_color="#138d75", hover_color="#16a085",
            command=self.toggle_mouse_pan
        )
        self.btn_mouse_pan.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_mouse_pan, "Hand Panning Mode")

        # 8. Separator
        sep3 = ctk.CTkLabel(self.header_bar, text="|", text_color="#555555", width=6)
        sep3.pack(side=tk.LEFT, padx=6)

        # 9. Fit Page button
        self.btn_zoom_reset = ctk.CTkButton(
            self.header_bar, text="", image=self.icon_zoom_all, width=28, height=28, 
            fg_color="#1a7abf", hover_color="#2980b9",
            command=self.reset_zoom_button
        )
        self.btn_zoom_reset.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_zoom_reset, "Fit Page to Screen")

        # 10. Separator
        sep4 = ctk.CTkLabel(self.header_bar, text="|", text_color="#555555", width=6)
        sep4.pack(side=tk.LEFT, padx=6)

        # 11. Add / Delete button and the helper text
        self.add_mode_active = False
        self.btn_obj_add = ctk.CTkButton(
            self.header_bar, text="", image=self.icon_add, width=28, height=28,
            fg_color="#2c3e50", hover_color="#34495e",
            command=self.toggle_add_mode
        )
        self.btn_obj_add.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_obj_add, "Add Box Mode (Left-click canvas to place)")

        self.remove_mode_active = False
        self.btn_obj_remove = ctk.CTkButton(
            self.header_bar, text="", image=self.icon_remove, width=28, height=28,
            fg_color="#2c3e50", hover_color="#34495e",
            command=self.toggle_remove_mode
        )
        self.btn_obj_remove.pack(side=tk.LEFT, padx=2)
        ToolTip(self.btn_obj_remove, "Delete Box Mode (Left-click boxes to remove)")

        self.lbl_nav_tip = ctk.CTkLabel(
            self.header_bar, text="Select Add / Delete tool to edit boxes",
            font=ctk.CTkFont(family=self.font_family, size=11, weight="bold"),
            text_color="lime"
        )
        self.lbl_nav_tip.pack(side=tk.LEFT, padx=(10, 0))
        ToolTip(self.btn_obj_add, "Add Box Mode (Left-click canvas to place)")
        
        # Scrollable / Panning Main Canvas
        self.canvas = tk.Canvas(self.canvas_frame, bg="#181818", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Event Bindings for Main Canvas
        self.canvas.bind("<ButtonPress-1>", self.on_left_click)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)
        self.canvas.bind("<B3-Motion>", self.on_pan_drag)
        self.canvas.bind("<MouseWheel>", self.on_zoom_scroll)
        self.canvas.bind("<Button-4>", self.on_zoom_scroll)
        self.canvas.bind("<Button-5>", self.on_zoom_scroll)
        
        self.canvas.bind("<Configure>", self.on_canvas_resize)
