"""Builds heocr.icns, heocr.ico, the PNG set under the names the repository uses, and the MSI's BMP images."""
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "icons"
S = OUT / "app-icon/svg"
A = OUT / "app-icon"
img = lambda name: Image.open(S / f"{name}.png").convert("RGBA")
macset = {16: img("pixel-16"), 32: img("pixel-32"), 64: img("mac-64"), 128: img("mac-128"), 256: img("mac-256"), 512: img("mac-512"), 1024: img("mac-1024")}
winset = {16: img("pixel-16"), 24: img("pixel-24"), 32: img("pixel-32"), 48: img("win-48"), 64: img("win-64"), 128: img("win-128"), 256: img("win-256")}
(A / "macos").mkdir(exist_ok=True)
(A / "windows").mkdir(exist_ok=True)
(A / "macos/heocr.iconset").mkdir(exist_ok=True)
for pt in (16, 32, 128, 256, 512):
    macset[pt].save(A / f"macos/heocr.iconset/icon_{pt}x{pt}.png")
    macset[pt * 2].save(A / f"macos/heocr.iconset/icon_{pt}x{pt}@2x.png")
macset[1024].save(A / "macos/heocr-1024.png")
macset[1024].save(A / "macos/heocr.icns", format="ICNS", append_images=[macset[s] for s in (16, 32, 64, 128, 256, 512)])
for s, im in winset.items():
    im.save(A / f"windows/heocr-{s}.png")
winset[256].save(A / "windows/heocr.ico", format="ICO", sizes=[(s, s) for s in winset], append_images=[winset[s] for s in winset if s != 256])
# the PNGs beside the icons in the repository's icons/ folder (heocr-16.png ... heocr-512.png)
(A / "repo-icons").mkdir(exist_ok=True)
for s in (16, 32, 64, 128, 256, 512):
    macset[s].save(A / f"repo-icons/heocr-{s}.png")
for f in ("heocr.icns",):
    (A / "repo-icons" / f).write_bytes((A / "macos" / f).read_bytes())
(A / "repo-icons/heocr.ico").write_bytes((A / "windows/heocr.ico").read_bytes())
I = OUT / "installer"
Image.open(I / "msi-dialog-493x312.png").convert("RGB").save(I / "msi-dialog-493x312.bmp")
Image.open(I / "msi-banner-493x58.png").convert("RGB").save(I / "msi-banner-493x58.bmp")
ico = Image.open(A / "windows/heocr.ico")
print("ico sizes", sorted(ico.info.get("sizes", ico.ico.sizes())))
icns = Image.open(A / "macos/heocr.icns")
print("icns sizes", sorted(icns.info.get("sizes", [])))
