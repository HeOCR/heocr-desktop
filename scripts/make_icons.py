#!/usr/bin/env python3
"""Draw the app icon (a blue tile with a white alef) at every size Briefcase needs.

    python scripts/make_icons.py <Alef-Bold.ttf>

Alef is under the SIL Open Font License 1.1. The output (icons/) is committed; this script
only documents how it was made.
"""

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "icons"
BLUE = (31, 95, 191, 255)


def tile(size: int, font_path: str) -> Image.Image:
    scale = 4
    big = size * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    inset = round(big * 0.09)
    draw.rounded_rectangle((inset, inset, big - inset, big - inset), radius=round(big * 0.2), fill=BLUE)
    font = ImageFont.truetype(font_path, round(big * 0.62))
    box = draw.textbbox((0, 0), "א", font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text(((big - w) / 2 - box[0], (big - h) / 2 - box[1] - big * 0.01), "א", font=font, fill="white")
    return img.resize((size, size), Image.LANCZOS)


def main(font_path: str) -> None:
    OUT.mkdir(exist_ok=True)
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    images = {s: tile(s, font_path) for s in sizes}
    for s in (16, 32, 64, 128, 256, 512):
        images[s].save(OUT / f"heocr-{s}.png")
    images[256].save(OUT / "heocr.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    if sys.platform == "darwin":
        iconset = ROOT / "build" / "heocr.iconset"
        iconset.mkdir(parents=True, exist_ok=True)
        for s in (16, 32, 128, 256, 512):
            images[s].save(iconset / f"icon_{s}x{s}.png")
            images[s * 2].save(iconset / f"icon_{s}x{s}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(OUT / "heocr.icns")], check=True)


if __name__ == "__main__":
    main(sys.argv[1])
