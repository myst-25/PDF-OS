"""
ui/tabs/editing_ui.py — iOS-styled editing tab.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os, threading, tempfile, shutil, gc
from utils.logger import get_logger, log_operation
from ui.progress_widget import ProcessingProgress
from ui import ios_widgets as ios

logger = get_logger("editing_ui")


class EditingTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=ios.BG)
        self.app = app
        self._results = {}; self._progress = {}; self._saves = {}; self._processes = {}; self._cancels = {}
        self._build_ui()

    def _build_ui(self):
        c = ios.ios_scrollable(self)
        c.pack(fill="both", expand=True, padx=16, pady=8)

        # Text Watermark
        wc = ios.ios_card(c, "Text Watermark", "Add diagonal text overlay")
        r = ctk.CTkFrame(wc, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(r, "Text").pack(side="left")
        self.wm_text = ios.ios_entry(r, 180, "CONFIDENTIAL"); self.wm_text.pack(side="left", padx=10)
        ios.ios_label(r, "Size").pack(side="left", padx=(8,0))
        self.wm_size = ios.ios_entry(r, 50, "60"); self.wm_size.pack(side="left", padx=6)
        self._make_btns(wc, "wm")

        # Image Watermark
        ic = ios.ios_card(c, "Image Watermark", "Add logo or image overlay")
        self._make_btns(ic, "imgwm")

        # Header
        hc = ios.ios_card(c, "Add Header", "Insert header text on every page")
        r2 = ctk.CTkFrame(hc, fg_color="transparent"); r2.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(r2, "Text").pack(side="left")
        self.hdr_text = ios.ios_entry(r2, 250, "Document Title"); self.hdr_text.pack(side="left", padx=10)
        self._make_btns(hc, "hdr")

        # Footer
        fc = ios.ios_card(c, "Add Footer", "Insert footer with optional page numbers")
        r3 = ctk.CTkFrame(fc, fg_color="transparent"); r3.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(r3, "Text").pack(side="left")
        self.ftr_text = ios.ios_entry(r3, 200, "Company Name"); self.ftr_text.pack(side="left", padx=10)
        self.ftr_nums = ios.ios_checkbox(r3, "Page numbers"); self.ftr_nums.pack(side="left", padx=10)
        self._make_btns(fc, "ftr")

        # Page Numbers
        pc = ios.ios_card(c, "Page Numbers", "Add page numbers to all pages")
        r4 = ctk.CTkFrame(pc, fg_color="transparent"); r4.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(r4, "Position").pack(side="left")
        self.pn_pos = ctk.StringVar(value="bottom-center")
        ios.ios_option_menu(r4, ["bottom-center","bottom-right","bottom-left","top-center"], self.pn_pos, 170).pack(side="left", padx=10)
        self._make_btns(pc, "pn")

        # Redact
        rc = ios.ios_card(c, "Redact Text", "Permanently black out sensitive text")
        r5 = ctk.CTkFrame(rc, fg_color="transparent"); r5.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(r5, "Text").pack(side="left")
        self.red_text = ios.ios_entry(r5, 250, "SSN, email, etc."); self.red_text.pack(side="left", padx=10)
        self._make_btns(rc, "red")

        ios.ios_section_label(c, "LOG")
        self.log_box = ios.ios_log_box(c, 90); self.log_box.pack(fill="x", pady=(0,10))

    def _make_btns(self, card, key):
        bf = ctk.CTkFrame(card, fg_color="transparent"); bf.pack(fill="x", padx=18)
        self._processes[key] = ios.ios_process_btn(bf, lambda: getattr(self, f"_do_{key}")())
        self._processes[key].pack(side="left", padx=5, pady=(0,12))
        self._cancels[key] = ios.ios_cancel_btn(bf, lambda: self.app.cancel_event.set())
        self._saves[key] = ios.ios_save_btn(bf, lambda k=key: self._save(k))
        self._progress[key] = ProcessingProgress(card)

    def _log(self, m): self.log_box.insert("end", m+"\n"); self.log_box.see("end"); logger.info(m)

    def _save(self, k):
        rp=self._results.get(k)
        if not rp: return
        d=filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if d: shutil.copy2(rp,d); self._log(f"Saved to {d}"); shutil.rmtree(os.path.dirname(rp), ignore_errors=True)
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

    def _pick(self): return filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])

    def _do_wm(self):
        inp=self._pick()
        if not inp: return
        txt=self.wm_text.get() or "CONFIDENTIAL"; sz=int(self.wm_size.get() or 60)
        def f():
            from core.editing import add_text_watermark
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"wm.pdf"); add_text_watermark(inp,t,text=txt,fontsize=sz,cancel_event=self.app.cancel_event); self._results["wm"]=t
        self._run("wm", f)

    def _do_imgwm(self):
        inp=self._pick()
        if not inp: return
        img=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.bmp")], title="Select image")
        if not img: return
        def f():
            from core.editing import add_image_watermark
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"imgwm.pdf"); add_image_watermark(inp,t,img,cancel_event=self.app.cancel_event); self._results["imgwm"]=t
        self._run("imgwm", f)

    def _do_hdr(self):
        inp=self._pick()
        if not inp: return
        txt=self.hdr_text.get() or "Header"
        def f():
            from core.editing import add_header
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"hdr.pdf"); add_header(inp,t,txt,cancel_event=self.app.cancel_event); self._results["hdr"]=t
        self._run("hdr", f)

    def _do_ftr(self):
        inp=self._pick()
        if not inp: return
        txt=self.ftr_text.get() or "Footer"; nums=bool(self.ftr_nums.get())
        def f():
            from core.editing import add_footer
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"ftr.pdf"); add_footer(inp,t,txt,include_page_numbers=nums,cancel_event=self.app.cancel_event); self._results["ftr"]=t
        self._run("ftr", f)

    def _do_pn(self):
        inp=self._pick()
        if not inp: return
        pos=self.pn_pos.get()
        def f():
            from core.editing import add_page_numbers
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"pn.pdf"); add_page_numbers(inp,t,position=pos,cancel_event=self.app.cancel_event); self._results["pn"]=t
        self._run("pn", f)

    def _do_red(self):
        inp=self._pick()
        if not inp: return
        txt=self.red_text.get()
        if not txt: messagebox.showwarning("PDFOS","Enter text to redact."); return
        def f():
            from core.editing import redact_text
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"red.pdf"); r=redact_text(inp,t,txt,cancel_event=self.app.cancel_event); self._results["red"]=t
            self._log(f"  {r['redactions']} instances found")
        self._run("red", f)
