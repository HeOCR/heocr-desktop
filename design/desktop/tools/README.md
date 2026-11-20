# How the files in `design/desktop/` were produced

Reference scripts; the app does not need them. They need Python 3 with Pillow and fontTools, and Node with Playwright (Chromium).

```
python make_desktop.py            # mockups/*.html, strings/strings.json, icons/in-app/*.svg
node render.js                    # mockups/png/** at 1100x760 and 720x520, light and night; also loads 1600x1000 and reports overflow
python make_standalone.py         # css/desktop-standalone.css
python make_icons.py              # app icon and installer SVG sources
node raster.js                    # their PNGs (reads icon_jobs.json)
python pack_icons.py              # heocr.icns, heocr.ico, the iconset, the MSI BMPs
```

`make_desktop.py` imports the Android design's generator (`design/android/tools/make_screens.py`) for the shared icon drawings and the invented sample document, so the two designs cannot drift. `hbrand.py` and `fonts/` are the same drawing helper and static font files as in the asset pack.

On a Mac, `iconutil -c icns ../icons/app-icon/macos/heocr.iconset` builds the complete `.icns`, including the 16 and 32 pt base sizes that Pillow's writer leaves out.
