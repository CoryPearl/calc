#!/usr/bin/env python3
"""Make logo.png a square image with dark grey background. Overwrites logo.png."""
import os
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(SCRIPT_DIR, "logo.png")
DARK_GREY = (0x2A, 0x2A, 0x2A)  # #2a2a2a

def main():
    if not os.path.exists(LOGO_PATH):
        print(f"Not found: {LOGO_PATH}")
        return
    img = Image.open(LOGO_PATH).convert("RGBA")
    w, h = img.size
    side = max(w, h)
    out = Image.new("RGBA", (side, side), (*DARK_GREY, 255))
    paste_x = (side - w) // 2
    paste_y = (side - h) // 2
    out.paste(img, (paste_x, paste_y), img)
    # Replace black or very dark pixels with dark grey so whole background is consistent
    pixels = out.load()
    for y in range(side):
        for x in range(side):
            r, g, b, a = pixels[x, y]
            if a < 30 or (r < 40 and g < 40 and b < 40):
                pixels[x, y] = (*DARK_GREY, 255)
    out.convert("RGB").save(LOGO_PATH)
    print(f"Saved square logo {side}x{side} with dark grey background: {LOGO_PATH}")

if __name__ == "__main__":
    main()
