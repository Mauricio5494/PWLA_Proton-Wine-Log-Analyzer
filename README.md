# PWLA — Proton Wine Log Analyzer

Offline game.log analyzer for **Call to Arms - Gates of Hell** mods running on Proton/Wine. Parses game logs to highlight CTD causes: missing files, invalid SDL tokens, bone link failures, and access violations. Color-coded error highlighting, severity filtering, and exportable reports. Helps modders diagnose crashes without launching the game.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux-lightgrey)](https://linux.org)

---

## Table of Contents

- [About](#about)
- [Features](#features)
- [Installation](#installation)
- [Running without a terminal (double-click)](#running-without-a-terminal-double-click)
- [Usage](#usage)
- [Repository Structure](#repository-structure)
- [License](#license)

---

## About

**PWLA (Proton Wine Log Analyzer)** is a Python-based offline tool for modders of *Call to Arms - Gates of Hell* (GEM2 engine). It reads `game.log` files generated when running the game under Proton/Wine and highlights critical error patterns that cause CTDs (Crash To Desktop), making it easier to diagnose mod issues without repeatedly launching the game.

## Features

- **Parse** `game.log` files from Proton/Wine installations
- **Highlight** error lines by severity: critical, error, warning, info
- **Filter** to show only errors with a checkbox toggle
- **Export** filtered error reports to text files
- **Open** the log in your system's default text editor with one click
- **No external dependencies** — runs on Python 3.8+ with tkinter only

## Installation

```bash
git clone https://github.com/Mauricio5494/PWLA_Proton-Wine-Log-Analyzer.git
cd PWLA_Proton-Wine-Log-Analyzer
```

No external Python dependencies are required — it runs on Python 3.8+ with the standard library only (**tkinter** is included with Python 3.8+ on most installations).

### System Dependencies

| Platform | Requirement |
|----------|-------------|
| **Windows** | Python 3.8+ installed from [python.org](https://python.org). During installation, check the box **"tcl/tk and IDLE"**. |
| **Linux** | Python 3.8+ and the `python3-tk` package (on Debian/Ubuntu: `sudo apt install python3-tk`). |
| **macOS** | **Not supported** (by author's decision). |

## Running without a terminal (double-click)

You do **not** need to open a terminal to use the GUI.

### Windows

Double-click **`run_gui.bat`**. It launches the app with `pythonw.exe` (no console window).

### Linux

1. Make the launcher executable:

   ```bash
   chmod +x run_gui.sh
   ```

2. Double-click **`run_gui.sh`** in your file manager, or run:

   ```bash
   ./run_gui.sh
   ```

3. Optionally, copy **`PWLA.desktop`** to `~/.local/share/applications/` to add it to your desktop environment's application menu.

## Usage

1. Launch the GUI: `python3 gui/main.py` (or double-click `run_gui.bat` / `run_gui.sh`)
2. Click **Examinar…** (Browse) and select your `game.log` file
3. The log loads automatically with color-coded severity:
   - **Red (critical)**: `«`, `EXCEPTION_ACCESS_VIOLATION`, fatal errors
   - **Orange (error)**: `error`, `unexpected token`, `file not found`, `access violation`
   - **Yellow (warn)**: warnings, deprecations
   - **Green (info)**: informational messages
4. Toggle **Solo mostrar errores** (Show errors only) to filter out informational lines
5. Click **Exportar reporte…** to save the filtered errors to a text file
6. Click **Abrir game.log** to open the raw file in your system's default editor

## Repository Structure

```
PWLA_Proton-Wine-Log-Analyzer/
├── LICENSE
├── README.md
├── .gitignore
├── run_gui.bat          # Launcher for Windows (double-click, no terminal)
├── run_gui.sh           # Launcher for Linux (double-click, no terminal)
├── PWLA.desktop         # Desktop menu entry for Linux desktop environments
├── gui/
│   ├── __init__.py
│   └── main.py          # Tkinter desktop application (no external deps)
```

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*Built for the Call to Arms / Gates of Hell modding community.*