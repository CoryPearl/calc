# Building the Calculator app

Packages the calculator into a standalone executable with the app logo as the icon.

## Prerequisites

- Python 3.10+ with `pip`
- **macOS:** Xcode Command Line Tools (for `iconutil` when generating `.icns`)
- **Windows:** None extra

## One-time setup

```bash
pip install -r requirements-build.txt
```

## Icons (from transparent PNG)

The app uses `logo.png` (transparent). Build scripts generate:

- **Windows:** `logo.ico` (from PNG)
- **macOS:** `logo.icns` (from PNG, only when run on Mac)

Generate both where possible:

```bash
python build_icons.py
```

On non‑Mac machines this only creates `.ico`; run `build_icons.py` on a Mac to get `.icns` for the Mac build.

## Build for macOS

On a Mac:

```bash
./build_mac.sh
```

Output: **`dist/Calculator.app`** (double‑click to run). Uses `logo.icns` as the app icon.

## Build for Windows

On Windows (Command Prompt or PowerShell):

```cmd
build_windows.bat
```

Output: **`dist\Calculator.exe`** (single file). Uses `logo.ico` as the icon.

## Manual build (optional)

- **Mac:**  
  `pyinstaller --noconfirm calculator_mac.spec`  
  (after running `build_icons.py` on Mac so `logo.icns` exists)

- **Windows:**  
  `pyinstaller --noconfirm calculator_win.spec`  
  (after `build_icons.py` so `logo.ico` exists)

## Cross‑platform note

- To get **Calculator.app** you must build on macOS.
- To get **Calculator.exe** you must build on Windows (or use a Windows VM/CI).

The same `logo.png` (transparent) is used to generate the platform‑specific icon files.
