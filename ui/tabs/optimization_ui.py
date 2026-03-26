"""
ui/tabs/optimization_ui.py — iOS-styled optimization tab.
"""
import customtkinter as ctk
from tkinter import filedialog
import os, threading, tempfile, shutil, gc
from utils.logger import get_logger, log_operation
from ui.progress_widget import ProcessingProgress
from ui import ios_widgets as ios

logger = get_logger("optimization_ui")


class OptimizationTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=ios.BG)
        self.app = app
        self._results = {}; self._progress = {}; self._saves = {}; self._processes = {}; self._cancels = {}
        self._build_ui()

    def _build_ui(self):
        c = ios.ios_scrollable(self)
        c.pack(fill="both", expand=True, padx=16, pady=8)

        # Compress
        cc = ios.ios_card(c, "Compress PDF", "Reduce file size with quality control")
        ci = ctk.CTkFrame(cc, fg_color="transparent"); ci.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(ci, "Quality").pack(side="left")
        self.q_var = ctk.IntVar(value=80)
        ios.ios_slider(ci, 30, 100, self.q_var).pack(side="left", padx=10)
        self.q_lbl = ios.ios_label(ci, "80"); self.q_lbl.pack(side="left")
        self.q_var.trace_add("write", lambda *_: self.q_lbl.configure(text=str(self.q_var.get())))
        self._make_btns(cc, "compress")

        # Linearize
        lc = ios.ios_card(c, "Linearize", "Optimize for fast web viewing")
        self._make_btns(lc, "linearize")

        # Downsample
        dc = ios.ios_card(c, "Downsample Images", "Reduce embedded image resolution")
        di = ctk.CTkFrame(dc, fg_color="transparent"); di.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(di, "Max DPI").pack(side="left")
        self.ds_dpi = ios.ios_entry(di, 60, "150"); self.ds_dpi.pack(side="left", padx=10)
        self._make_btns(dc, "downsample")

        # Repair
        rc = ios.ios_card(c, "Repair PDF", "Attempt to fix a corrupted file")
        self._make_btns(rc, "repair")

        # Remove Metadata
        mc = ios.ios_card(c, "Remove Metadata", "Strip all metadata for privacy")
        self._make_btns(mc, "meta")

        # Grayscale
        gc_c = ios.ios_card(c, "Grayscale", "Convert all pages to grayscale")
        self._make_btns(gc_c, "gray")

        ios.ios_section_label(c, "LOG")
        self.log_box = ios.ios_log_box(c, 100); self.log_box.pack(fill="x", pady=(0,10))

    def _make_btns(self, card, key):
        bf = ctk.CTkFrame(card, fg_color="transparent"); bf.pack(fill="x", padx=18)
        self._processes[key] = ios.ios_process_btn(bf, lambda: getattr(self, f"_do_{key}")())
        self._processes[key].pack(side="left", padx=5, pady=(0, 12))
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

    def _do_compress(self):
        inp=self._pick()
        if not inp: return
        q=self.q_var.get()
        def f():
            from core.optimization import compress_pdf
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"comp.pdf"); r=compress_pdf(inp,t,image_quality=q,cancel_event=self.app.cancel_event); self._results["compress"]=t
            self._log(f"  {r['original_size']//1024}KB → {r['compressed_size']//1024}KB ({r['reduction_pct']}%)")
        self._run("compress", f)

    def _do_linearize(self):
        inp=self._pick()
        if not inp: return
        def f():
            from core.optimization import linearize_pdf
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"lin.pdf"); linearize_pdf(inp,t,cancel_event=self.app.cancel_event); self._results["linearize"]=t
        self._run("linearize", f)

    def _do_downsample(self):
        inp=self._pick()
        if not inp: return
        dpi=int(self.ds_dpi.get() or 150)
        def f():
            from core.optimization import downsample_images
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"ds.pdf"); downsample_images(inp,t,dpi,cancel_event=self.app.cancel_event); self._results["downsample"]=t
        self._run("downsample", f)

    def _do_repair(self):
        inp=self._pick()
        if not inp: return
        def f():
            from core.optimization import repair_pdf
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"rep.pdf"); r=repair_pdf(inp,t,cancel_event=self.app.cancel_event); self._results["repair"]=t
            if r["success"]: self._log(f"  Repaired: {r['pages']} pages")
        self._run("repair", f)

    def _do_meta(self):
        inp=self._pick()
        if not inp: return
        def f():
            from core.optimization import remove_metadata
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"nm.pdf"); remove_metadata(inp,t,cancel_event=self.app.cancel_event); self._results["meta"]=t
        self._run("meta", f)

    def _do_gray(self):
        inp=self._pick()
        if not inp: return
        def f():
            from core.optimization import convert_to_grayscale
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"gray.pdf"); convert_to_grayscale(inp,t,cancel_event=self.app.cancel_event); self._results["gray"]=t
        self._run("gray", f)
