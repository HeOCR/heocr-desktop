# How the files in `design/android/` were produced

Reference scripts. They are not part of the app and nothing in the build needs them. They need Python 3 with Pillow, and Node with Playwright (Chromium) for the PNG renders. Run them from this folder:

```
python make_screens.py        # mockups/*.html, icons/in-app/*.svg, strings/strings.json
node render.js                # mockups/png/**  (412x915 and 360x800, light and night, at 2x)
node font_scale_check.js      # mockups/png/font-scale-200/**
python compress_mockups.py    # palette-compress the mockup renders
python make_standalone.py     # css/fonts-embedded.css, css/*-standalone.css
python make_launcher.py       # launcher/** and splash/** sources and resource files
node raster.js raster_jobs.json   # their PNGs
python mask_previews.py       # launcher/**/preview-masks.png
python make_store.py          # compositions for the store graphics
node store.js                 # store/fastlane/**/images/*.png
```

`fonts/subset_fonts.py` rebuilds the font files from the upstream variable fonts.

All text in the mockups is invented. Nothing here reads from the network.
