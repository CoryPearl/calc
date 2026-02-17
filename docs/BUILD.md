# Building the Calculator app

Packages the calculator into a standalone executable with the app logo as the icon.

## Project layout

- **`main.py`** – Entry point (launches app from `src/`)
- **`src/`** – App code (`src/app.py`)
- **`assets/`** – Logo and generated icons (`logo.png`, `logo.ico`, `logo.icns`)
- **`scripts/`** – Build helpers (`build_icons.py`)
- **`packaging/`** – Build scripts and PyInstaller specs
- **`docs/`** – Documentation (this file)

## Prerequisites

- Python 3.10+ with `pip`
- **macOS:** Xcode Command Line Tools (for `iconutil` when generating `.icns`)
- **Windows:** None extra

## One-time setup

```bash
pip install -r requirements-build.txt
```

## Icons (from PNG in assets/)

The app uses **`assets/logo.png`**. Build scripts generate:

- **Windows:** `assets/logo.ico`
- **macOS:** `assets/logo.icns` (only when run on Mac)

Generate both where possible:

```bash
python scripts/build_icons.py
```

On non‑Mac machines this only creates `.ico`; run on a Mac to get `.icns`.

## Build for macOS

From project root, on a Mac:

```bash
./packaging/build_mac.sh
```

Output: **`dist/Calculator.app`** (double‑click to run). Uses `assets/logo.icns` as the app icon.

## Build for Windows

From project root, on Windows (Command Prompt or PowerShell):

```cmd
packaging\build_windows.bat
```

Output: **`dist\Calculator.exe`** (single file). Uses `assets/logo.ico` as the icon.

## Manual build (optional)

From project root, after generating icons:

- **Mac:**  
  `pyinstaller --noconfirm packaging/calculator_mac.spec`

- **Windows:**  
  `pyinstaller --noconfirm packaging/calculator_win.spec`

## Cross‑platform note

- To get **Calculator.app** you must build on macOS.
- To get **Calculator.exe** you must build on Windows (or use a Windows VM/CI).

**`assets/logo.png`** is the source for the platform‑specific icon files.
