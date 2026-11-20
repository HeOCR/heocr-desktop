# HeOCR for the desktop

**Drop in a PDF, a Word file or an image, and get its Hebrew text out, with its headings, paragraphs and tables.** For macOS and Windows. Free and open source (Apache-2.0).

**Fully offline.** Your files never leave your computer. The app makes no network connections at all: no telemetry, no analytics, no update checks, no downloads. The guarantee is enforced in the app itself, not just promised (see [Privacy](#privacy)).

It is a window around [heocr](https://github.com/HeOCR/heocr), HeOCR's open pipeline for Hebrew documents, with Tesseract OCR and its Hebrew model built in.

> Status: built on heocr 0.2.0, which reads with HeOCR's own model, `heocr_modern_v1`, by default. It writes no niqqud: pointed text comes out unpointed.

## What it does

- **Opens** PDF, Word (DOCX), and images (PNG, JPEG, TIFF; also GIF, BMP, WebP, JPEG 2000), plus Excel (XLSX), PowerPoint (PPTX) and saved web pages (HTML). Drag a file into the window, or use **Open file…**. The format is decided from the file's content, not its name.
  - **Older Word files (.doc), RTF and OpenDocument** need LibreOffice to convert, which the app does not include (its licence is copyleft). The app says so, and asks you to save the file as DOCX or PDF.
- **Shows** the text right to left where it is Hebrew and left to right where it is English, with headings, paragraphs, lists and tables. Three views: formatted, plain text, and Markdown.
- **Says how it was read:**
  - from the PDF's own text layer, when it can be trusted;
  - by OCR, for scans and photos;
  - from the document file itself, for Word, Excel and PowerPoint.
  It also says when parts could not be read (details in the JSON record), and marks OCR text as a reading that may have mistakes.
- **Copies** the text, or **saves** it as `.txt`, `.md` (Markdown, tables kept) or `.json` (heocr's full `heocr_document.v1` record).
- **Progress:** page by page for long PDFs, with Cancel.
- **Language:** Hebrew or English, following your system, with a toggle.

## Download

Not yet. Releases will be on [heocr.github.io](https://heocr.github.io) and on this repository's Releases page:
- **macOS** 13 or later, one app for Apple silicon and Intel: a signed and notarized DMG.
- **Windows** 10 and 11, 64-bit: an MSI installer.

## Privacy

HeOCR does not transfer any information to other networked systems. Concretely:
- the window is one page passed to the system web view as a string, with a content security policy that lets it load nothing (`default-src 'none'`, `connect-src 'none'`);
- the app's own process refuses every network connection except to itself (`engine.install_offline_guard`); a library that tried to connect would fail instead of sending anything;
- heocr's optional model download is never called; OCR uses only the bundled models;
- the only file the app writes on its own is a one-line settings file with your interface language.

## Inside

| Part | Version | Licence |
|---|---|---|
| [heocr](https://github.com/HeOCR/heocr) | 0.2.0 from PyPI (tag `v0.2.0`, `5d41b43`), with HeOCR's own models `heocr_modern_v1` (the default) and `heocr_oldprint_v1` inside | Apache-2.0 |
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | 5.5.3, built from source in CI by `scripts/build_tesseract.py`: static, without network code (no libcurl, no libarchive) | Apache-2.0 |
| Leptonica and image libraries | 1.87.0, via vcpkg `2026.10.16` | BSD-style, see the list |
| OCR models | `heb` from [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) 4.1.0 (`e12c65a`) and `eng` from [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) 4.1.0 (for heocr's second reading of numbers): exactly the files heocr's release gate ran with, pinned by sha256 in `tesseract/pins.json` | Apache-2.0 |
| pypdfium2 / PDFium, Pillow, defusedxml | 5.15.2, 13.0.0, 0.7.1: the versions heocr's gate ran with | Apache-2.0/BSD-3, MIT-CMU, PSF |
| [pywebview](https://pywebview.flowrl.com) | 6.2.1: the system's own web view (WebKit on macOS, WebView2 on Windows) | BSD-3-Clause |
| Python | 3.12, from Briefcase's support packages | PSF |

Every bundled component is permissive; none is copyleft. The full list, with each component's licence, is in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) and in the app's About box. Licence texts ship inside the app.

### Why pywebview inside Briefcase

[Briefcase](https://briefcase.readthedocs.io) builds a signed, notarizable macOS app and a Windows MSI from one Python codebase, which matters because heocr is Python. For the window, Toga (Briefcase's own toolkit) has no drop target, and right-to-left text mixed with English, numbers and tables is what a web view renders best. pywebview gives dropped files as full paths on both systems and uses the web view the OS already has, so nothing heavy is bundled.

## Building

Requires Python 3.12, and for Tesseract CMake, Ninja and a C++ compiler (Xcode command line tools, or MSVC on Windows).

```sh
python -m pip install -e ".[test,desktop]" briefcase==0.4.7
python -m pytest                                     # unit tests; OCR tests need a Tesseract (below)

python scripts/build_tesseract.py --target macos-arm64  --out build/tess/macos-arm64
python scripts/build_tesseract.py --target macos-x86_64 --out build/tess/macos-x86_64
python scripts/prebuild_wheels.py                     # proxy_tools has no wheel on PyPI
python scripts/assemble_resources.py build/tess/macos-arm64 build/tess/macos-x86_64

briefcase create macOS && briefcase build macOS
python scripts/smoke_app.py macos                     # the packaged app reads every fixture
```

Instead of building Tesseract, you can download the `tesseract-<target>` artifacts of the **Tesseract** workflow into `build/tess/`.

- **macOS release:** `scripts/release_mac.sh build/tess/macos-arm64 build/tess/macos-x86_64` signs with the Developer ID Application identity (hardened runtime), smoke-tests the signed app, builds and signs the DMG, and notarizes and staples it when the `heocr-notary` notarytool profile exists.
- **Windows:** CI builds the MSI on `windows-latest`, smoke-tests the built app, installs the MSI silently and smoke-tests the installed app. Release builds will be signed through SignPath Foundation; see [docs/code-signing-policy.md](docs/code-signing-policy.md).

In development, without bundled resources, point the app at a local Tesseract:
`HEOCR_DESKTOP_DEV_TESSERACT=/path/to/tesseract HEOCR_DESKTOP_DEV_TESSDATA=/path/to/tessdata python -m heocr_desktop`.

Test fixtures in `tests/fixtures/` hold invented text only (a made-up community-garden memo, `garden.source.html`). They were made with LibreOffice from that HTML in the OFL fonts David Libre and Alef, and the "scan" is the PDF rendered and degraded with Pillow.

## Code signing policy

Windows builds will be signed by SignPath Foundation (free code signing for open source), after a manual approval for each release. The policy, the team's roles and what gets signed are in [docs/code-signing-policy.md](docs/code-signing-policy.md). macOS builds are signed with the maintainer's Apple Developer ID and notarized by Apple.

## Licence

Apache-2.0. See [LICENSE](LICENSE), [NOTICE](NOTICE) and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

HeOCR is an open Hebrew OCR project: [github.com/HeOCR](https://github.com/HeOCR), [heocr.github.io](https://heocr.github.io).
