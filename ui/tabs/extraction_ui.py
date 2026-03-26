"""
ui/tabs/extraction_ui.py — iOS-styled extraction tab.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os, json, threading, gc
from utils.logger import get_logger, log_operation
from ui.progress_widget import ProcessingProgress
from ui import ios_widgets as ios

logger = get_logger("extraction_ui")


class ExtractionTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=ios.BG)
        self.app = app
        self.loaded_file = None
        self._last_result = ""
        self._build_ui()

    def _build_ui(self):
        c = ios.ios_scrollable(self)
        c.pack(fill="both", expand=True, padx=16, pady=8)

        # File Picker
        pk_card = ios.ios_card(c, "Source PDF", "Load a PDF to extract data from")
        pk = ctk.CTkFrame(pk_card, fg_color="transparent"); pk.pack(fill="x", padx=18, pady=(0,14))
        self.file_label = ios.ios_label(pk, "No file loaded", color=ios.LABEL_TER); self.file_label.pack(side="left")
        ios.ios_select_btn(pk, "Load PDF", self._load).pack(side="right")

        # Tool grid
        ios.ios_section_label(c, "EXTRACTION TOOLS")
        tools_card = ios.ios_card(c, "Select Tool")
        tf = ctk.CTkFrame(tools_card, fg_color="transparent"); tf.pack(fill="x", padx=14, pady=(0,12))

        tool_btns = [
            ("Text", self._ext_text, ios.BLUE), ("Images", self._ext_images, ios.TEAL),
            ("Tables", self._ext_tables, ios.PURPLE), ("Metadata", self._ext_meta, ios.INDIGO),
            ("Fonts", self._ext_fonts, ios.ORANGE), ("Links", self._ext_links, ios.GREEN),
            ("Bookmarks", self._ext_bmarks, ios.BLUE), ("Attachments", self._ext_attach, ios.RED),
        ]
        row = None
        for i, (label, cmd, color) in enumerate(tool_btns):
            if i % 4 == 0:
                row = ctk.CTkFrame(tf, fg_color="transparent"); row.pack(fill="x", pady=3)
            ctk.CTkButton(
                row, text=label, height=36, width=140, corner_radius=8,
                fg_color=ios.FILL, hover_color=color,
                text_color=ios.LABEL,
                font=ctk.CTkFont(family=ios.FONT, size=12, weight="bold"),
                command=cmd
            ).pack(side="left", padx=4, pady=2)

        # Search
        ios.ios_section_label(c, "SEARCH")
        sc = ios.ios_card(c, "Full-Text Search")
        sf = ctk.CTkFrame(sc, fg_color="transparent"); sf.pack(fill="x", padx=18, pady=(0,12))
        self.search_entry = ios.ios_entry(sf, 280, "Search query…"); self.search_entry.pack(side="left")
        ios.ios_button(sf, "Search", self._search, width=90, height=32).pack(side="left", padx=10)

        # Progress
        self.progress = ProcessingProgress(c)

        # Results
        res_row = ctk.CTkFrame(c, fg_color="transparent"); res_row.pack(fill="x", pady=(6,3))
        ios.ios_label(res_row, "Results", size=13, weight="bold").pack(side="left")
        self.export_btn = ios.ios_button(res_row, "Export", self._export, ios.GREEN, 100, 30)
        self.export_btn.pack(side="right"); self.export_btn.pack_forget()

        self.results_box = ctk.CTkTextbox(
            c, height=250, corner_radius=10,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=ios.CARD_BG
        )
        self.results_box.pack(fill="both", expand=True, pady=(0,10))

    def _load(self):
        p = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if p: self.loaded_file=p; self.file_label.configure(text=os.path.basename(p), text_color=ios.LABEL)
        logger.info(f"Loaded: {p}")

    def _ok(self):
        if not self.loaded_file: messagebox.showwarning("PDFOS","Load a PDF first."); return False
        return True

    def _show(self, t):
        self._last_result = t
        self.results_box.delete("1.0","end"); self.results_box.insert("1.0", t)
        self.export_btn.pack(side="right")

    def _export(self):
        if not self._last_result: return
        d = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")])
        if d:
            with open(d,"w",encoding="utf-8") as f: f.write(self._last_result)
            self.app.set_status(f"Exported")

    def _run(self, name, func):
        self.export_btn.pack_forget(); self.progress.start()
        def w():
            try:
                func()
                self.progress.finish(on_complete=lambda: self.export_btn.pack(side="right"))
                gc.collect()
            except Exception as e: self._show(f"Error: {e}"); self.progress.error("Failed")
        threading.Thread(target=w, daemon=True).start()

    def _ext_text(self):
        if not self._ok(): return
        def f():
            from core.extraction import extract_text; t=extract_text(self.loaded_file)
            self._show(t if t.strip() else "(No text found)"); self.app.set_status("Text extracted")
        self._run("text", f)

    def _ext_images(self):
        if not self._ok(): return
        od=filedialog.askdirectory(title="Output folder")
        if not od: return
        def f():
            from core.extraction import extract_images; r=extract_images(self.loaded_file,od)
            self._show(f"Extracted {len(r)} images:\n"+"\n".join(r)); self.app.set_status(f"{len(r)} images")
        self._run("images", f)

    def _ext_tables(self):
        if not self._ok(): return
        def f():
            from core.extraction import extract_tables; tables=extract_tables(self.loaded_file)
            if not tables: self._show("No tables found."); return
            t=""
            for tb in tables:
                t+=f"\n— Table (Page {tb['page']}) —\n"
                for row in tb["data"]: t+=" | ".join(str(c) if c else "" for c in row)+"\n"
            self._show(t)
        self._run("tables", f)

    def _ext_meta(self):
        if not self._ok(): return
        def f():
            from core.extraction import extract_metadata; m=extract_metadata(self.loaded_file)
            self._show(json.dumps(m,indent=2,ensure_ascii=False))
        self._run("metadata", f)

    def _ext_fonts(self):
        if not self._ok(): return
        def f():
            from core.extraction import extract_fonts; fs=extract_fonts(self.loaded_file)
            self._show("Fonts:\n"+"\n".join(f"  • {x['name']} ({x['encoding']})" for x in fs) if fs else "No fonts.")
        self._run("fonts", f)

    def _ext_links(self):
        if not self._ok(): return
        def f():
            from core.extraction import extract_hyperlinks; ls=extract_hyperlinks(self.loaded_file)
            self._show(f"{len(ls)} links:\n"+"\n".join(f"  p{l['page']}: {l['uri']}" for l in ls) if ls else "No links.")
        self._run("links", f)

    def _ext_bmarks(self):
        if not self._ok(): return
        def f():
            from core.extraction import extract_bookmarks; bs=extract_bookmarks(self.loaded_file)
            self._show("Bookmarks:\n"+"\n".join(f"{'  '*(b['level']-1)}• {b['title']} → p{b['page']}" for b in bs) if bs else "No bookmarks.")
        self._run("bookmarks", f)

    def _ext_attach(self):
        if not self._ok(): return
        od=filedialog.askdirectory(title="Output folder")
        if not od: return
        def f():
            from core.extraction import extract_attachments; r=extract_attachments(self.loaded_file,od)
            self._show(f"{len(r)} attachments:\n"+"\n".join(r) if r else "No attachments.")
        self._run("attachments", f)

    def _search(self):
        if not self._ok(): return
        q=self.search_entry.get().strip()
        if not q: return
        def f():
            from core.extraction import full_text_search; r=full_text_search(self.loaded_file,q)
            self._show(f"{len(r)} matches for '{q}':\n"+"\n".join(f"  Page {x['page']}" for x in r) if r else f"No matches for '{q}'.")
        self._run("search", f)
