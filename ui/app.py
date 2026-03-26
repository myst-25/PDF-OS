"""
ui/app.py
Main application window — iOS-inspired design system.
Uses Inter/Segoe UI as SF Pro alternatives, iOS color palette, clean rounded cards.
"""
import customtkinter as ctk
import sys
import webbrowser
import os
import gc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from utils.resource_monitor import ResourceMonitor, cleanup_memory

logger = get_logger("app")


class PDFOSApp(ctk.CTk):
    """Main PDFOS application — iOS-inspired design."""

    CATEGORIES = [
        ("arrow.2.squarepath", "Conversion", "conversion"),
        ("doc.on.doc", "Pages", "pages"),
        ("pencil.and.outline", "Editing", "editing"),
        ("magnifyingglass", "Extraction", "extraction"),
        ("lock.shield", "Security", "security"),
        ("bolt.circle", "Optimize", "optimization"),
    ]

    # iOS-style SF Symbol text alternatives
    ICONS = {
        "conversion": "⇄",
        "pages": "☰",
        "editing": "✎",
        "extraction": "⊕",
        "security": "⊘",
        "optimization": "⚡",
    }

    # ── iOS Color Palette ──
    # (light_mode, dark_mode)
    IOS = {
        # Backgrounds
        "bg":               ("#F2F2F7", "#000000"),
        "bg_secondary":     ("#FFFFFF", "#1C1C1E"),
        "bg_tertiary":      ("#F2F2F7", "#2C2C2E"),
        "bg_grouped":       ("#F2F2F7", "#000000"),

        # Sidebar
        "sidebar_bg":       ("#F2F2F7", "#1C1C1E"),
        "sidebar_active":   ("#E8E8ED", "#3A3A3C"),
        "sidebar_hover":    ("#ECECF0", "#2C2C2E"),

        # Text
        "label":            ("#000000", "#FFFFFF"),
        "label_secondary":  ("#3C3C43", "#EBEBF5"),
        "label_tertiary":   ("#8E8E93", "#8E8E93"),
        "label_quaternary": ("#C7C7CC", "#48484A"),

        # Tints
        "blue":             "#007AFF",
        "green":            "#34C759",
        "red":              "#FF3B30",
        "orange":           "#FF9500",
        "yellow":           "#FFCC00",
        "purple":           "#AF52DE",
        "teal":             "#5AC8FA",
        "indigo":           "#5856D6",

        # Separators
        "separator":        ("#C6C6C8", "#38383A"),

        # Fill
        "fill":             ("#E5E5EA", "#3A3A3C"),
        "fill_secondary":   ("#D1D1D6", "#48484A"),

        # Card
        "card":             ("#FFFFFF", "#1C1C1E"),
        "card_border":      ("#E5E5EA", "#38383A"),

        # Header
        "header_bg":        ("#F9F9F9", "#1C1C1E"),

        # Status
        "status_bg":        ("#F2F2F7", "#000000"),
    }

    # iOS-like font (Segoe UI on Windows is closest to SF Pro)
    FONT_FAMILY = "Segoe UI"

    def __init__(self):
        super().__init__()
        self.title("PDFOS — PDF - OS (Open Source)")
        self.geometry("1380x880")
        self.minsize(1080, 700)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.active_category = None
        self.tab_frames = {}
        self.sidebar_buttons = {}
        self.sidebar_indicators = {}

        self.configure(fg_color=self.IOS["bg"])

        self._build_layout()
        self._build_sidebar()
        self._build_header()
        self._build_content_area()
        self._build_status_bar()
        self._init_tabs()
        self._switch_tab("conversion")

        # Resource monitor
        self.resource_monitor = ResourceMonitor(callback=self._on_resource_update, interval=2.0)
        self.resource_monitor.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        logger.info("Shutting down")
        self.resource_monitor.stop()
        cleanup_memory()
        self.destroy()

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    # ── SIDEBAR ──
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=240, corner_radius=0,
            fg_color=self.IOS["sidebar_bg"],
            border_width=0
        )
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsw")
        self.sidebar.grid_propagate(False)

        # ─ App branding ─
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=95)
        brand.pack(fill="x")
        brand.pack_propagate(False)

        # Load icon if exists
        icon_png = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "assets", "icon.png")
        brand_inner = ctk.CTkFrame(brand, fg_color="transparent")
        brand_inner.pack(anchor="w", padx=20, pady=(18, 0))

        if os.path.exists(icon_png):
            from PIL import Image
            pil_img = Image.open(icon_png).resize((36, 36), Image.LANCZOS)
            self._app_icon = ctk.CTkImage(pil_img, pil_img, size=(36, 36))
            ctk.CTkLabel(brand_inner, image=self._app_icon, text="").pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            brand_inner, text="PDFOS",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=22, weight="bold"),
            text_color=self.IOS["label"]
        ).pack(side="left")

        ctk.CTkLabel(
            brand, text="   PDF - OS (Open Source)",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=10),
            text_color=self.IOS["label_tertiary"], anchor="w"
        ).pack(fill="x", pady=(2, 0))

        # Separator
        ctk.CTkFrame(self.sidebar, height=1, fg_color=self.IOS["separator"]).pack(
            fill="x", padx=16, pady=(8, 12))

        # Section label
        ctk.CTkLabel(
            self.sidebar, text="   TOOLS",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=11, weight="bold"),
            text_color=self.IOS["label_tertiary"], anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 6))

        # ─ Category buttons ─
        for _, label, key in self.CATEGORIES:
            icon = self.ICONS.get(key, "•")

            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=44)
            btn_frame.pack(fill="x", padx=10, pady=1)
            btn_frame.pack_propagate(False)

            # Active indicator (thin left bar)
            indicator = ctk.CTkFrame(btn_frame, width=3, fg_color="transparent", corner_radius=2)
            indicator.pack(side="left", fill="y", padx=(2, 0))
            self.sidebar_indicators[key] = indicator

            btn = ctk.CTkButton(
                btn_frame, text=f"  {icon}   {label}",
                font=ctk.CTkFont(family=self.FONT_FAMILY, size=14),
                height=40, anchor="w", corner_radius=10,
                fg_color="transparent",
                text_color=self.IOS["label"],
                hover_color=self.IOS["sidebar_hover"],
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left", fill="both", expand=True, padx=(4, 6))
            self.sidebar_buttons[key] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # ─ Bottom controls ─
        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkButton(
            bottom, text="Free Memory",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=12),
            height=32, corner_radius=8,
            fg_color=self.IOS["fill"],
            hover_color=self.IOS["fill_secondary"],
            text_color=self.IOS["label_secondary"],
            command=self._manual_gc
        ).pack(fill="x", pady=(0, 8))

        self.theme_var = ctk.StringVar(value="dark")
        ctk.CTkSwitch(
            bottom, text="Light Mode",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=12),
            text_color=self.IOS["label_tertiary"],
            variable=self.theme_var, onvalue="light", offvalue="dark",
            command=self._toggle_theme,
            progress_color=self.IOS["green"],
            button_color="#FFFFFF",
            button_hover_color="#E5E5EA"
        ).pack(pady=4)

    # ── HEADER ──
    def _build_header(self):
        self.header = ctk.CTkFrame(
            self, height=56, corner_radius=0,
            fg_color=self.IOS["header_bg"],
            border_width=0
        )
        self.header.grid(row=0, column=1, sticky="new")
        self.header.grid_propagate(False)

        # Bottom border line
        sep = ctk.CTkFrame(self.header, height=1, fg_color=self.IOS["separator"])
        sep.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        self.header_title = ctk.CTkLabel(
            self.header, text="Conversion",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=18, weight="bold"),
            text_color=self.IOS["label"]
        )
        self.header_title.pack(side="left", padx=24, pady=14)

        # ── Social Links + Resource Monitor (right side) ──
        res_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        res_frame.pack(side="right", padx=20, pady=10)

        # Social links
        ctk.CTkButton(
            res_frame, text="GitHub", width=60, height=24, corner_radius=6,
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=10),
            fg_color=self.IOS["fill"], hover_color=self.IOS["fill_secondary"],
            text_color=self.IOS["label_secondary"],
            command=lambda: webbrowser.open("https://github.com/myst-25")
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            res_frame, text="Telegram", width=70, height=24, corner_radius=6,
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=10),
            fg_color=self.IOS["fill"], hover_color=self.IOS["fill_secondary"],
            text_color=self.IOS["label_secondary"],
            command=lambda: webbrowser.open("https://t.me/Myst_25")
        ).pack(side="right", padx=(6, 0))

        # RAM
        ram_c = ctk.CTkFrame(res_frame, fg_color="transparent")
        ram_c.pack(side="right", padx=(14, 0))
        ctk.CTkLabel(
            ram_c, text="RAM",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=9, weight="bold"),
            text_color=self.IOS["label_tertiary"]
        ).pack()
        self.ram_bar = ctk.CTkProgressBar(
            ram_c, width=70, height=6, corner_radius=3,
            progress_color=self.IOS["purple"],
            fg_color=self.IOS["fill"]
        )
        self.ram_bar.pack(pady=(2, 0))
        self.ram_bar.set(0)
        self.ram_label = ctk.CTkLabel(
            ram_c, text="0 MB",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=9),
            text_color=self.IOS["label_tertiary"]
        )
        self.ram_label.pack()

        # CPU
        cpu_c = ctk.CTkFrame(res_frame, fg_color="transparent")
        cpu_c.pack(side="right", padx=(14, 0))
        ctk.CTkLabel(
            cpu_c, text="CPU",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=9, weight="bold"),
            text_color=self.IOS["label_tertiary"]
        ).pack()
        self.cpu_bar = ctk.CTkProgressBar(
            cpu_c, width=70, height=6, corner_radius=3,
            progress_color=self.IOS["blue"],
            fg_color=self.IOS["fill"]
        )
        self.cpu_bar.pack(pady=(2, 0))
        self.cpu_bar.set(0)
        self.cpu_label = ctk.CTkLabel(
            cpu_c, text="0%",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=9),
            text_color=self.IOS["label_tertiary"]
        )
        self.cpu_label.pack()

    # ── CONTENT ──
    def _build_content_area(self):
        self.content_wrapper = ctk.CTkFrame(self, fg_color=self.IOS["bg"])
        self.content_wrapper.grid(row=1, column=1, sticky="nsew")
        self.content_wrapper.grid_columnconfigure(0, weight=1)
        self.content_wrapper.grid_rowconfigure(0, weight=1)

    # ── STATUS BAR ──
    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(
            self, height=24, corner_radius=0,
            fg_color=self.IOS["status_bg"]
        )
        self.status_bar.grid(row=2, column=1, sticky="sew")
        self.status_bar.grid_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_bar, text="  Ready",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=10),
            text_color=self.IOS["label_tertiary"], anchor="w"
        )
        self.status_label.pack(side="left", padx=12, fill="x")

        self.version_label = ctk.CTkLabel(
            self.status_bar, text="v1.2  ",
            font=ctk.CTkFont(family=self.FONT_FAMILY, size=9),
            text_color=self.IOS["label_quaternary"]
        )
        self.version_label.pack(side="right", padx=10)

    # ── TABS ──
    def _init_tabs(self):
        from ui.tabs.conversion_ui import ConversionTab
        from ui.tabs.page_manip_ui import PageManipTab
        from ui.tabs.editing_ui import EditingTab
        from ui.tabs.extraction_ui import ExtractionTab
        from ui.tabs.security_ui import SecurityTab
        from ui.tabs.optimization_ui import OptimizationTab

        tab_map = {
            "conversion": ConversionTab, "pages": PageManipTab, "editing": EditingTab,
            "extraction": ExtractionTab, "security": SecurityTab, "optimization": OptimizationTab,
        }
        for key, cls in tab_map.items():
            frame = cls(self.content_wrapper, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.tab_frames[key] = frame

    def _switch_tab(self, key: str):
        titles = {
            "conversion": "Conversion", "pages": "Pages",
            "editing": "Editing", "extraction": "Extraction",
            "security": "Security", "optimization": "Optimize",
        }
        for k, btn in self.sidebar_buttons.items():
            if k == key:
                btn.configure(fg_color=self.IOS["sidebar_active"])
                self.sidebar_indicators[k].configure(fg_color=self.IOS["blue"])
            else:
                btn.configure(fg_color="transparent")
                self.sidebar_indicators[k].configure(fg_color="transparent")

        self.header_title.configure(text=titles.get(key, ""))
        if key in self.tab_frames:
            self.tab_frames[key].tkraise()
        self.active_category = key
        logger.debug(f"Tab → {key}")

    def set_status(self, message: str):
        self.status_label.configure(text=f"  {message}")
        self.update_idletasks()

    def _on_resource_update(self, cpu, ram_mb, ram_pct):
        try:
            self.after(0, self._update_resource_ui, cpu, ram_mb, ram_pct)
        except Exception:
            pass

    def _update_resource_ui(self, cpu, ram_mb, ram_pct):
        self.cpu_bar.set(min(cpu / 100.0, 1.0))
        self.cpu_label.configure(text=f"{cpu:.1f}%")
        self.ram_bar.set(min(ram_pct / 100.0, 1.0))
        self.ram_label.configure(text=f"{ram_mb:.0f} MB")

        # iOS-style color thresholds
        if cpu > 80:
            self.cpu_bar.configure(progress_color=self.IOS["red"])
        elif cpu > 50:
            self.cpu_bar.configure(progress_color=self.IOS["orange"])
        else:
            self.cpu_bar.configure(progress_color=self.IOS["blue"])

        if ram_mb > 400:
            self.ram_bar.configure(progress_color=self.IOS["red"])
        elif ram_mb > 200:
            self.ram_bar.configure(progress_color=self.IOS["orange"])
        else:
            self.ram_bar.configure(progress_color=self.IOS["purple"])

    def _manual_gc(self):
        collected = cleanup_memory()
        self.set_status(f"Freed {collected} objects")
        logger.info(f"Manual GC: freed {collected}")

    def _toggle_theme(self):
        mode = self.theme_var.get()
        ctk.set_appearance_mode(mode)
        logger.info(f"Theme → {mode}")


# Expose iOS colors globally for tabs to use
IOS_COLORS = PDFOSApp.IOS
IOS_FONT = PDFOSApp.FONT_FAMILY


def run():
    app = PDFOSApp()
    app.mainloop()


if __name__ == "__main__":
    run()
