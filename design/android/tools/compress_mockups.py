"""Save the mockup renders with a 256-colour palette. The screens are flat colour, so nothing visible is lost
and the folder is about a third of the size. Store graphics are not touched: Play wants 24-bit PNG."""
from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parent.parent / "mockups/png"
for f in sorted(root.rglob("*.png")):
    im = Image.open(f)
    if im.mode != "P":
        im.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(f, optimize=True)
print("done")
