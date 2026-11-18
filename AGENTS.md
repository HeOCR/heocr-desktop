# Agent instructions

## Setup and validation
- Install: `pip install -e ".[test]" briefcase==0.4.7`
- Test: `python -m pytest` (the OCR tests run when a Tesseract is bundled or `HEOCR_DESKTOP_DEV_TESSERACT` / `HEOCR_DESKTOP_DEV_TESSDATA` point at one).
- Tesseract: `python scripts/build_tesseract.py --target <macos-arm64|macos-x86_64|windows-x64> --out build/tess/<target>`, or the **Tesseract** workflow's artifacts; then `python scripts/prebuild_wheels.py` and `python scripts/assemble_resources.py build/tess/<target> [...]`.
- Packaged app: `briefcase create/build macOS|windows`, then `python scripts/smoke_app.py macos|windows`. CI does this on every PR, and also installs the MSI and smoke-tests the installed app.
- On the maintainer's Mac, heavy builds (Tesseract) go through the HeOCR power scheduler.

## Branching and pull requests
- Branch from the latest `main` as `<tool>/<topic>`. Use Conventional Commits.
- Agent-authored PR bodies begin with `Agent: <role>[<tool>#<host>] | Thread: <thread> @ heocr-desktop`.
- Do not merge your own PR. Every PR waits for green CI and maintainer review.

## Hard boundaries
- **Offline.** The app makes no network connection and has no telemetry. `engine.install_offline_guard` refuses every non-loopback connection in the app's process, and the page loads nothing (a content security policy of `default-src 'none'`). Don't add an update check, crash reporter, analytics or remote font.
- **heocr as released.** The app calls `heocr.extract` with the gate's settings (bundled Tesseract, stock models, conversion off). The progress hook wraps heocr's per-page step without changing its arguments or result (`tests/test_engine.py` checks this). Anything that needs a change in heocr goes to heocr as its own PR, after the RC freeze.
- **Models.** The bundled traineddata are exactly the gate's files, pinned by sha256 in `tesseract/pins.json`. Change them only with a new gate record.
- **Permissive licences only** in what the app bundles. No copyleft component; LibreOffice stays out, and conversion is off. Every bundled component is listed in `THIRD_PARTY_LICENSES.md`, with its licence text inside the app.
- **Test text is invented,** never copied from real documents. Fixtures in `tests/fixtures/` come from `garden.source.html`.
- No credentials, signing secrets, local machine paths, build state (`.briefcase/`, `build/`, `wheels/`) or private dataset names in the repository (`tests/test_repo_rules.py`).
- Releases (GitHub Releases, the site's download page) and the SignPath application need the maintainers' go.
