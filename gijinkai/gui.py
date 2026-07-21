"""擬人化 Gijinkai GUI — native tkinter desktop application.

Neon-gradient dark theme. Ninja vibes.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path

from gijinkai.core import (
    mode_light,
    mode_medium,
    mode_aggressive,
    gijinkai_file,
    gijinkai_directory,
    rules_for,
    LANG_RULES,
)
from gijinkai import __version__


# ═══════════════════════════════════════════════════════════════════════════
# Neon gradient color scheme
# ═══════════════════════════════════════════════════════════════════════════

BG          = "#08080f"
CARD        = "#10101a"
CARD2       = "#141421"
INPUT       = "#0d0d16"
BORDER      = "#1a1a2a"
TEXT        = "#c8cde0"
MUTED       = "#5a5f77"
HILITE      = "#e0e4ff"

# Neon accents
N_RED       = "#ff4055"
N_RED2      = "#ff6b7a"
N_GREY      = "#7b8caa"
N_GREY2     = "#a0adc4"
N_BLUE      = "#4055ff"
N_BLUE2     = "#6b80ff"
N_GREEN     = "#22dd55"
N_GREEN2    = "#44ee77"
N_YELLOW    = "#ffbb22"
N_YELLOW2   = "#ffcc44"
N_ORANGE    = "#ff6622"
N_ORANGE2   = "#ff8844"

MODE_COLORS = {
    "light":      N_GREY,
    "medium":     N_GREEN,
    "aggressive": N_RED,
}

ACTIVE_BUTTON = "#222240"


class GijinkaiApp:
    """Main GUI application for Gijinkai."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("擬人化 Gijinkai — AI Fingerprint Removal")
        self.root.geometry("1100x780")
        self.root.configure(bg=BG)
        self.root.minsize(900, 600)

        # State
        self.mode_var = tk.StringVar(value="medium")
        self.target_var = tk.StringVar(value=str(Path.home()))
        self.target_is_file = tk.BooleanVar(value=False)
        self.results: list[tuple[Path, int, int, str]] = []
        self.preview_path: Path | None = None
        self.preview_text = ""
        self.working = False

        self._build_ui()
        self._bind_keys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_target_bar()
        self._build_mode_selector()
        self._build_actions()
        self._build_main_area()

    def _build_header(self):
        h = tk.Frame(self.root, bg=CARD, height=66, highlightthickness=1,
                     highlightbackground=BORDER)
        h.pack(fill=tk.X, padx=12, pady=(12, 0))
        h.pack_propagate(False)

        tk.Label(h, text="🥷", font=("DejaVu Sans", 32),
                 bg=CARD, fg=N_GREY2).pack(side=tk.LEFT, padx=(16, 8))

        left = tk.Frame(h, bg=CARD)
        left.pack(side=tk.LEFT, padx=(4, 0))

        tk.Label(left, text="擬人化  Gijinkai",
                 font=("DejaVu Sans Mono", 22, "bold"),
                 fg=N_BLUE2, bg=CARD).pack(anchor=tk.W)

        tk.Label(left, text="Language-aware AI fingerprint removal  ·  v" + __version__,
                 font=("DejaVu Sans Mono", 10), fg=MUTED, bg=CARD).pack(anchor=tk.W)

        # Right side: version badge
        ver_frame = tk.Frame(h, bg=CARD)
        ver_frame.pack(side=tk.RIGHT, padx=16)
        for lang, col in [("6 langs", N_GREEN), ("3 modes", N_YELLOW)]:
            tk.Label(ver_frame, text=lang,
                     font=("DejaVu Sans Mono", 9, "bold"),
                     fg=col, bg=CARD2).pack(side=tk.RIGHT, padx=3)

    def _build_target_bar(self):
        """File or directory picker."""
        bar = tk.Frame(self.root, bg=CARD, highlightthickness=1,
                       highlightbackground=BORDER)
        bar.pack(fill=tk.X, padx=12, pady=(8, 0))

        inner = tk.Frame(bar, bg=CARD)
        inner.pack(fill=tk.X, padx=14, pady=10)

        # Label row
        tk.Label(inner, text="🎯  Target", font=("DejaVu Sans Mono", 10, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor=tk.W)

        # Entry + browse row
        row = tk.Frame(inner, bg=CARD)
        row.pack(fill=tk.X, pady=(6, 0))

        self.target_entry = tk.Entry(
            row, textvariable=self.target_var,
            font=("DejaVu Sans Mono", 11), fg=TEXT, bg=INPUT,
            insertbackground=N_BLUE2, relief=tk.FLAT, bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=N_BLUE,
        )
        self.target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True,
                               ipady=5, padx=(0, 6))

        for label, file_mode, col in [
            ("📁  Browse Dir",  False, N_BLUE),
            ("📄  Browse File", True, N_GREY),
        ]:
            btn = tk.Button(row, text=label,
                            font=("DejaVu Sans Mono", 10),
                            fg=col, bg=INPUT, relief=tk.FLAT, bd=0,
                            activebackground=ACTIVE_BUTTON,
                            activeforeground=col,
                            highlightthickness=1, highlightbackground=BORDER,
                            command=lambda fm=file_mode: self._browse(fm))
            btn.pack(side=tk.RIGHT, padx=2)

    def _build_mode_selector(self):
        """Light / Medium / Aggressive mode toggle bar."""
        bar = tk.Frame(self.root, bg=CARD, highlightthickness=1,
                       highlightbackground=BORDER)
        bar.pack(fill=tk.X, padx=12, pady=(8, 0))

        inner = tk.Frame(bar, bg=CARD)
        inner.pack(fill=tk.X, padx=14, pady=10)

        tk.Label(inner, text="⚙️  Mode", font=("DejaVu Sans Mono", 10, "bold"),
                 fg=TEXT, bg=CARD).pack(anchor=tk.W)

        modes_row = tk.Frame(inner, bg=CARD)
        modes_row.pack(fill=tk.X, pady=(8, 0))

        modes = [
            ("light",      "🐾  Light",       "Whitespace only",
             N_GREY,   "Trailing spaces, blank-line collapse"),
            ("medium",     "🧹  Medium",      "Clean code, human style",
             N_GREEN,  "Docstrings, comments, pragmas, dividers"),
            ("aggressive", "🔥  Aggressive",  "Strip everything",
             N_RED,    "Above + type hints, shebangs, version boilerplate"),
        ]

        self.mode_buttons: dict[str, tk.Frame] = {}
        for i, (key, label, title, col, desc) in enumerate(modes):
            frame = tk.Frame(modes_row, bg=CARD2, bd=0,
                             highlightthickness=2,
                             highlightbackground=CARD,
                             padx=10, pady=8)
            frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0 if i == 0 else 6, 0 if i == 2 else 0))

            # Make the whole frame clickable
            for widget in (frame,):
                widget.bind("<Button-1>", lambda e, k=key: self._set_mode(k))
                for child_cls in (tk.Label,):
                    pass  # children will inherit from frame if we bind to frame

            header = tk.Frame(frame, bg=CARD2)
            header.pack(fill=tk.X)
            header.bind("<Button-1>", lambda e, k=key: self._set_mode(k))

            tk.Label(header, text=label,
                     font=("DejaVu Sans Mono", 11, "bold"),
                     fg=col, bg=CARD2).pack(side=tk.LEFT)
            tk.Label(header, text=title,
                     font=("DejaVu Sans Mono", 9),
                     fg=MUTED, bg=CARD2).pack(side=tk.RIGHT)

            tk.Label(frame, text=desc,
                     font=("DejaVu Sans Mono", 9),
                     fg=MUTED, bg=CARD2).pack(anchor=tk.W, pady=(4, 0))

            # Bind all children
            for child in frame.winfo_children():
                child.bind("<Button-1>", lambda e, k=key: self._set_mode(k))

            self.mode_buttons[key] = frame

        self._highlight_mode()

    def _set_mode(self, key: str):
        self.mode_var.set(key)
        self._highlight_mode()

    def _highlight_mode(self):
        active = self.mode_var.get()
        for key, frame in self.mode_buttons.items():
            col = MODE_COLORS.get(key, N_GREY)
            if key == active:
                frame.configure(highlightbackground=col, highlightthickness=2)
            else:
                frame.configure(highlightbackground=CARD, highlightthickness=2)

    def _build_actions(self):
        """Scan + Apply buttons."""
        bar = tk.Frame(self.root, bg=CARD, highlightthickness=1,
                       highlightbackground=BORDER)
        bar.pack(fill=tk.X, padx=12, pady=(8, 0))

        inner = tk.Frame(bar, bg=CARD)
        inner.pack(fill=tk.X, padx=14, pady=10)

        btn_row = tk.Frame(inner, bg=CARD)
        btn_row.pack(fill=tk.X)

        self.scan_btn = tk.Button(
            btn_row, text="🔍  Scan",
            font=("DejaVu Sans Mono", 12, "bold"),
            fg=N_BLUE2, bg=CARD2, relief=tk.FLAT, bd=0,
            activebackground="#1a1a40", activeforeground=N_BLUE2,
            highlightthickness=1, highlightbackground=BORDER,
            command=self._start_scan, padx=24, pady=8,
        )
        self.scan_btn.pack(side=tk.LEFT)

        self.apply_btn = tk.Button(
            btn_row, text="✏️  Apply Changes",
            font=("DejaVu Sans Mono", 12, "bold"),
            fg=N_GREEN2, bg=CARD2, relief=tk.FLAT, bd=0,
            activebackground="#0a1a10", activeforeground=N_GREEN2,
            highlightthickness=1, highlightbackground=BORDER,
            command=self._apply_changes, padx=24, pady=8,
            state=tk.DISABLED,
        )
        self.apply_btn.pack(side=tk.LEFT, padx=(8, 0))

        # Stats summary (right side)
        self.stats_label = tk.Label(
            btn_row, text="",
            font=("DejaVu Sans Mono", 10),
            fg=MUTED, bg=CARD, anchor=tk.E,
        )
        self.stats_label.pack(side=tk.RIGHT)

        # Spinner
        self.spinner_label = tk.Label(
            btn_row, text="",
            font=("DejaVu Sans Mono", 10),
            fg=N_YELLOW, bg=CARD,
        )
        self.spinner_label.pack(side=tk.RIGHT, padx=(0, 8))

    def _build_main_area(self):
        """Results table + preview diff panel."""
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Left: results list
        left = tk.Frame(main, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Header
        lh = tk.Frame(left, bg=CARD)
        lh.pack(fill=tk.X, padx=12, pady=(10, 4))
        tk.Label(lh, text="📋  Files", font=("DejaVu Sans Mono", 11, "bold"),
                 fg=TEXT, bg=CARD).pack(side=tk.LEFT)
        tk.Label(lh, text="Click to preview changes",
                 font=("DejaVu Sans Mono", 9),
                 fg=MUTED, bg=CARD).pack(side=tk.RIGHT)

        # Treeview for file list
        tree_frame = tk.Frame(left, bg=CARD)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        columns = ("lang", "before", "after", "delta")
        self.tree = ttk.Treeview(tree_frame, columns=columns,
                                 show="headings", selectmode="browse",
                                 height=12)
        self.tree.heading("#0", text="File")
        self.tree.heading("lang", text="Lang")
        self.tree.heading("before", text="Before")
        self.tree.heading("after", text="After")
        self.tree.heading("delta", text="Δ")

        self.tree.column("#0", width=260, stretch=True)
        self.tree.column("lang", width=80, anchor=tk.CENTER)
        self.tree.column("before", width=80, anchor=tk.E)
        self.tree.column("after", width=80, anchor=tk.E)
        self.tree.column("delta", width=75, anchor=tk.E)

        # Style the treeview for dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=INPUT, foreground=TEXT,
                        fieldbackground=INPUT, borderwidth=0,
                        font=("DejaVu Sans Mono", 10))
        style.configure("Treeview.Heading",
                        background=CARD2, foreground=MUTED,
                        font=("DejaVu Sans Mono", 9, "bold"),
                        borderwidth=0, relief=tk.FLAT)
        style.map("Treeview",
                  background=[("selected", "#1a1a40")],
                  foreground=[("selected", N_BLUE2)])
        style.map("Treeview.Heading",
                  background=[("active", CARD2)])

        # Scrollbar
        tree_scroll = tk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                   command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self._on_file_select)
        self.tree.bind("<Return>", self._on_file_select)

        # Right: preview
        right = tk.Frame(main, bg=CARD, highlightthickness=1,
                         highlightbackground=BORDER, width=400)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right.pack_propagate(False)

        rh = tk.Frame(right, bg=CARD)
        rh.pack(fill=tk.X, padx=12, pady=(10, 4))
        tk.Label(rh, text="🔍  Diff Preview", font=("DejaVu Sans Mono", 11, "bold"),
                 fg=TEXT, bg=CARD).pack(side=tk.LEFT)

        self.preview_title = tk.Label(rh, text="",
                                      font=("DejaVu Sans Mono", 9),
                                      fg=MUTED, bg=CARD)
        self.preview_title.pack(side=tk.RIGHT)

        # Diff text widget with colored tags
        self.diff_text = scrolledtext.ScrolledText(
            right, wrap=tk.NONE,
            font=("DejaVu Sans Mono", 10),
            bg=INPUT, fg=TEXT,
            insertbackground=N_BLUE2,
            relief=tk.FLAT, bd=0,
            highlightthickness=1, highlightbackground=BORDER,
            padx=10, pady=8,
        )
        self.diff_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # Configure diff tags
        self.diff_text.tag_configure("removed", foreground=N_RED,
                                     overstrike=True, background="#1a0a0a")
        self.diff_text.tag_configure("added", foreground=N_GREEN2,
                                      background="#0a1a0a")
        self.diff_text.tag_configure("header", foreground=N_ORANGE,
                                     font=("DejaVu Sans Mono", 9, "bold"))
        self.diff_text.tag_configure("filename", foreground=N_BLUE2,
                                     font=("DejaVu Sans Mono", 10, "bold"))
        self.diff_text.tag_configure("stats", foreground=MUTED,
                                     font=("DejaVu Sans Mono", 9))
        self.diff_text.configure(state=tk.DISABLED)

        # Bottom status bar
        status_bar = tk.Frame(self.root, bg=CARD2, height=28,
                              highlightthickness=1, highlightbackground=BORDER)
        status_bar.pack(fill=tk.X, padx=12, pady=(0, 12))
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            status_bar, text="Ready. Select a file or directory to scan.",
            font=("DejaVu Sans Mono", 9), fg=MUTED, bg=CARD2, anchor=tk.W,
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, padx=12, pady=2)

    def _bind_keys(self):
        self.root.bind("<Control-o>", lambda e: self._browse(False))
        self.root.bind("<Control-f>", lambda e: self._browse(True))
        self.root.bind("<Control-Return>", lambda e: self._start_scan())
        self.root.bind("<Escape>", lambda e: self._on_close())

    # ─────────────────────────────────────────────────────────────────────
    # Actions
    # ─────────────────────────────────────────────────────────────────────

    def _browse(self, is_file: bool):
        if is_file:
            path = filedialog.askopenfilename(
                title="Select source file",
                filetypes=[
                    ("All supported", "*.py *.js *.ts *.html *.css *.sh"),
                    ("Python", "*.py"),
                    ("JavaScript/TypeScript", "*.js *.ts *.mjs"),
                    ("HTML", "*.html"),
                    ("CSS", "*.css"),
                    ("Shell", "*.sh *.bash *.zsh"),
                    ("All files", "*.*"),
                ],
            )
        else:
            path = filedialog.askdirectory(title="Select directory")

        if path:
            self.target_var.set(path)
            self.target_is_file.set(is_file)
            self._clear_results()

    def _start_scan(self):
        if self.working:
            return

        target = Path(self.target_var.get())
        if not target.exists():
            messagebox.showwarning("Not Found", f"Path does not exist:\n{target}")
            return

        self.working = True
        self._set_scanning_ui(True)
        self._clear_results()

        thread = threading.Thread(target=self._scan_thread, args=(target,),
                                  daemon=True)
        thread.start()

    def _scan_thread(self, target: Path):
        mode_key = self.mode_var.get()
        mode_map = {"light": mode_light, "medium": mode_medium, "aggressive": mode_aggressive}
        mode = mode_map.get(mode_key, mode_medium)()

        try:
            if target.is_file():
                rules = rules_for(target)
                if rules is None:
                    self.root.after(0, lambda: self._scan_done([], "Unsupported file type"))
                    return
                orig = target.read_text(encoding="utf-8")
                from gijinkai.core import gijinkai as run
                new = run(orig, rules, mode)
                if new != orig:
                    results = [(target, len(orig), len(new), rules.name)]
                else:
                    results = []
            else:
                results = gijinkai_directory(target, mode, in_place=False, dry_run=True)

            self.root.after(0, lambda: self._scan_done(results))
        except Exception as e:
            self.root.after(0, lambda: self._scan_done([], str(e)))

    def _scan_done(self, results: list, error: str = ""):
        self.working = False
        self._set_scanning_ui(False)
        self.results = results

        if error:
            messagebox.showerror("Error", error)
            self.status_label.configure(text="Scan failed.")
            return

        # Populate tree
        self.tree.delete(*self.tree.get_children())
        for fpath, before, after, lang in results:
            rel = fpath if fpath.is_absolute() else fpath
            delta = before - after
            self.tree.insert("", tk.END, text=str(rel),
                             values=(lang, f"{before:,}B", f"{after:,}B",
                                     f"-{delta:,}B"))

        # Stats
        n = len(results)
        total_before = sum(b for _, b, _, _ in results) if results else 0
        total_after = sum(a for _, _, a, _ in results) if results else 0
        pct = ((total_before - total_after) / total_before * 100) if total_before else 0

        if results:
            self.stats_label.configure(
                text=f"{n} file{'' if n == 1 else 's'}  ·  "
                     f"{total_before:,}B → {total_after:,}B  "
                     f"(-{total_before - total_after:,}B / {pct:.1f}%)"
            )
            self.apply_btn.configure(state=tk.NORMAL)
            self.status_label.configure(text=f"Scanned {n} file{'' if n == 1 else 's'}."
                                         f"  {total_before - total_after:,}B of AI fingerprints found.")
        else:
            self.stats_label.configure(text="All clean!")
            self.apply_btn.configure(state=tk.DISABLED)
            self.status_label.configure(text="No AI fingerprints detected. Code looks human-written. 🧑‍💻")

    def _on_file_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        fpath_str = item["text"]

        # Find the matching result
        for fpath, before, after, lang in self.results:
            if str(fpath) == fpath_str or str(fpath) == Path(fpath_str).name:
                self._show_diff(fpath, before, after)
                return

    def _show_diff(self, fpath: Path, before: int, after: int):
        try:
            orig = fpath.read_text(encoding="utf-8")
        except Exception:
            return

        mode_key = self.mode_var.get()
        mode_map = {"light": mode_light, "medium": mode_medium, "aggressive": mode_aggressive}
        mode = mode_map.get(mode_key, mode_medium)()

        rules = rules_for(fpath)
        if rules is None:
            return

        from gijinkai.core import gijinkai as run
        new = run(orig, rules, mode)

        # Generate unified diff
        import difflib
        diff_lines = list(difflib.unified_diff(
            orig.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=str(fpath),
            tofile=f"(cleaned) {fpath.name}",
            lineterm="",
        ))

        self.diff_text.configure(state=tk.NORMAL)
        self.diff_text.delete("1.0", tk.END)

        if not diff_lines:
            self.diff_text.insert(tk.END, "No changes to display.")
        else:
            for line in diff_lines:
                line = line + "\n"
                if line.startswith("---") or line.startswith("+++"):
                    self.diff_text.insert(tk.END, line, "filename")
                elif line.startswith("@@"):
                    self.diff_text.insert(tk.END, line, "header")
                elif line.startswith("-"):
                    self.diff_text.insert(tk.END, line, "removed")
                elif line.startswith("+"):
                    self.diff_text.insert(tk.END, line, "added")
                else:
                    self.diff_text.insert(tk.END, line)

        self.diff_text.configure(state=tk.DISABLED)
        delta = before - after
        self.preview_title.configure(
            text=f"{fpath.name}  ·  -{delta:,}B ({delta/before*100:.1f}%)"
            if delta > 0 else f"{fpath.name}")

    def _apply_changes(self):
        if not self.results:
            return

        # Confirm
        n = len(self.results)
        total = sum(b - a for _, b, a, _ in self.results)
        ok = messagebox.askyesno(
            "Apply Changes",
            f"Write changes to {n} file{'' if n == 1 else 's'}?\n\n"
            f"Total: -{total:,}B will be removed.\n\n"
            f"⚠️  This cannot be undone. Make sure you have backups.",
            icon="warning",
        )
        if not ok:
            return

        # Write in place
        mode_key = self.mode_var.get()
        mode_map = {"light": mode_light, "medium": mode_medium, "aggressive": mode_aggressive}
        mode = mode_map.get(mode_key, mode_medium)()

        count = 0
        errors = []

        for fpath, _, _, _ in self.results:
            try:
                rules = rules_for(fpath)
                if rules is None:
                    continue
                orig = fpath.read_text(encoding="utf-8")
                from gijinkai.core import gijinkai as run
                new = run(orig, rules, mode)
                if new != orig:
                    fpath.write_text(new, encoding="utf-8")
                    count += 1
            except Exception as e:
                errors.append(f"{fpath.name}: {e}")

        if errors:
            messagebox.showwarning(
                "Partial Success",
                f"Applied to {count} file(s).\n{len(errors)} error(s):\n" +
                "\n".join(errors[:5]),
            )
        else:
            self.status_label.configure(
                text=f"✓  Applied changes to {count} file{'' if count == 1 else 's'}."
            )
            self.apply_btn.configure(state=tk.DISABLED)
            self._clear_results()

    def _clear_results(self):
        self.results = []
        self.tree.delete(*self.tree.get_children())
        self.stats_label.configure(text="")
        self.apply_btn.configure(state=tk.DISABLED)

        self.diff_text.configure(state=tk.NORMAL)
        self.diff_text.delete("1.0", tk.END)
        self.diff_text.insert(
            tk.END,
            "Select a file or directory and click Scan to begin.\n\n"
            "🟢  Light    — whitespace only\n"
            "🟡  Medium   — docstrings, comments, pragmas\n"
            "🔴  Aggressive — above + type hints, shebangs\n\n"
            "Double-click a file above to preview the diff.",
        )
        self.diff_text.configure(state=tk.DISABLED)
        self.preview_title.configure(text="")

    def _set_scanning_ui(self, scanning: bool):
        if scanning:
            self.scan_btn.configure(text="⏳  Scanning...", state=tk.DISABLED)
            self.spinner_label.configure(text="Working...")
            self.status_label.configure(text="Scanning files...")
        else:
            self.scan_btn.configure(text="🔍  Scan", state=tk.NORMAL)
            self.spinner_label.configure(text="")

    def _on_close(self):
        if self.working:
            messagebox.showwarning("Busy", "Scan in progress — please wait.")
            return
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def launch_gui():
    app = GijinkaiApp()
    app.run()
