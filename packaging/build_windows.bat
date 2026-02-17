@echo off
REM Build Calculator.exe for Windows. Run from project root: packaging\build_windows.bat
cd /d "%~dp0\.."

echo Installing build deps (if needed)...
pip install -q -r requirements-build.txt -r requirements.txt

echo Generating icons (ICO)...
python scripts\build_icons.py

if not exist assets\logo.ico (
  echo Error: assets\logo.ico not found.
  exit /b 1
)

echo Building with PyInstaller...
pyinstaller --noconfirm packaging\calculator_win.spec

echo Done. Executable: dist\Calculator.exe
