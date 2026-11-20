"""HeOCR desktop app icon (option B: the mark fills a white tile), installer images, and their exports.
SVG sources are written here; raster.js makes the PNGs; pack_icons.py builds .icns, .ico and the BMPs."""
import json
from pathlib import Path

from hbrand import THEMES, grid, lockup, mark, n, text

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "icons"
BLUE, INK, EDGE = "#2447f9", "#0c1222", "#c9cfe3"
jobs = []


def save(path, svg, png=None, scale=1, transparent=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    jobs.append(dict(svg=str(path), out=str(png or path.with_suffix(".png")), scale=scale, transparent=transparent))


def head(size, crisp=False):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}"{" shape-rendering=" + chr(34) + "crispEdges" + chr(34) if crisp else ""}>'


def mac(size):
    """macOS icon grid: on a 1024 canvas the tile is 824 wide with a 185 radius; the mark's grid is 90% of the tile."""
    k = size / 1024
    m = 824 * 0.9 * k
    w = dict(o=2.75, h=7, l=5) if size >= 128 else dict(o=3.1, h=7.5, l=5.4)
    return (head(size) + f'<rect x="{n(100 * k)}" y="{n(100 * k)}" width="{n(824 * k)}" height="{n(824 * k)}" rx="{n(185 * k)}" fill="#ffffff" stroke="{EDGE}" stroke-width="{n(max(1, 4 * k))}"/>'
            + mark((size - m) / 2, (size - m) / 2, m, BLUE, INK, **w) + "</svg>\n")


def win(size):
    """Windows: the tile fills the canvas, so nothing is lost to a margin in the taskbar."""
    m = size * 0.94
    w = dict(o=2.75, h=7, l=5) if size >= 128 else dict(o=3.1, h=7.5, l=5.4)
    return (head(size) + f'<rect x="0.5" y="0.5" width="{size - 1}" height="{size - 1}" rx="{n(size * 0.16)}" fill="#ffffff" stroke="{EDGE}"/>'
            + mark((size - m) / 2, (size - m) / 2, m, BLUE, INK, **w) + "</svg>\n")


def pixel(size, radius, blue, ink):
    r = lambda rs, c: "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"/>' for x, y, w, h in rs)
    return (head(size, True) + f'<rect x="0.5" y="0.5" width="{size - 1}" height="{size - 1}" rx="{radius}" fill="#ffffff" stroke="{EDGE}" shape-rendering="auto"/>{r(blue, BLUE)}{r(ink, INK)}</svg>\n')


# small sizes, drawn on the pixel grid: handles, the four sides of the box, then the letter's three strokes
PIXEL = {
    16: (2.5, [(1, 1, 3, 3), (12, 1, 3, 3), (1, 12, 3, 3), (12, 12, 3, 3), (4, 2, 8, 1), (4, 13, 8, 1), (2, 4, 1, 8), (13, 4, 1, 8)], [(5, 5, 6, 2), (9, 5, 2, 6), (5, 9, 2, 2)]),
    24: (3.5, [(1, 1, 4, 4), (19, 1, 4, 4), (1, 19, 4, 4), (19, 19, 4, 4), (5, 2, 14, 2), (5, 20, 14, 2), (2, 5, 2, 14), (20, 5, 2, 14)], [(7, 8, 10, 3), (14, 8, 3, 9), (7, 13, 3, 4)]),
    32: (5, [(1, 1, 6, 6), (25, 1, 6, 6), (1, 25, 6, 6), (25, 25, 6, 6), (7, 3, 18, 2), (7, 27, 18, 2), (3, 7, 2, 18), (27, 7, 2, 18)], [(10, 10, 13, 4), (19, 10, 4, 12), (10, 17, 4, 5)]),
}
for s, (rad, b, i) in PIXEL.items():
    save(OUT / f"app-icon/svg/pixel-{s}.svg", pixel(s, rad, b, i))
for s in (64, 128, 256, 512, 1024):
    save(OUT / f"app-icon/svg/mac-{s}.svg", mac(s))
for s in (48, 64, 128, 256):
    save(OUT / f"app-icon/svg/win-{s}.svg", win(s))

# ---------------- DMG window background: 660 x 400 pt, with a 2x version ----------------
t = THEMES["light"]
W, H = 660, 400
body = grid(W, H, 20, t) + lockup(36, 30, 34, t)[0]
body += f'<path d="M270 208H384M372 196l12 12-12 12" fill="none" stroke="{t["accent"]}" stroke-width="2.5" stroke-linecap="square"/>'
body += text("Drag HeOCR to Applications", "JetBrainsMono-500", 13, W / 2, 330, "middle", t["muted"])[0]
body += text("גררו את HeOCR אל Applications", "NotoSansHebrew-500", 14, W / 2, 354, "middle", t["muted"], fallback="NotoSansHebrew-500")[0]
dmg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{body}</svg>\n'
save(OUT / "installer/dmg-background.svg", dmg, OUT / "installer/dmg-background.png", 1, False)
save(OUT / "installer/dmg-background.svg", dmg, OUT / "installer/dmg-background@2x.png", 2, False)

# ---------------- Windows MSI: 493 x 312 dialog image and 493 x 58 banner (BMP made by pack_icons.py) ----------------
W, H = 493, 312
strip = 164
body = f'<rect width="{W}" height="{H}" fill="#ffffff"/>' + "".join(f'<path d="M{x},0V{H}" stroke="{t["grid"]}"/>' for x in range(20, strip, 20)) + "".join(f'<path d="M0,{y}H{strip}" stroke="{t["grid"]}"/>' for y in range(20, H, 20))
body += f'<path d="M{strip}.5,0V{H}" stroke="{t["line"]}"/>' + mark((strip - 84) / 2, 96, 84, t["accent"], t["text"])
he, w1 = text("He", "JetBrainsMono-700", 22, 0, 0, tracking=-0.03)
ocr, w2 = text("OCR", "JetBrainsMono-700", 22, 0, 0, tracking=-0.03)
x0 = (strip - (w1 + w2)) / 2
body += text("He", "JetBrainsMono-700", 22, x0, 214, fill=t["text"], tracking=-0.03)[0] + text("OCR", "JetBrainsMono-700", 22, x0 + w1, 214, fill=t["accent"], tracking=-0.03)[0]
save(OUT / "installer/msi-dialog.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{body}</svg>\n', OUT / "installer/msi-dialog-493x312.png", 1, False)
W, H = 493, 58
body = f'<rect width="{W}" height="{H}" fill="#ffffff"/><path d="M0,{H - 0.5}H{W}" stroke="{t["line"]}"/>' + mark(W - 52, 10, 38, t["accent"], t["text"])
save(OUT / "installer/msi-banner.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{body}</svg>\n', OUT / "installer/msi-banner-493x58.png", 1, False)
(HERE / "icon_jobs.json").write_text(json.dumps(jobs))
print(len(jobs), "jobs")
