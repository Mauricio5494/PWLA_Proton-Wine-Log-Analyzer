#!/usr/bin/env python3
"""
PWLA — Proton Wine Log Analyzer
================================

Generic offline game.log analyzer and error amplifier for any game running
under Proton/Wine or natively. Highlights critical error patterns, filters by
severity, and allows exporting reports. Users can add custom error patterns.

Depends only on the Python standard library (tkinter).
"""

import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import sys
import os
import json

# UI colors
COLOR_BG = "#f5f5f5"
COLOR_PANEL = "#ffffff"
COLOR_HEADER = "#2c3e50"
COLOR_ACENT = "#3498db"
COLOR_OK = "#2ecc71"
COLOR_ERROR = "#e74c3c"
COLOR_WARN = "#f39c12"
COLOR_TEXT = "#333333"

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
PATTERNS_FILE = SCRIPTS_DIR / "error_patterns.json"

# Default error patterns (generic, work with any game engine)
DEFAULT_PATTERNS = [
    ("critical", ["«", "EXCEPTION_ACCESS_VIOLATION", "fatal", "access violation", "segmentation fault", "sigsegv"]),
    ("error", ["error", "unexpected token", "file not found", "file signature mismatch", "ctd", "crash", "assertion failed"]),
    ("warn", ["warning", "advertencia", "deprecated", "deprecat", "warn"]),
    ("info", ["info", "log", "loading", "initialized", "starting"]),
]


def load_patterns():
    """Load error patterns from JSON file, or return defaults."""
    if PATTERNS_FILE.exists():
        try:
            with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_PATTERNS


def save_patterns(patterns):
    """Save error patterns to JSON file."""
    with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)


class PWLAGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PWLA — Proton Wine Log Analyzer")
        self.root.geometry("1100x800")
        self.root.minsize(900, 700)
        self.root.configure(bg=COLOR_BG)

        self.log_path_var = tk.StringVar(value="")
        self.only_errors_var = tk.BooleanVar(value=False)
        self.patterns = load_patterns()

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)
        style.configure(
            "Header.TLabel",
            background=COLOR_HEADER,
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            padding=10,
        )
        style.configure(
            "Title.TLabel",
            background=COLOR_BG,
            foreground=COLOR_HEADER,
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLOR_BG,
            foreground="#666666",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Accent.TButton",
            background=COLOR_ACENT,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 6),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#2980b9"), ("disabled", "#95a5a6")],
        )
        style.configure(
            "Status.TLabel",
            background=COLOR_BG,
            foreground=COLOR_TEXT,
            font=("Segoe UI", 9),
            padding=(5, 2),
        )

    def _build_ui(self):
        # ── Title ──
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=20, pady=(15, 5))

        ttk.Label(
            title_frame,
            text="PWLA — Proton Wine Log Analyzer",
            style="Title.TLabel",
        ).pack(side=tk.LEFT)
        ttk.Label(
            title_frame,
            text="  ·  Generic game.log error reader & amplifier",
            style="Subtitle.TLabel",
        ).pack(side=tk.LEFT, padx=(10, 0))

        # ── File selector ──
        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        ttk.Label(file_frame, text="Log file:").pack(side=tk.LEFT)
        self.log_entry = ttk.Entry(file_frame, textvariable=self.log_path_var, width=60)
        self.log_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse…", command=self._browse_log).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        ttk.Checkbutton(
            file_frame,
            text="Show errors only",
            variable=self.only_errors_var,
            command=self._refresh_log,
        ).pack(side=tk.LEFT, padx=(15, 0))

        # ── Buttons ──
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        ttk.Button(
            btn_frame,
            text="Open log file",
            style="Accent.TButton",
            command=self._open_log_external,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="Refresh",
            command=self._refresh_log,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="Edit error patterns…",
            command=self._edit_patterns,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="Export report…",
            command=self._export_report,
        ).pack(side=tk.LEFT)

        # ── Output area ──
        out_frame = ttk.LabelFrame(self.root, text="Log content")
        out_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        self.output_log = scrolledtext.ScrolledText(
            out_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#1e1e1e",
            foreground="#d4d4d4",
            insertbackground="white",
            padx=8,
            pady=8,
        )
        self.output_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Color tags for output
        self.output_log.tag_configure("critical", foreground="#f44336", font=("Consolas", 10, "bold"))
        self.output_log.tag_configure("error", foreground="#ff5252")
        self.output_log.tag_configure("warn", foreground="#ff9800")
        self.output_log.tag_configure("info", foreground="#81c784")

        # ── Status bar ──
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, style="Status.TLabel").pack(
            side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 10)
        )

        self._refresh_log()

    # ── Actions ──
    def _browse_log(self):
        f = filedialog.askopenfilename(
            title="Select log file",
            filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")],
        )
        if f:
            self.log_path_var.set(f)
            self._refresh_log()

    def _open_log_external(self):
        path = self.log_path_var.get()
        if not path:
            messagebox.showwarning("No file", "Select a log file first.")
            return
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", path])
            else:
                os.startfile(path)  # type: ignore[attr-defined]
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def _edit_patterns(self):
        """Open a simple dialog to edit error patterns."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Edit Error Patterns")
        dlg.geometry("700x500")
        dlg.configure(bg=COLOR_BG)
        dlg.transient(self.root)
        dlg.grab_set()

        ttk.Label(dlg, text="Edit error patterns (JSON format):", style="Subtitle.TLabel").pack(
            padx=15, pady=(15, 5), anchor=tk.W
        )

        text = scrolledtext.ScrolledText(
            dlg,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#1e1e1e",
            foreground="#d4d4d4",
            insertbackground="white",
            padx=8,
            pady=8,
        )
        text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        text.insert(tk.END, json.dumps(self.patterns, indent=2, ensure_ascii=False))

        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        def save_and_close():
            try:
                new_patterns = json.loads(text.get(1.0, tk.END))
                # Validate structure
                for sev, keywords in new_patterns.items():
                    if not isinstance(keywords, list):
                        raise ValueError(f"Severity '{sev}' must have a list of keywords")
                self.patterns = new_patterns
                save_patterns(new_patterns)
                self._refresh_log()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Invalid JSON", f"Error parsing patterns:\n{e}", parent=dlg)

        ttk.Button(btn_frame, text="Save", command=save_and_close).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side=tk.LEFT)
        ttk.Button(
            btn_frame,
            text="Reset to defaults",
            command=lambda: self._reset_patterns(text, dlg),
        ).pack(side=tk.LEFT)

    def _reset_patterns(self, text_widget, dialog):
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, json.dumps(DEFAULT_PATTERNS, indent=2, ensure_ascii=False))

    def _classify_line(self, line: str):
        lower = line.lower()
        for severity, keywords in self.patterns.items():
            if any(k.lower() in lower for k in keywords):
                return severity
        return None

    def _refresh_log(self):
        path = self.log_path_var.get()
        self.output_log.delete(1.0, tk.END)

        if not path:
            self.output_log.insert(
                tk.END,
                "Select a log file using the 'Browse…' button.\n",
                "info",
            )
            self.status_var.set("Ready — no file selected")
            return

        p = Path(path)
        if not p.exists():
            self.output_log.insert(
                tk.END,
                f"File not found:\n{path}\n",
                "error",
            )
            self.status_var.set("Error: file not found")
            return

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            self.output_log.insert(tk.END, f"Error reading log file: {e}\n", "error")
            self.status_var.set("Error reading file")
            return

        only_errors = self.only_errors_var.get()
        error_count = 0
        warn_count = 0
        crit_count = 0

        for line in lines:
            if only_errors:
                tag = self._classify_line(line)
                if tag not in ("critical", "error"):
                    continue

            tag = self._classify_line(line)
            if tag == "critical":
                crit_count += 1
            elif tag == "error":
                error_count += 1
            elif tag == "warn":
                warn_count += 1

            self.output_log.insert(tk.END, line, tag)

        self.output_log.see(tk.END)

        # Update status bar
        total = crit_count + error_count + warn_count
        self.status_var.set(
            f"File: {p.name} | Lines: {len(lines)} | "
            f"Critical: {crit_count} | Errors: {error_count} | Warnings: {warn_count}"
        )

    def _export_report(self):
        path = self.log_path_var.get()
        if not path:
            messagebox.showwarning("No file", "Select a log file first.")
            return

        p = Path(path)
        if not p.exists():
            messagebox.showerror("Error", f"File not found:\n{path}")
            return

        out = filedialog.asksaveasfilename(
            title="Export report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not out:
            return

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            report_lines = []
            for line in lines:
                lower = line.lower()
                if any(
                    k.lower() in lower
                    for severity, keywords in self.patterns.items()
                    for k in keywords
                    if severity in ("critical", "error")
                ):
                    report_lines.append(line.rstrip("\n"))

            with open(out, "w", encoding="utf-8") as f:
                f.write(f"PWLA Error Report — {p.name}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Total error/critical lines: {len(report_lines)}\n\n")
                f.write("\n".join(report_lines))

            messagebox.showinfo("Exported", f"Report saved to:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export report:\n{e}")


def main():
    root = tk.Tk()
    app = PWLAGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()