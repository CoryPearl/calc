#!/usr/bin/env python3
"""
Generate logo.ico (Windows) and logo.icns (macOS) from logo.png.
Run from project root. Requires: pip install pillow
On macOS, .icns is created using system iconutil (no extra install).
"""
import os
import subprocess
import sys

try:
    from PIL import Image
except ImportError:
    print("Install Pillow: pip install pillow", file=sys.stderr)
    sys.exit(1)

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PNG_PATH = os.path.join(PROJECT_DIR, "logo.png")
ICO_PATH = os.path.join(PROJECT_DIR, "logo.ico")

# ICO sizes (Windows)
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# macOS iconset: exact filename -> pixel size (must match for iconutil)
ICONSET_SIZES = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]


def main():
    if not os.path.exists(PNG_PATH):
        print(f"Missing {PNG_PATH}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(PNG_PATH).convert("RGBA")

    # --- Windows ICO ---
    ico_sizes = []
    for (w, h) in ICO_SIZES:
        ico_sizes.append((w, h))
    img.save(ICO_PATH, format="ICO", sizes=ico_sizes)
    print(f"Wrote {ICO_PATH}")

    # --- macOS ICNS (only on macOS, using iconutil) ---
    if sys.platform != "darwin":
        print("Skipping .icns (run on macOS to generate logo.icns)")
        return

    iconset_dir = os.path.join(PROJECT_DIR, "logo.iconset")
    if os.path.isdir(iconset_dir):
        import shutil
        shutil.rmtree(iconset_dir)
    os.makedirs(iconset_dir, exist_ok=True)
    try:
        for name, size in ICONSET_SIZES:
            out_path = os.path.join(iconset_dir, name)
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(out_path, "PNG")
        icns_path = os.path.join(PROJECT_DIR, "logo.icns")
        r = subprocess.run(
            ["iconutil", "-c", "icns", "-o", icns_path, iconset_dir],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print("iconutil warning:", r.stderr or r.stdout, file=sys.stderr)
            print("Skipping .icns; use logo.png as icon or fix iconset.", file=sys.stderr)
        else:
            print(f"Wrote {icns_path}")
    finally:
        import shutil
        if os.path.isdir(iconset_dir):
            shutil.rmtree(iconset_dir)


if __name__ == "__main__":
    main()
