# HeOCR desktop: design files

The Bounding Box brand on the macOS and Windows app: every screen as a state of one page, the stylesheets, the app icon, installer images, in-app icons and strings. Prepared 2026-11-20 against `HeOCR/heocr-desktop` at `15041b4` (app 0.1.0). It replaces the direction round and follows the owner's three answers (icon B, Save with a format menu, the index kept).

Start with [`SPEC.md`](SPEC.md). To see the screens, open [`mockups/index.html`](mockups/index.html) or look at `overview.png` and `mockups/png/`.

Nothing here is app code, and nothing here loads anything from the network.

## Index

| Path | What it is |
|---|---|
| `overview.png` | One board with the main screens, the icon and the installer images. |
| `SPEC.md` | Decisions, tokens, the window, screens and flow, the result, problem states, About, components with states, keyboard and menus, motion, right to left, accessibility, icons and installers, brand extensions, what heocr-app must provide, open questions. |
| `css/desktop-standalone.css` | **The one-file build** (94 KB, of which 69 KB is embedded fonts) to replace the `/*STYLE*/` block in `ui/index.html`. |
| `css/desktop.css` | The window: bar, start, drop veil, reading, result chrome, index, menu, toast, messages, About. |
| `css/result.css` | The result view. **Identical to `design/android/css/result.css`.** |
| `css/tokens.css`, `css/fonts-embedded.css` | The Android design's tokens and embedded fonts (the tokens file differs only in its first comment line). |
| `mockups/he/`, `mockups/en/` | 15 files per language. Each is the whole page in one state, set by the classes on `<body>`. No script. |
| `mockups/png/1100x760/`, `mockups/png/720x520/` | Renders of every state, `light/` and `night/`, `he/` and `en/`. |
| `icons/app-icon/` | The app icon: `macos/` (`heocr.icns`, the iconset, the 1024 master), `windows/` (`heocr.ico` and its seven PNGs), `repo-icons/` (the same under the repository's file names), `svg/` (sources), and previews. |
| `icons/installer/` | DMG background (PNG, `@2x`, a preview) and the two MSI images (BMP, with PNG and SVG sources). |
| `icons/in-app/` | 20 SVG icons on a 24 px grid and `icons.json` (which mirror in Hebrew; which are new for the desktop). |
| `strings/strings.json` | Every string and every menu label in Hebrew and English, each marked `app` (already in `i18n.py`), `android`, or `new`. |
| `tools/` | The scripts that produced all of the above. |

## States

| Mockup | Classes on `<body>` | Screen |
|---|---|---|
| `01-start` | `is-start` | Start |
| `02-start-dragging` | `is-start is-dragging` | A file dragged over the window |
| `03-reading` | `is-reading` | Reading |
| `04-result-formatted` | `is-result` | Result, formatted |
| `05-result-text`, `06-result-markdown` | `is-result` | The other two views |
| `07-result-save-menu` | `is-result menu-open` | The Save menu today |
| `07b-result-save-menu-with-word` | same | The Save menu once Word ships |
| `08-result-saved`, `09-result-copied` | `is-result toast-on` | Confirmations |
| `10` to `13` | `is-message` | Needs converting, could not be read, no text, stopped |
| `14-about` | `is-start about-open` | About |

## Source of every asset

| Asset | Source | Licence |
|---|---|---|
| Tokens, result stylesheet, fonts, 14 in-app icons, the toast and notice | The Android design, `design/android/` in this repository | Project's own; fonts OFL 1.1 |
| The mark, the box, the grid | The brand handover in `HeOCR/heocr.github.io` | Project's own |
| App icon, installer images, six new in-app icons, `desktop.css`, the mockups | Made for this handover | Project's own |
| Noto Sans Hebrew, JetBrains Mono | `google/fonts`, subset by `design/android/fonts/subset_fonts.py`; static instances in `tools/fonts/` for outlining the installer images' text | SIL OFL 1.1 |
| Sample document | Invented (the neighbourhood library notice used in the Android mockups) | Project's own |
| Interface strings | `src/heocr_desktop/i18n.py` where they exist, unchanged; the rest new | Project's own |

## Checks made

- All 30 pages loaded at 1100 × 760, 720 × 520 and 1600 × 1000: none scrolls the window in either direction.
- 298 controls checked by script: all are native buttons, links or summaries, and all are labelled.
- The `.ico` holds seven sizes, and its 16, 24 and 32 px frames are the hand-drawn ones, bit for bit.
- New contrast pairs computed (`SPEC.md` §12).
- The generator scripts import the Android generator for shared icons and the sample document.

## Not checked

- **Today's app was not built or run,** so there are no screenshots of it in either language. That needs a Mac or a Windows machine.
- **Nothing was rendered in WebKit.** The renders are Chromium's. The CSS avoids what Safari 16.0 lacks, but that is by reading, not by test.
- The icons and installer images were not installed on macOS or Windows. The `.icns` lacks two base sizes until `iconutil` is run on the iconset.
- VoiceOver and Narrator were not run.
- New Hebrew wording needs the owner's review.

---

`design[claude/claude-code#shay-macbook-m4]@heocr/opensource`
