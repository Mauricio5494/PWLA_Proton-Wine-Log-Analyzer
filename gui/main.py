#!/usr/bin/env python3
"""
PWLA - Proton Wine Log Analyzer
================================

Interfaz gráfica para analizar archivos game.log de Call to Arms - Gates of Hell
ejecutados bajo Proton/Wine. Resalta errores críticos, filtra por severidad y
permite exportar reportes.

Depende solo de la biblioteca estándar de Python (tkinter).
"""

import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import sys
import os

# Colores de la interfaz
COLOR_BG = "#f5f5f5"
COLOR_PANEL = "#ffffff"
COLOR_HEADER = "#2c3e50"
COLOR_ACENT = "#3498db"
COLOR_OK = "#2ecc71"
COLOR_ERROR = "#e74c3c"
COLOR_WARN = "#f39c12"
COLOR_TEXT = "#333333"

SCRIPTS_DIR = Path(__file__).resolve().parent.parent

# Patrones de error conocidos en game.log de GEM2
ERROR_PATTERNS = [
    ("critical", ["«", "EXCEPTION_ACCESS_VIOLATION", "fatal", "access violation"]),
    ("error", ["error", "unexpected token", "file not found", "file signature mismatch", "ctd", "crash"]),
    ("warn", ["warning", "advertencia", "deprecated", "deprecat"]),
    ("info", ["info", "log", "loading", "initialized"]),
]


class PWLAGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PWLA — Proton Wine Log Analyzer")
        self.root.geometry("1000x750")
        self.root.minsize(850, 650)
        self.root.configure(bg=COLOR_BG)

        self.log_path_var = tk.StringVar(value="")
        self.only_errors_var = tk.BooleanVar(value=False)

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
        # ── Título ──
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=20, pady=(15, 5))

        ttk.Label(
            title_frame,
            text="PWLA — Proton Wine Log Analyzer",
            style="Title.TLabel",
        ).pack(side=tk.LEFT)
        ttk.Label(
            title_frame,
            text="  ·  Call to Arms / Gates of Hell Modding Tool",
            style="Subtitle.TLabel",
        ).pack(side=tk.LEFT, padx=(10, 0))

        # ── Selector de archivo ──
        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        ttk.Label(file_frame, text="Archivo game.log:").pack(side=tk.LEFT)
        self.log_entry = ttk.Entry(file_frame, textvariable=self.log_path_var, width=60)
        self.log_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Examinar…", command=self._browse_log).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        ttk.Checkbutton(
            file_frame,
            text="Solo mostrar errores",
            variable=self.only_errors_var,
            command=self._refresh_log,
        ).pack(side=tk.LEFT, padx=(15, 0))

        # ── Botones ──
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        ttk.Button(
            btn_frame,
            text="Abrir game.log",
            style="Accent.TButton",
            command=self._open_log_external,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="Refrescar",
            command=self._refresh_log,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="Exportar reporte…",
            command=self._export_report,
        ).pack(side=tk.LEFT)

        # ── Área de salida ──
        out_frame = ttk.LabelFrame(self.root, text="Contenido de game.log")
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

        # Tags de color para la salida
        self.output_log.tag_configure("critical", foreground="#f44336", font=("Consolas", 10, "bold"))
        self.output_log.tag_configure("error", foreground="#ff5252")
        self.output_log.tag_configure("warn", foreground="#ff9800")
        self.output_log.tag_configure("info", foreground="#81c784")

        self._refresh_log()

    # ── Acciones ──
    def _browse_log(self):
        f = filedialog.askopenfilename(
            title="Seleccionar game.log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
        )
        if f:
            self.log_path_var.set(f)
            self._refresh_log()

    def _open_log_external(self):
        path = self.log_path_var.get()
        if not path:
            messagebox.showwarning("Sin archivo", "Seleccioná primero un archivo game.log.")
            return
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", path])
            else:
                os.startfile(path)  # type: ignore[attr-defined]
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")

    def _classify_line(self, line: str):
        lower = line.lower()
        for tag, keywords in ERROR_PATTERNS:
            if any(k.lower() in lower for k in keywords):
                return tag
        return None

    def _refresh_log(self):
        path = self.log_path_var.get()
        self.output_log.delete(1.0, tk.END)

        if not path:
            self.output_log.insert(
                tk.END,
                "Seleccioná un archivo game.log usando el botón 'Examinar…'\n",
                "info",
            )
            return

        p = Path(path)
        if not p.exists():
            self.output_log.insert(
                tk.END,
                f"Archivo no encontrado:\n{path}\n",
                "error",
            )
            return

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            self.output_log.insert(tk.END, f"Error leyendo game.log: {e}\n", "error")
            return

        only_errors = self.only_errors_var.get()
        for line in lines:
            if only_errors and not any(
                k in line.lower()
                for k in [
                    "error", "ctd", "exception", "fatal", "«",
                    "unexpected token", "file not found", "access violation",
                ]
            ):
                continue

            tag = self._classify_line(line)
            self.output_log.insert(tk.END, line, tag)

        self.output_log.see(tk.END)

    def _export_report(self):
        path = self.log_path_var.get()
        if not path:
            messagebox.showwarning("Sin archivo", "Seleccioná primero un archivo game.log.")
            return

        p = Path(path)
        if not p.exists():
            messagebox.showerror("Error", f"Archivo no encontrado:\n{path}")
            return

        out = filedialog.asksaveasfilename(
            title="Exportar reporte",
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
                    k in lower
                    for k in [
                        "error", "ctd", "exception", "fatal", "«",
                        "unexpected token", "file not found", "access violation",
                    ]
                ):
                    report_lines.append(line.rstrip("\n"))

            with open(out, "w", encoding="utf-8") as f:
                f.write(f"PWLA Error Report — {p.name}\n")
                f.write("=" * 60 + "\n\n")
                f.write("\n".join(report_lines))

            messagebox.showinfo("Exportado", f"Reporte guardado en:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el reporte:\n{e}")


def main():
    root = tk.Tk()
    app = PWLAGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()