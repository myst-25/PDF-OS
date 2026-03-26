"""
ui/viewer.py
Embedded PDF viewer component using PyMuPDF rendering.
"""
import customtkinter as ctk
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io


class PDFViewer(ctk.CTkFrame):
    """Reusable PDF viewer widget with page navigation and zoom."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0

        self._build_ui()

    def _build_ui(self):
        # Navigation bar
        nav = ctk.CTkFrame(self, height=40, fg_color=("gray88", "gray20"))
        nav.pack(fill="x", padx=5, pady=(5, 0))

        self.btn_prev = ctk.CTkButton(
            nav, text="◀ Prev", width=70, height=28,
            command=self.prev_page,
            fg_color="#0f3460", hover_color="#e94560"
        )
        self.btn_prev.pack(side="left", padx=5, pady=5)

        self.page_label = ctk.CTkLabel(
            nav, text="No PDF loaded",
            font=ctk.CTkFont(size=12)
        )
        self.page_label.pack(side="left", padx=10, pady=5)

        self.btn_next = ctk.CTkButton(
            nav, text="Next ▶", width=70, height=28,
            command=self.next_page,
            fg_color="#0f3460", hover_color="#e94560"
        )
        self.btn_next.pack(side="left", padx=5, pady=5)

        # Zoom controls
        self.btn_zoom_out = ctk.CTkButton(
            nav, text="−", width=30, height=28,
            command=self.zoom_out,
            fg_color="gray40", hover_color="gray50"
        )
        self.btn_zoom_out.pack(side="right", padx=(0, 5), pady=5)

        self.zoom_label = ctk.CTkLabel(
            nav, text="100%", font=ctk.CTkFont(size=11), width=50
        )
        self.zoom_label.pack(side="right", padx=2, pady=5)

        self.btn_zoom_in = ctk.CTkButton(
            nav, text="+", width=30, height=28,
            command=self.zoom_in,
            fg_color="gray40", hover_color="gray50"
        )
        self.btn_zoom_in.pack(side="right", padx=(5, 0), pady=5)

        # Canvas for rendering
        self.canvas_frame = ctk.CTkScrollableFrame(self, fg_color=("gray85", "gray17"))
        self.canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.image_label = ctk.CTkLabel(self.canvas_frame, text="Drop a PDF or use the file picker above")
        self.image_label.pack(expand=True, padx=20, pady=40)

    def load_pdf(self, path: str):
        """Load a PDF file into the viewer."""
        try:
            if self.doc:
                self.doc.close()
            self.doc = fitz.open(path)
            self.total_pages = len(self.doc)
            self.current_page = 0
            self._render_page()
        except Exception as e:
            self.page_label.configure(text=f"Error: {e}")

    def _render_page(self):
        """Render the current page."""
        if not self.doc or self.total_pages == 0:
            return

        page = self.doc[self.current_page]
        zoom = self.zoom_level * 1.5  # Base zoom for good quality
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Convert to CTkImage
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(pix.width, pix.height))

        self.image_label.configure(image=ctk_img, text="")
        self.image_label._image = ctk_img  # Keep reference

        self.page_label.configure(
            text=f"Page {self.current_page + 1} of {self.total_pages}"
        )
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self._render_page()

    def next_page(self):
        if self.doc and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._render_page()

    def zoom_in(self):
        if self.zoom_level < 3.0:
            self.zoom_level += 0.25
            self._render_page()

    def zoom_out(self):
        if self.zoom_level > 0.25:
            self.zoom_level -= 0.25
            self._render_page()

    def close(self):
        if self.doc:
            self.doc.close()
            self.doc = None
