"""
ui/progress_widget.py
iOS-styled animated processing progress bar.
"""
import customtkinter as ctk
import threading
import time

# iOS colors
_BLUE = "#007AFF"
_GREEN = "#34C759"
_RED = "#FF3B30"
_TEAL = "#5AC8FA"
_FILL = ("#E5E5EA", "#3A3A3C")
_LABEL = ("#8E8E93", "#8E8E93")
_FONT = "Segoe UI"


class ProcessingProgress(ctk.CTkFrame):
    """iOS-styled animated progress bar."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", height=38, **kwargs)
        self._running = False
        self._finished = False
        self._on_complete = None

        self.bar = ctk.CTkProgressBar(
            self, width=400, height=4, corner_radius=2,
            progress_color=_BLUE,
            fg_color=_FILL
        )
        self.bar.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
        self.bar.set(0)

        self.pct_label = ctk.CTkLabel(
            self, text="0%",
            font=ctk.CTkFont(family=_FONT, size=12, weight="bold"),
            text_color=_BLUE, width=45
        )
        self.pct_label.pack(side="right", pady=10)

        self.status_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family=_FONT, size=11),
            text_color=_LABEL, width=90
        )
        self.status_label.pack(side="right", padx=(0, 6), pady=10)

        self.pack_forget()

    def start(self):
        self._running = True
        self._finished = False
        self.bar.set(0)
        self.pct_label.configure(text="0%", text_color=_BLUE)
        self.status_label.configure(text="Processing…")
        self.bar.configure(progress_color=_BLUE)
        self.pack(fill="x", pady=(4, 4))
        threading.Thread(target=self._animate, daemon=True).start()

    def _animate(self):
        current = 0.0
        # Phase 1: fast to 85%
        while current < 0.85 and self._running and not self._finished:
            step = 0.03 + (0.85 - current) * 0.05
            current = min(current + step, 0.85)
            self._set_ui(current)
            time.sleep(0.05)
        # Phase 2: slow to 95%
        while current < 0.95 and self._running and not self._finished:
            current = min(current + 0.002, 0.95)
            self._set_ui(current)
            time.sleep(0.15)
        # Phase 3: stall
        while current < 0.99 and self._running and not self._finished:
            current = min(current + 0.001, 0.99)
            self._set_ui(current)
            time.sleep(0.3)

    def _set_ui(self, val):
        try:
            self.after(0, lambda: self._apply(val))
        except Exception:
            pass

    def _apply(self, val):
        self.bar.set(val)
        self.pct_label.configure(text=f"{int(val * 100)}%")
        if val >= 0.85:
            self.bar.configure(progress_color=_TEAL)

    def finish(self, on_complete=None):
        self._finished = True
        self._running = False
        self._on_complete = on_complete
        threading.Thread(target=self._burst, daemon=True).start()

    def _burst(self):
        current = 0.85
        while current < 1.0:
            current = min(current + 0.04, 1.0)
            try:
                self.after(0, lambda v=current: self._apply(v))
            except Exception:
                break
            time.sleep(0.02)
        time.sleep(0.15)
        try:
            self.after(0, self._done)
        except Exception:
            pass

    def _done(self):
        self.bar.set(1.0)
        self.pct_label.configure(text="100%", text_color=_GREEN)
        self.status_label.configure(text="Done")
        self.bar.configure(progress_color=_GREEN)
        if self._on_complete:
            self._on_complete()

    def reset(self):
        self._running = False
        self._finished = False
        self.bar.set(0)
        self.pct_label.configure(text="0%")
        self.status_label.configure(text="")
        self.pack_forget()

    def error(self, msg="Failed"):
        self._running = False
        self._finished = True
        self.bar.configure(progress_color=_RED)
        self.pct_label.configure(text_color=_RED)
        self.status_label.configure(text=msg)
