import os
import customtkinter as ctk
from PIL import Image
from lib.utils import apply_window_icon

class CTkAboutDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.title(parent.app_name)
        self.geometry("450x360")
        self.resizable(False, False)
        
        # Make modal & transient
        self.transient(parent)
        self.grab_set()
        apply_window_icon(self, parent.ico_path)
        
        # Center dialog relative to parent frame window
        self.update_idletasks()
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - 450) // 2
        y = py + (ph - 360) // 2
        self.geometry(f"+{x}+{y}")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header banner frame
        hdr_frame = ctk.CTkFrame(self, height=45, fg_color="#16a085", corner_radius=0)
        hdr_frame.grid(row=0, column=0, sticky="ew")
        hdr_frame.pack_propagate(False)
        
        lbl_title = ctk.CTkLabel(
            hdr_frame, text=f"ℹ️  About {parent.app_name}", 
            font=ctk.CTkFont(family=parent.font_family, size=14, weight="bold"),
            text_color="#ffffff"
        )
        lbl_title.pack(side="left", padx=15, pady=8)
        
        # Main content area
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=15)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Display logo if it exists
        logo_row = 0
        if os.path.exists(parent.logo_path):
            try:
                pil_logo = Image.open(parent.logo_path)
                orig_w, orig_h = pil_logo.size
                new_h = 45
                new_w = int((orig_w * new_h) / orig_h)
                self.img_logo = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(new_w, new_h))
                
                lbl_logo = ctk.CTkLabel(content_frame, image=self.img_logo, text="", cursor="hand2")
                lbl_logo.grid(row=0, column=0, pady=(0, 10))
                lbl_logo.bind("<Button-1>", lambda e: webbrowser.open_new_tab(parent.app_url))
                logo_row = 1
            except Exception as e:
                parent.logger.warning("Error loading logo in about dialog: %s", e)
                
        # App Name Label
        lbl_app_name = ctk.CTkLabel(
            content_frame, text=parent.app_name, 
            font=ctk.CTkFont(family=parent.font_family, size=22, weight="bold"),
            cursor="hand2"
        )
        lbl_app_name.grid(row=logo_row, column=0, pady=(0, 2))
        lbl_app_name.bind("<Button-1>", lambda e: webbrowser.open_new_tab(parent.app_url))
        
        # Version
        lbl_version = ctk.CTkLabel(
            content_frame, text=f"Version {parent.app_version}", 
            font=ctk.CTkFont(family=parent.font_family, size=13, weight="normal"),
            text_color="gray"
        )
        lbl_version.grid(row=logo_row + 1, column=0, pady=(0, 10))
        
        # Licensing info box
        info_box = ctk.CTkFrame(content_frame, fg_color="#2b2b2b", corner_radius=6)
        info_box.grid(row=logo_row + 2, column=0, sticky="ew", padx=10, pady=5)
        info_box.grid_columnconfigure(0, weight=1)
        
        lbl_license = ctk.CTkLabel(
            info_box, text=f"Licensed To: {parent.licensed_to}", 
            font=ctk.CTkFont(family=parent.font_family, size=12)
        )
        lbl_license.grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")
        
        lbl_expiry = ctk.CTkLabel(
            info_box, text=f"Expiry Date: {parent.expiry_date} ({parent.days_left} days left)", 
            font=ctk.CTkFont(family=parent.font_family, size=12)
        )
        lbl_expiry.grid(row=1, column=0, padx=10, pady=(2, 8), sticky="w")
        
        import webbrowser
        
        # Copyright Notice
        lbl_copyright = ctk.CTkLabel(
            content_frame, text=parent.copyright_notice, 
            font=ctk.CTkFont(family=parent.font_family, size=11),
            text_color="gray", cursor="hand2"
        )
        lbl_copyright.grid(row=logo_row + 3, column=0, pady=(10, 5))
        lbl_copyright.bind("<Button-1>", lambda e: webbrowser.open_new_tab(parent.company_url))
        
        # OK Button
        btn_ok = ctk.CTkButton(
            self, text="OK", width=100,
            font=ctk.CTkFont(family=parent.font_family, size=12, weight="bold"),
            command=self.destroy
        )
        btn_ok.grid(row=2, column=0, pady=(0, 15))
        
        self.deiconify()
        self.attributes("-alpha", 1.0)
        self.wait_window(self)
