"""
ui/tabs/page_manip_ui.py — iOS-styled page manipulation tab.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os, threading, tempfile, shutil, gc
from utils.logger import get_logger, log_operation
from ui.progress_widget import ProcessingProgress
from ui import ios_widgets as ios

logger = get_logger("page_manip_ui")


class PageManipTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=ios.BG)
        self.app = app
        self._results = {}
        self._progress = {}
        self._saves = {}
        self._processes = {}
        self._cancels = {}
        self._build_ui()

    def _build_ui(self):
        c = ios.ios_scrollable(self)
        c.pack(fill="both", expand=True, padx=16, pady=8)

        self._build_merge(c)
        self._build_split(c)
        self._build_rotate(c)
        self._build_delete(c)
        self._build_extract(c)
        self._build_reverse(c)
        self._build_crop(c)

        ios.ios_section_label(c, "LOG")
        self.log_box = ios.ios_log_box(c, 90)
        self.log_box.pack(fill="x", pady=(0, 10))

    def _log(self, m): self.log_box.insert("end", m+"\n"); self.log_box.see("end"); logger.info(m)

    def _make_btns(self, card, key):
        bf = ctk.CTkFrame(card, fg_color="transparent"); bf.pack(fill="x", padx=18)
        self._processes[key] = ios.ios_process_btn(bf, lambda: getattr(self, f"_do_{key}")())
        self._processes[key].pack(side="left", padx=5, pady=(0, 12))
        self._cancels[key] = ios.ios_cancel_btn(bf, lambda: self.app.cancel_event.set())
        self._saves[key] = ios.ios_save_btn(bf, lambda k=key: self._save(k))
        self._progress[key] = ProcessingProgress(card)

    def _save(self, k):
        rp = self._results.get(k)
        if not rp: return
        if isinstance(rp, list):
            d = filedialog.askdirectory(title="Save files")
            if d:
                for f in rp: shutil.copy2(f, d)
                self._log(f"Saved {len(rp)} files"); shutil.rmtree(os.path.dirname(rp[0]), ignore_errors=True)
        else:
            d = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
            if d: shutil.copy2(rp, d); self._log(f"Saved to {d}"); shutil.rmtree(os.path.dirname(rp), ignore_errors=True)
        self._results[k]=None; self._saves[k].pack_forget(); self._progress[k].reset(); self.app.set_status("Saved")

    def _run(self, key, func):
        self._saves[key].pack_forget(); self._processes[key].pack_forget()
        self._cancels[key].pack(side="left", padx=5, pady=(0, 12))
        self.app.cancel_event.clear()
        self._progress[key].start()
        def w():
            try:
                func()
                if self.app.cancel_event.is_set(): raise Exception("Cancelled by user")
                self._log("✓ Done"); sb = self._saves[key]
                self._progress[key].finish(on_complete=lambda: [self._cancels[key].pack_forget(), sb.pack(side="left",padx=5,pady=(0,12))]); gc.collect()
            except Exception as e:
                self._log(f"✗ {e}")
                self._progress[key].error(str(e) if "Cancel" in str(e) else "Failed")
                self._cancels[key].pack_forget(); self._processes[key].pack(side="left", padx=5, pady=(0, 12))
        threading.Thread(target=w, daemon=True).start()

    # ── MERGE ──
    def _build_merge(self, c):
        card = ios.ios_card(c, "Merge PDFs", "Combine multiple PDFs into one")
        self._merge_files = []
        r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0,8))
        self.merge_label = ios.ios_label(r, "No files selected", color=ios.LABEL_TER); self.merge_label.pack(side="left")
        ios.ios_select_btn(r, "Select PDFs", self._pick_merge).pack(side="right")
        self._make_btns(card, "merge")

    def _pick_merge(self):
        fs = filedialog.askopenfilenames(filetypes=[("PDF","*.pdf")])
        if fs: self._merge_files=list(fs); self.merge_label.configure(text=f"{len(fs)} PDFs selected", text_color=ios.LABEL)

    def _do_merge(self):
        if len(self._merge_files)<2: messagebox.showinfo("PDFOS","Select 2+ PDFs."); return
        def f():
            from core.page_manipulation import merge_pdfs
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"merged.pdf"); merge_pdfs(self._merge_files,t,cancel_event=self.app.cancel_event); self._results["merge"]=t
        self._run("merge", f)

    # ── SPLIT ──
    def _build_split(self, c):
        card = ios.ios_card(c, "Split PDF", "Split into pages or custom ranges")
        r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0,8))
        ios.ios_label(r, "Ranges").pack(side="left")
        self.split_entry = ios.ios_entry(r, 180, "e.g. 1-3, 5-5 or blank"); self.split_entry.pack(side="left", padx=12)
        self._make_btns(card, "split")

    def _do_split(self):
        inp = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if not inp: return
        rt = self.split_entry.get().strip(); ranges=None
        if rt:
            try: ranges=[(int(s),int(e)) for s,e in (p.strip().split("-") for p in rt.split(","))]
            except: messagebox.showerror("PDFOS","Invalid range."); return
        def f():
            from core.page_manipulation import split_pdf
            t=tempfile.mkdtemp(prefix="pdfos_"); r=split_pdf(inp,t,ranges,cancel_event=self.app.cancel_event); self._results["split"]=r
        self._run("split", f)

    # ── ROTATE ──
    def _build_rotate(self, c):
        card = ios.ios_card(c, "Rotate Pages", "Rotate specific or all pages")
        r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0,8))
        ios.ios_label(r, "Angle").pack(side="left")
        self.rot_angle = ctk.StringVar(value="90")
        ios.ios_option_menu(r, ["90","180","270"], self.rot_angle, 80).pack(side="left", padx=12)
        ios.ios_label(r, "Pages").pack(side="left", padx=(12,0))
        self.rot_pages = ios.ios_entry(r, 120, "Blank = all"); self.rot_pages.pack(side="left", padx=8)
        self._make_btns(card, "rotate")

    def _do_rotate(self):
        inp = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if not inp: return
        angle=int(self.rot_angle.get()); pt=self.rot_pages.get().strip()
        pages=[int(p.strip()) for p in pt.split(",")] if pt else None
        def f():
            from core.page_manipulation import rotate_pages
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"rotated.pdf"); rotate_pages(inp,t,pages or [],angle,cancel_event=self.app.cancel_event); self._results["rotate"]=t
        self._run("rotate", f)

    # ── DELETE ──
    def _build_delete(self, c):
        card = ios.ios_card(c, "Delete Pages", "Remove specific pages")
        r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0,8))
        ios.ios_label(r, "Pages").pack(side="left")
        self.del_entry = ios.ios_entry(r, 180, "e.g. 2, 4, 6"); self.del_entry.pack(side="left", padx=12)
        self._make_btns(card, "delete")

    def _do_delete(self):
        inp = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if not inp: return
        pt=self.del_entry.get().strip()
        if not pt: messagebox.showwarning("PDFOS","Enter pages."); return
        pages=[int(p.strip()) for p in pt.split(",")]
        def f():
            from core.page_manipulation import delete_pages
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"del.pdf"); delete_pages(inp,t,pages,cancel_event=self.app.cancel_event); self._results["delete"]=t
        self._run("delete", f)

    # ── EXTRACT ──
    def _build_extract(self, c):
        card = ios.ios_card(c, "Extract Pages", "Extract specific pages into new PDF")
        r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0,8))
        ios.ios_label(r, "Pages").pack(side="left")
        self.ext_entry = ios.ios_entry(r, 180, "e.g. 1, 3, 5"); self.ext_entry.pack(side="left", padx=12)
        self._make_btns(card, "extract")

    def _do_extract(self):
        inp = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if not inp: return
        pt=self.ext_entry.get().strip()
        if not pt: messagebox.showwarning("PDFOS","Enter pages."); return
        pages=[int(p.strip()) for p in pt.split(",")]
        def f():
            from core.page_manipulation import extract_pages
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"ext.pdf"); extract_pages(inp,t,pages,cancel_event=self.app.cancel_event); self._results["extract"]=t
        self._run("extract", f)

    # ── REVERSE ──
    def _build_reverse(self, c):
        card = ios.ios_card(c, "Reverse Order", "Reverse all page order")
        self._make_btns(card, "reverse")

    def _do_reverse(self):
        inp = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if not inp: return
        def f():
            from core.page_manipulation import reverse_pages
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"rev.pdf"); reverse_pages(inp,t,cancel_event=self.app.cancel_event); self._results["reverse"]=t
        self._run("reverse", f)

    # ── CROP ──
    def _build_crop(self, c):
        card = ios.ios_card(c, "Crop Pages", "Trim margins from all pages (in points)")
        r = ctk.CTkFrame(card, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0,8))
        self.crop_e = {}
        for lbl in ["Left","Top","Right","Bottom"]:
            ios.ios_label(r, lbl, size=11).pack(side="left", padx=(8,2))
            e = ios.ios_entry(r, 50, "0"); e.pack(side="left"); self.crop_e[lbl.lower()] = e
        self._make_btns(card, "crop")

    def _do_crop(self):
        inp = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if not inp: return
        try: l,t,r,b = [float(self.crop_e[k].get() or 0) for k in ("left","top","right","bottom")]
        except ValueError: messagebox.showerror("PDFOS","Numbers only."); return
        def f():
            from core.page_manipulation import crop_pages
            tp=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"crop.pdf"); crop_pages(inp,tp,l,t,r,b,pages=None,cancel_event=self.app.cancel_event); self._results["crop"]=tp
        self._run("crop", f)
