# Agent instructions

## Setup and validation
- Install: `pip install -e . briefcase==0.4.7`
- Tesseract and models: `python scripts/build_tesseract.py --out vendor` (CI builds it), then
  `python scripts/vendor.py --tesseract vendor`.
- Test: `python -m unittest discover -s tests -t .`
- CI builds macOS and Windows on every PR and smoke-tests the packaged app on invented fixtures.

## Branching and pull requests
- Start from the latest `main`. Branch as `<tool>/<topic>`. Use Conventional Commits.
- Agent-authored PR bodies begin with `Agent: <role>[<tool>#<host>] | Thread: <thread> @ heocr-desktop`.
- Do not merge your own PR. Every PR waits for green CI and maintainer review.

## Hard boundaries
- **Offline.** The app makes no network connection and has no telemetry. `offline.py` refuses
  connections to other machines, and the page loads nothing remote (a content security policy of
  `default-src 'none'`). Don't add an update check, crash reporter, analytics or remote font.
- **Permissive licences only** in what the app bundles. No copyleft component (LibreOffice stays out;
  heocr uses it only when the user installed it). Every bundled component is listed in
  `src/heocr_desktop/THIRD_PARTY_LICENSES.md`, with its licence text inside the app.
- **Test text is invented,** never copied from real documents, even generic ones. Fixtures are made
  by `tests/synth/` and `scripts/make_fixtures.py`.
- No credentials, signing identities' secrets, local machine paths or private dataset names in the
  repository.
- Releases (GitHub Releases, the site's download page) need the maintainers' go.
