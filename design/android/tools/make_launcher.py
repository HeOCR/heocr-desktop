"""HeOCR Android launcher icon, splash icon and their Android resource files.
Everything is drawn from the Logo 1 geometry (48-unit grid) as filled shapes, so the SVG and the
VectorDrawable XML carry the same path data. PNGs are rasterised from the SVGs (raster.js)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
BLUE, INK, WHITE = "#2447f9", "#0c1222", "#ffffff"
NIGHT_BLUE, NIGHT_INK, NIGHT_BG = "#8fa3ff", "#ecebe8", "#141414"
LOGO = dict(o=2.0, h=6.0, l=4.5)      # the logo as drawn in the brand files
ICON = dict(o=2.75, h=7.0, l=5.0)     # "icon weight": slightly heavier, for 48 dp and smaller


def n(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s or "0"


def mark_paths(s, tx, ty, o, h, l):
    """Returns (box_path, letter_path) in canvas units. Sub-paths are wound so nonZero fill leaves the hole."""
    X = lambda x: n(tx + s * x)
    Y = lambda y: n(ty + s * y)
    a, b = 7 - o / 2, 41 + o / 2      # outer frame
    c, d = 7 + o / 2, 41 - o / 2      # inner frame
    box = f"M{X(a)},{Y(a)}H{X(b)}V{Y(b)}H{X(a)}Z M{X(c)},{Y(c)}V{Y(d)}H{X(d)}V{Y(c)}Z"
    for cx, cy in ((7, 7), (41, 7), (7, 41), (41, 41)):
        box += f" M{X(cx - h / 2)},{Y(cy - h / 2)}H{X(cx + h / 2)}V{Y(cy + h / 2)}H{X(cx - h / 2)}Z"
    letter = (f"M{X(16)},{Y(18 - l / 2)}H{X(32 + l / 2)}V{Y(32.5)}H{X(32 - l / 2)}V{Y(18 + l / 2)}H{X(16)}Z "
              f"M{X(16 - l / 2)},{Y(24.5)}H{X(16 + l / 2)}V{Y(32.5)}H{X(16 - l / 2)}Z")
    return box, letter


def svg(size, body, bg=None, extra=""):
    rect = f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">{rect}{extra}{body}</svg>\n'


def mark_svg(s, t, w, box_fill, ink_fill):
    box, letter = mark_paths(s, t, t, **w)
    return f'<path fill="{box_fill}" d="{box}"/><path fill="{ink_fill}" d="{letter}"/>'


def vector_xml(size, s, t, w, box_fill, ink_fill, comment):
    box, letter = mark_paths(s, t, t, **w)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!-- {comment} -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="{size}dp" android:height="{size}dp"
    android:viewportWidth="{size}" android:viewportHeight="{size}">
    <path android:fillColor="{box_fill.upper()}" android:pathData="{box}" />
    <path android:fillColor="{ink_fill.upper()}" android:pathData="{letter}" />
</vector>
'''


ADAPTIVE_XML = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />
</adaptive-icon>
'''

jobs = []


def w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def raster(svg_path, out, px, transparent=False):
    jobs.append(dict(svg=str(svg_path), out=str(out), px=px, transparent=transparent))


def variant(root, ground, box_fill, ink_fill, edge):
    """One complete launcher set. edge: hairline colour for the legacy shapes (None for a coloured ground)."""
    S, T = 1.0, (108 - 48) / 2                  # the 48-unit logo grid maps 1:1 to dp; handles sit 29 dp from the centre (safe radius 33)
    src = root / "svg"
    fg = mark_svg(S, T, ICON, box_fill, ink_fill)
    w(src / "ic_launcher_foreground.svg", svg(108, fg))
    w(src / "ic_launcher_background.svg", svg(108, "", bg=ground))
    w(src / "ic_launcher_monochrome.svg", svg(108, mark_svg(S, T, ICON, "#000000", "#000000")))
    w(src / "ic_launcher_full.svg", svg(108, fg, bg=ground))
    # legacy shapes, 48 dp grid: a square with the brand's small radius and a disc, mark at 62% of the tile
    ls = 0.64
    lt = (48 - 48 * ls) / 2
    lm = mark_svg(ls, lt, ICON, box_fill, ink_fill)
    stroke = f' stroke="{edge}" stroke-width="0.75"' if edge else ""
    inset = 0.375 if edge else 0
    w(src / "legacy_square.svg", svg(48, lm, extra=f'<rect x="{1 + inset}" y="{1 + inset}" width="{46 - 2 * inset}" height="{46 - 2 * inset}" rx="3" fill="{ground}"{stroke}/>'))
    w(src / "legacy_round.svg", svg(48, lm, extra=f'<circle cx="24" cy="24" r="{23 - inset}" fill="{ground}"{stroke}/>'))
    # Play Store: full-bleed square, no alpha; Play applies its own rounded mask
    ps = 512 * 0.56 / 48
    w(src / "play_store.svg", svg(512, mark_svg(ps, (512 - 48 * ps) / 2, ICON, box_fill, ink_fill), bg=ground))

    res = root / "res"
    w(res / "mipmap-anydpi-v26/ic_launcher.xml", ADAPTIVE_XML)
    w(res / "mipmap-anydpi-v26/ic_launcher_round.xml", ADAPTIVE_XML)
    w(res / "values/ic_launcher_background.xml", f'<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">{ground.upper()}</color>\n</resources>\n')
    w(res / "drawable/ic_launcher_foreground.xml", vector_xml(108, S, T, ICON, box_fill, ink_fill, "HeOCR launcher icon, foreground layer. 108 dp canvas; the mark stays inside the 66 dp safe circle."))
    w(res / "drawable/ic_launcher_monochrome.xml", vector_xml(108, S, T, ICON, "#000000", "#000000", "HeOCR launcher icon, monochrome layer for themed icons (Android 13+). The system recolours it."))
    for dpi, px in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        raster(src / "legacy_square.svg", res / f"mipmap-{dpi}/ic_launcher.png", px, True)
        raster(src / "legacy_round.svg", res / f"mipmap-{dpi}/ic_launcher_round.png", px, True)
    raster(src / "play_store.svg", root / "play-store-icon-512.png", 512)
    # the same icon under the file names Briefcase's Android template reads (icon = "icons/android/heocr")
    b = root / "briefcase"
    for px in (48, 72, 96, 144, 192):
        raster(src / "legacy_square.svg", b / f"heocr-square-{px}.png", px, True)
        raster(src / "legacy_round.svg", b / f"heocr-round-{px}.png", px, True)
    for px in (108, 162, 216, 324, 432):
        raster(src / "ic_launcher_full.svg", b / f"heocr-adaptive-{px}.png", px)
    raster(src / "ic_launcher_full.svg", root / "_full_1024.png", 1024)
    raster(src / "ic_launcher_monochrome.svg", root / "_mono_1024.png", 1024, True)


variant(OUT / "launcher", WHITE, BLUE, INK, "#b9c1de")
variant(OUT / "launcher/alternate-blue", BLUE, WHITE, WHITE, None)

# ---------------- splash: 288 dp canvas, icon inside the 192 dp circle ----------------
sp = OUT / "splash"
SS = 2.5                                  # mark 120 dp wide; its corners sit 85 dp from the centre (limit 96)
ST = (288 - 48 * SS) / 2
w(sp / "svg/splash_icon.svg", svg(288, mark_svg(SS, ST, LOGO, BLUE, INK)))
w(sp / "svg/splash_icon_night.svg", svg(288, mark_svg(SS, ST, LOGO, NIGHT_BLUE, NIGHT_INK)))
w(sp / "res/drawable/splash_icon.xml", vector_xml(288, SS, ST, LOGO, BLUE, INK, "HeOCR splash icon, light. 288 dp canvas; the mark stays inside the 192 dp circle."))
w(sp / "res/drawable-night/splash_icon.xml", vector_xml(288, SS, ST, LOGO, NIGHT_BLUE, NIGHT_INK, "HeOCR splash icon, night."))
w(sp / "res/values/splash.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="splash_background">{WHITE.upper()}</color>
</resources>
''')
w(sp / "res/values-night/splash.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="splash_background">{NIGHT_BG.upper()}</color>
</resources>
''')
w(sp / "res/values/splash_theme_example.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Example only: how the splash resources are meant to be wired on Android 12+ (API 31).
     heocr-app decides where this lives in the Briefcase template. -->
<resources>
    <style name="HeOCR.Splash" parent="android:Theme.Material.Light.NoActionBar">
        <item name="android:windowSplashScreenBackground">@color/splash_background</item>
        <item name="android:windowSplashScreenAnimatedIcon">@drawable/splash_icon</item>
        <item name="android:windowBackground">@color/splash_background</item>
    </style>
</resources>
''')
raster(sp / "svg/splash_icon.svg", sp / "png/splash_icon-288.png", 288, True)
raster(sp / "svg/splash_icon.svg", sp / "png/splash_icon-1152.png", 1152, True)
raster(sp / "svg/splash_icon_night.svg", sp / "png/splash_icon_night-288.png", 288, True)
raster(sp / "svg/splash_icon_night.svg", sp / "png/splash_icon_night-1152.png", 1152, True)
# Briefcase's template takes square images for its splash at these sizes: the mark on its ground, no rounding
bs = 0.42
for name, bg, bf, inkf in (("", WHITE, BLUE, INK), ("-night", NIGHT_BG, NIGHT_BLUE, NIGHT_INK)):
    w(sp / f"svg/splash_square{name}.svg", svg(48, mark_svg(bs, (48 - 48 * bs) / 2, LOGO, bf, inkf), bg=bg))
    for px in (320, 480, 640, 960, 1280):
        raster(sp / f"svg/splash_square{name}.svg", sp / f"briefcase{name}/heocr-square-{px}.png", px)

(HERE / "raster_jobs.json").write_text(json.dumps(jobs))
print(len(jobs), "raster jobs")
