"""
ui/tabs/security_ui.py — iOS-styled security tab.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os, threading, tempfile, shutil, gc
from utils.logger import get_logger, log_operation
from ui.progress_widget import ProcessingProgress
from ui import ios_widgets as ios

logger = get_logger("security_ui")


class SecurityTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=ios.BG)
        self.app = app
        self._results = {}; self._progress = {}; self._saves = {}; self._processes = {}; self._cancels = {}
        self._build_ui()

    def _build_ui(self):
        c = ios.ios_scrollable(self)
        c.pack(fill="both", expand=True, padx=16, pady=8)

        # Encrypt
        ec = ios.ios_card(c, "Encrypt PDF", "Protect with user and owner passwords")
        ef = ctk.CTkFrame(ec, fg_color="transparent"); ef.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(ef, "User Password").pack(side="left")
        self.enc_upw = ios.ios_entry(ef, 140); self.enc_upw.configure(show="•"); self.enc_upw.pack(side="left", padx=8)
        ios.ios_label(ef, "Owner Password").pack(side="left", padx=(8,0))
        self.enc_opw = ios.ios_entry(ef, 140); self.enc_opw.configure(show="•"); self.enc_opw.pack(side="left", padx=8)
        pf = ctk.CTkFrame(ec, fg_color="transparent"); pf.pack(fill="x", padx=18, pady=4)
        self.enc_print = ios.ios_checkbox(pf, "Allow Print"); self.enc_print.pack(side="left", padx=8); self.enc_print.select()
        self.enc_copy = ios.ios_checkbox(pf, "Allow Copy"); self.enc_copy.pack(side="left", padx=8)
        self._make_btns(ec, "enc")

        # Decrypt
        dc = ios.ios_card(c, "Decrypt PDF", "Remove password protection")
        df = ctk.CTkFrame(dc, fg_color="transparent"); df.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(df, "Password").pack(side="left")
        self.dec_pw = ios.ios_entry(df, 200); self.dec_pw.configure(show="•"); self.dec_pw.pack(side="left", padx=8)
        self._make_btns(dc, "dec")

        # Permissions
        pc = ios.ios_card(c, "Set Permissions", "Configure granular access controls")
        ppf = ctk.CTkFrame(pc, fg_color="transparent"); ppf.pack(fill="x", padx=18, pady=(0,6))
        ios.ios_label(ppf, "Owner Password").pack(side="left")
        self.perm_pw = ios.ios_entry(ppf, 200); self.perm_pw.configure(show="•"); self.perm_pw.pack(side="left", padx=8)
        pf2 = ctk.CTkFrame(pc, fg_color="transparent"); pf2.pack(fill="x", padx=18, pady=4)
        self.p_pr = ios.ios_checkbox(pf2, "Print"); self.p_pr.pack(side="left", padx=6); self.p_pr.select()
        self.p_cp = ios.ios_checkbox(pf2, "Copy"); self.p_cp.pack(side="left", padx=6); self.p_cp.select()
        self.p_md = ios.ios_checkbox(pf2, "Modify"); self.p_md.pack(side="left", padx=6)
        self.p_an = ios.ios_checkbox(pf2, "Annotate"); self.p_an.pack(side="left", padx=6); self.p_an.select()
        self._make_btns(pc, "perm")

        # Check
        cc2 = ios.ios_card(c, "Check Encryption", "Verify if a PDF is password-protected")
        ios.ios_button(cc2, "Check PDF", self._check, ios.INDIGO, 140).pack(padx=18, pady=(0,14))

        ios.ios_section_label(c, "LOG")
        self.log_box = ios.ios_log_box(c, 90); self.log_box.pack(fill="x", pady=(0,10))

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

    def _do_enc(self):
        inp=self._pick()
        if not inp: return
        upw=self.enc_upw.get()
        if not upw: messagebox.showwarning("PDFOS","Enter user password."); return
        opw=self.enc_opw.get() or upw; ap=bool(self.enc_print.get()); ac=bool(self.enc_copy.get())
        def f():
            from core.security import encrypt_pdf
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"enc.pdf"); encrypt_pdf(inp,t,upw,opw,ap,ac,cancel_event=self.app.cancel_event); self._results["enc"]=t
        self._run("enc", f)

    def _do_dec(self):
        inp=self._pick()
        if not inp: return
        pw=self.dec_pw.get()
        if not pw: messagebox.showwarning("PDFOS","Enter password."); return
        def f():
            from core.security import decrypt_pdf
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"dec.pdf"); decrypt_pdf(inp,t,pw,cancel_event=self.app.cancel_event); self._results["dec"]=t
        self._run("dec", f)

    def _do_perm(self):
        inp=self._pick()
        if not inp: return
        pw=self.perm_pw.get()
        if not pw: messagebox.showwarning("PDFOS","Enter owner password."); return
        def f():
            from core.security import set_permissions
            t=os.path.join(tempfile.mkdtemp(prefix="pdfos_"),"perm.pdf")
            set_permissions(inp,t,pw,bool(self.p_pr.get()),bool(self.p_cp.get()),bool(self.p_md.get()),bool(self.p_an.get()),cancel_event=self.app.cancel_event); self._results["perm"]=t
        self._run("perm", f)

    def _check(self):
        inp=self._pick()
        if not inp: return
        try:
            from core.security import is_encrypted
            enc=is_encrypted(inp)
            self._log(f"{'Encrypted' if enc else 'Not encrypted'}: {os.path.basename(inp)}")
        except Exception as e: self._log(f"✗ {e}")
