#!/usr/bin/env python3
"""After ``briefcase create android``: put the design's launcher and splash resources in the Gradle project.

Briefcase writes the launcher and splash PNGs from ``icons/android/`` (the design's Briefcase-named files,
``design/android/launcher/briefcase/`` and ``splash/briefcase/``). What it has no setting for comes from
the design itself (design/android/SPEC.md §15):

- the adaptive icon with a vector foreground and a **monochrome** layer for themed icons (Android 13+),
  on the design's background colour (``launcher/res/``);
- the night splash: the window background ``#141414`` and the night mark (``splash/briefcase-night/``),
  chosen by Android from the phone's dark-mode setting (``values-night``, ``mipmap-night-*``).

    python scripts/android_design_res.py

Safe to run again; Gradle compiles the hand-written vector drawables, so the build checks them.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "design" / "android"
RES = ROOT / "build" / "heocr_mobile" / "android" / "gradle" / "app" / "src" / "main" / "res"
# Briefcase's template: splash.png per density, from the square sizes it reads (its briefcase.toml).
SPLASH = {"mdpi": 320, "hdpi": 480, "xhdpi": 640, "xxhdpi": 960, "xxxhdpi": 1280}
NIGHT_BACKGROUND = "#141414"


def main() -> None:
    if not RES.is_dir():
        raise SystemExit(f"no Gradle project at {RES.relative_to(ROOT)}; run briefcase create android first")
    launcher = DESIGN / "launcher" / "res"
    for rel in (
        "drawable/ic_launcher_foreground.xml",
        "drawable/ic_launcher_monochrome.xml",
        "mipmap-anydpi-v26/ic_launcher.xml",
        "mipmap-anydpi-v26/ic_launcher_round.xml",
        "values/ic_launcher_background.xml",
    ):
        target = RES / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(launcher / rel, target)
    night = RES / "values-night"
    night.mkdir(exist_ok=True)
    (night / "colors_heocr_night.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        f'    <color name="colorSplashScreenBackground">{NIGHT_BACKGROUND}</color>\n</resources>\n',
        "utf-8",
    )
    for density, size in SPLASH.items():
        folder = RES / f"mipmap-night-{density}"
        folder.mkdir(exist_ok=True)
        shutil.copy2(DESIGN / "splash" / "briefcase-night" / f"heocr-square-{size}.png", folder / "splash.png")
    print("design resources in", RES.relative_to(ROOT))


if __name__ == "__main__":
    main()
