@echo off
REM Build Calculator.exe for Windows. Run from project root on Windows.
cd /d "%~dp0"

echo Installing build deps (if needed)...
pip install -q -r requirements-build.txt -r requirements.txt

echo Generating icons (ICO)...
python build_icons.py

if not exist logo.ico (
  echo Error: logo.ico not found.
  exit /b 1
)

echo Building with PyInstaller...
pyinstaller --noconfirm calculator_win.spec

echo Done. Executable: dist\Calculator.exe
