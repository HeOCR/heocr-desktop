#!/usr/bin/env python3
"""Make the Android launcher icons from the brand icon (icons/heocr-512.png).

    python scripts/android_icons.py      # writes icons/android/heocr-{round,square,adaptive}-<size>.png

- square: the brand icon itself (rounded blue square, white aleph), for older launchers and the splash;
- round: a blue disc with the aleph;
- adaptive: a full-bleed blue square with the aleph inside the 66/108 safe zone, so any launcher mask
  (circle, squircle, teardrop) shows blue around it.
Sizes are the ones Briefcase's Android template asks for. Needs Pillow.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "icons" / "heocr-512.png"
OUT = ROOT / "icons" / "android"
SQUARE = (48, 72, 96, 144, 192, 320, 480, 640, 960, 1280)
ROUND = (48, 72, 96, 144, 192)
ADAPTIVE = (108, 162, 216, 324, 432)


def main() -> None:
    brand = Image.open(SOURCE).convert("RGBA")
    blue = brand.getpixel((256, 100))  # inside the rounded square, above the aleph
    letter = brand.crop((118, 118, 394, 394))  # blue with the aleph, clear of the rounded corners
    OUT.mkdir(parents=True, exist_ok=True)
    for size in SQUARE:
        brand.resize((size, size), Image.LANCZOS).save(OUT / f"heocr-square-{size}.png", optimize=True)
    for size in ROUND:
        big = 4 * size
        disc = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        mask = Image.new("L", (big, big), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
        disc.paste(Image.new("RGBA", (big, big), blue), (0, 0), mask)
        inner = int(big * 0.78)
        disc.alpha_composite(letter.resize((inner, inner), Image.LANCZOS), ((big - inner) // 2, (big - inner) // 2))
        disc.putalpha(mask)
        disc.resize((size, size), Image.LANCZOS).save(OUT / f"heocr-round-{size}.png", optimize=True)
    for size in ADAPTIVE:
        canvas = Image.new("RGBA", (size, size), blue)
        inner = int(size * 0.66)
        canvas.alpha_composite(letter.resize((inner, inner), Image.LANCZOS), ((size - inner) // 2, (size - inner) // 2))
        canvas.save(OUT / f"heocr-adaptive-{size}.png", optimize=True)
    print("wrote", len(list(OUT.glob("heocr-*.png"))), "icons to", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
