"""
ui/tabs/conversion_ui.py — iOS-styled conversion tab.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os, threading, tempfile, shutil, gc
from utils.logger import get_logger, log_operation
from ui.progress_widget import ProcessingProgress
from ui import ios_widgets as ios

logger = get_logger("conversion_ui")


class ConversionTab(ctk.CTkFrame):
    FORMATS_FROM = [
        "Images (PNG)", "Images (JPEG)", "Word (DOCX)", "Excel (XLSX)",
        "PowerPoint (PPTX)", "HTML", "Markdown", "Plain Text",
        "CSV (Tables)", "JSON", "XML", "PDF/A"
    ]
    FORMATS_TO = ["Images → PDF", "HTML → PDF", "Markdown → PDF"]

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=ios.BG)
        self.app = app
        self.selected_file = None
        self.to_pdf_files = []
        self._result_path = None
        self._result_paths = []
        self._to_result_path = None
        self.process_from_btn = None
        self.cancel_from_btn = None
        self.process_to_btn = None
        self.cancel_to_btn = None
        self._build_ui()

    def _build_ui(self):
        c = ios.ios_scrollable(self)
        c.pack(fill="both", expand=True, padx=16, pady=8)

        # ── FROM PDF ──
        ios.ios_section_label(c, "CONVERT FROM PDF")
        card = ios.ios_card(c, "Export PDF", "Convert your PDF to other formats")

        # File select
        pk = ctk.CTkFrame(card, fg_color="transparent"); pk.pack(fill="x", padx=18, pady=(0, 8))
        self.file_label = ios.ios_label(pk, "No file selected", color=ios.LABEL_TER)
        self.file_label.pack(side="left")
        ios.ios_select_btn(pk, "Select PDF", self._pick_input).pack(side="right")

        # Format
        of = ctk.CTkFrame(card, fg_color="transparent"); of.pack(fill="x", padx=18, pady=4)
        ios.ios_label(of, "Format").pack(side="left")
        self.fmt_var = ctk.StringVar(value=self.FORMATS_FROM[0])
        ios.ios_option_menu(of, self.FORMATS_FROM, self.fmt_var, width=200).pack(side="left", padx=12)

        # DPI
        df = ctk.CTkFrame(card, fg_color="transparent"); df.pack(fill="x", padx=18, pady=4)
        ios.ios_label(df, "DPI").pack(side="left")
        self.dpi_var = ctk.IntVar(value=200)
        ios.ios_slider(df, 72, 600, self.dpi_var).pack(side="left", padx=12)
        self.dpi_lbl = ios.ios_label(df, "200", size=12)
        self.dpi_lbl.pack(side="left")
        # DPI label update handled via trace
        self.dpi_var.trace_add("write", lambda *_: self.dpi_lbl.configure(text=str(self.dpi_var.get())))

        # Buttons
        bf = ctk.CTkFrame(card, fg_color="transparent"); bf.pack(fill="x", padx=18)
        self.process_from_btn = ios.ios_process_btn(bf, self._process_from)
        self.process_from_btn.pack(side="left", padx=5, pady=(0, 12))
        self.cancel_from_btn = ios.ios_cancel_btn(bf, lambda: self.app.cancel_event.set())
        self.save_from_btn = ios.ios_save_btn(bf, self._save_from)

        self.from_progress = ProcessingProgress(card)

        # ── TO PDF ──
        ios.ios_section_label(c, "CONVERT TO PDF")
        card2 = ios.ios_card(c, "Import to PDF", "Create PDF from images, HTML, or Markdown")

        pk2 = ctk.CTkFrame(card2, fg_color="transparent"); pk2.pack(fill="x", padx=18, pady=(0, 8))
        self.to_label = ios.ios_label(pk2, "No files selected", color=ios.LABEL_TER)
        self.to_label.pack(side="left")
        ios.ios_select_btn(pk2, "Select Files", self._pick_to).pack(side="right")

        tf = ctk.CTkFrame(card2, fg_color="transparent"); tf.pack(fill="x", padx=18, pady=4)
        ios.ios_label(tf, "Type").pack(side="left")
        self.to_fmt_var = ctk.StringVar(value=self.FORMATS_TO[0])
        ios.ios_option_menu(tf, self.FORMATS_TO, self.to_fmt_var, width=200).pack(side="left", padx=12)

        bf2 = ctk.CTkFrame(card2, fg_color="transparent"); bf2.pack(fill="x", padx=18)
        self.process_to_btn = ios.ios_process_btn(bf2, self._process_to)
        self.process_to_btn.pack(side="left", padx=5, pady=(0, 12))
        self.cancel_to_btn = ios.ios_cancel_btn(bf2, lambda: self.app.cancel_event.set())
        self.save_to_btn = ios.ios_save_btn(bf2, self._save_to)

        self.to_progress = ProcessingProgress(card2)

        # Log
        ios.ios_section_label(c, "LOG")
        self.log_box = ios.ios_log_box(c, 100)
        self.log_box.pack(fill="x", pady=(0, 10))

    def _log(self, m): self.log_box.insert("end", m+"\n"); self.log_box.see("end"); logger.info(m)

    def _pick_input(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p:
            self.selected_file = p
            self.file_label.configure(text=os.path.basename(p), text_color=ios.LABEL)
            self.save_from_btn.pack_forget(); self.from_progress.reset()

    def _pick_to(self):
        fmt = self.to_fmt_var.get()
        ft = [("Images", "*.png *.jpg *.jpeg *.bmp *.tiff")] if "Images" in fmt else \
             [("HTML", "*.html *.htm")] if "HTML" in fmt else [("Markdown", "*.md")]
        ps = filedialog.askopenfilenames(filetypes=ft)
        if ps:
            self.to_pdf_files = list(ps)
            self.to_label.configure(text=f"{len(ps)} file(s) selected", text_color=ios.LABEL)
            self.save_to_btn.pack_forget(); self.to_progress.reset()

    def _process_from(self):
        if not self.selected_file: messagebox.showwarning("PDFOS", "Select a PDF file first."); return
        fmt = self.fmt_var.get(); dpi = self.dpi_var.get()
        self.app.set_status(f"Processing → {fmt}…")
        self._log(f"Converting {os.path.basename(self.selected_file)} → {fmt}")
        self.save_from_btn.pack_forget(); self.process_from_btn.pack_forget()
        self.cancel_from_btn.pack(side="left", padx=5, pady=(0, 12))
        self.app.cancel_event.clear()
        self.from_progress.start()

        def work():
            try:
                from core import conversion
                inp = self.selected_file; tmp = tempfile.mkdtemp(prefix="pdfos_")
                if "Images" in fmt:
                    ext = "png" if "PNG" in fmt else "jpg"
                    self._result_paths = conversion.pdf_to_images(inp, tmp, fmt=ext, dpi=dpi, cancel_event=self.app.cancel_event); self._result_path = tmp
                elif fmt == "Word (DOCX)": o=os.path.join(tmp,"out.docx"); conversion.pdf_to_docx(inp,o); self._result_path=o
                elif fmt == "Excel (XLSX)": o=os.path.join(tmp,"out.xlsx"); conversion.pdf_to_xlsx(inp,o); self._result_path=o
                elif fmt == "PowerPoint (PPTX)": o=os.path.join(tmp,"out.pptx"); conversion.pdf_to_pptx(inp,o,dpi=dpi, cancel_event=self.app.cancel_event); self._result_path=o
                elif fmt == "HTML": o=os.path.join(tmp,"out.html"); conversion.pdf_to_html(inp,o, cancel_event=self.app.cancel_event); self._result_path=o
                elif fmt == "Markdown": o=os.path.join(tmp,"out.md"); conversion.pdf_to_markdown(inp,o, cancel_event=self.app.cancel_event); self._result_path=o
                elif fmt == "Plain Text": o=os.path.join(tmp,"out.txt"); conversion.pdf_to_text(inp,o); self._result_path=o
                elif fmt == "CSV (Tables)": o=os.path.join(tmp,"out.csv"); conversion.pdf_to_csv(inp,o); self._result_path=o
                elif fmt == "JSON": o=os.path.join(tmp,"out.json"); conversion.pdf_to_json(inp,o); self._result_path=o
                elif fmt == "XML": o=os.path.join(tmp,"out.xml"); conversion.pdf_to_xml(inp,o); self._result_path=o
                elif fmt == "PDF/A": o=os.path.join(tmp,"out.pdf"); conversion.pdf_to_pdfa(inp,o); self._result_path=o
                
                if self.app.cancel_event.is_set(): raise Exception("Cancelled by user")
                
                log_operation("conversion", f"to_{fmt}", inp, success=True)
                self._log("✓ Done"); self.app.set_status("Ready to save")
                self.from_progress.finish(on_complete=lambda: [self.cancel_from_btn.pack_forget(), self.save_from_btn.pack(side="left", padx=5, pady=(0,12))])
                gc.collect()
            except Exception as e:
                log_operation("conversion", f"to_{fmt}", inp, error=str(e), success=False)
                self._log(f"✗ {e}"); self.from_progress.error(str(e) if "Cancel" in str(e) else "Failed")
                self.cancel_from_btn.pack_forget(); self.process_from_btn.pack(side="left", padx=5, pady=(0, 12))
        threading.Thread(target=work, daemon=True).start()

    def _save_from(self):
        if not self._result_path: return
        fmt = self.fmt_var.get()
        if "Images" in fmt and self._result_paths:
            d = filedialog.askdirectory(title="Save images")
            if d:
                for f in self._result_paths: shutil.copy2(f, d)
                self._log(f"Saved {len(self._result_paths)} images")
                shutil.rmtree(os.path.dirname(self._result_paths[0]), ignore_errors=True)
        else:
            ext_map = {"Word (DOCX)":".docx","Excel (XLSX)":".xlsx","PowerPoint (PPTX)":".pptx",
                       "HTML":".html","Markdown":".md","Plain Text":".txt","CSV (Tables)":".csv",
                       "JSON":".json","XML":".xml","PDF/A":".pdf"}
            ext = ext_map.get(fmt, ".pdf")
            d = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[("File",f"*{ext}")])
            if d: shutil.copy2(self._result_path, d); self._log(f"Saved to {d}"); shutil.rmtree(os.path.dirname(self._result_path), ignore_errors=True)
        self.save_from_btn.pack_forget(); self.from_progress.reset()
        self._result_path=None; self._result_paths=[]; self.app.set_status("Saved")

    def _process_to(self):
        if not self.to_pdf_files: messagebox.showwarning("PDFOS", "Select files first."); return
        fmt = self.to_fmt_var.get()
        self.save_to_btn.pack_forget(); self.process_to_btn.pack_forget()
        self.cancel_to_btn.pack(side="left", padx=5, pady=(0, 12))
        self.app.cancel_event.clear()
        self.to_progress.start()
        def work():
            try:
                from core import conversion
                tmp = os.path.join(tempfile.mkdtemp(prefix="pdfos_"), "out.pdf")
                if "Images" in fmt: conversion.images_to_pdf(self.to_pdf_files, tmp, cancel_event=self.app.cancel_event)
                elif "HTML" in fmt: conversion.html_to_pdf(self.to_pdf_files[0], tmp)
                elif "Markdown" in fmt: conversion.markdown_to_pdf(self.to_pdf_files[0], tmp)
                self._to_result_path = tmp
                if self.app.cancel_event.is_set(): raise Exception("Cancelled by user")
                self._log("✓ Done"); self.to_progress.finish(on_complete=lambda: [self.cancel_to_btn.pack_forget(), self.save_to_btn.pack(side="left",padx=5,pady=(0,12))])
                gc.collect()
            except Exception as e:
                self._log(f"✗ {e}")
                self.to_progress.error(str(e) if "Cancel" in str(e) else "Failed")
                self.cancel_to_btn.pack_forget(); self.process_to_btn.pack(side="left", padx=5, pady=(0, 12))
        threading.Thread(target=work, daemon=True).start()

    def _save_to(self):
        if not self._to_result_path: return
        d = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if d: shutil.copy2(self._to_result_path, d); self._log(f"Saved to {d}"); shutil.rmtree(os.path.dirname(self._to_result_path), ignore_errors=True)
        self.save_to_btn.pack_forget(); self.to_progress.reset(); self._to_result_path=None; self.app.set_status("Saved")
