#!/bin/bash
# Build Calculator.app for macOS. Run from project root: ./packaging/build_mac.sh
set -e
cd "$(dirname "$0")/.."

echo "Installing build deps (if needed)..."
pip install -q -r requirements-build.txt -r requirements.txt

echo "Generating icons (ICO + ICNS)..."
python3 scripts/build_icons.py

if [[ ! -f assets/logo.icns ]]; then
  echo "Error: assets/logo.icns not found. Run scripts/build_icons.py on macOS." 1>&2
  exit 1
fi

echo "Building with PyInstaller..."
pyinstaller --noconfirm packaging/calculator_mac.spec

echo "Done. App: dist/Calculator.app"
