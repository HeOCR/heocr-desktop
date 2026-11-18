# HeOCR for the desktop

Drop in a PDF, a Word document or an image, and get its Hebrew text out, with its headings, paragraphs and tables. For macOS and Windows. **Fully offline:** your files never leave the computer, and the app makes no network connections and collects nothing.

It is a window around [heocr](https://github.com/HeOCR/heocr), HeOCR's open pipeline for Hebrew documents, with Tesseract OCR and the Hebrew model bundled. Apache-2.0.

## What it does

- **Opens** PDF, DOCX, DOC, PNG, JPEG and TIFF, by drag and drop or the open button. heocr decides the format from the content, not the file name.
  - DOC needs LibreOffice, which is not bundled because its licence is copyleft. If LibreOffice is installed, heocr uses it; otherwise the app says how to proceed.
- **Shows** the text right to left where it is Hebrew, with headings, paragraphs and tables. A plain-text view is one click away.
- **Says how each page was read:**
  - PDF text layer;
  - OCR;
  - the Word document itself.

  It also notes what could not be read, and why.
- **Copies** the text, or saves it as `.txt`, as `.md` (Markdown), or as `.json` (heocr's full `heocr_document.v1` record).
- **Progress:** a bar, page by page, for long PDFs.
- **Language:** Hebrew or English, following the system, with a toggle.

OCR text is a reading, not a verified transcript, and the app says so.

## Inside

| Part | |
|---|---|
| heocr 0.1.0rc1 | The release candidate in HeOCR's release gate; 0.1.0 after the verdict |
| Tesseract 5.5.3 | Built from source by `scripts/build_tesseract.py`, statically, with Leptonica, libpng and zlib only |
| Models | `heb` from tessdata_best and `eng` (for heocr's second reading of numbers) from tessdata_fast, both 4.1.0 and pinned by sha256: the models heocr's release gate used |
| Window | [pywebview](https://pywebview.flowrl.com): the system's own web view (WebKit on macOS, WebView2 on Windows), showing one inline page |
| Packaging | [Briefcase](https://briefcase.readthedocs.io): a signed `.app` and DMG for macOS, an MSI for Windows |

Every bundled component is permissive. The list is in [THIRD_PARTY_LICENSES.md](src/heocr_desktop/THIRD_PARTY_LICENSES.md), and in the app's About box.

### Why pywebview inside Briefcase

Briefcase gives one codebase for a signed, notarisable macOS app and a Windows MSI. For the window, Toga (Briefcase's own toolkit) has no drop-target API, and right-to-left mixed text and tables are what a web view does best. pywebview's DOM events deliver dropped files as paths, on both systems. The page is inline, so nothing is fetched.

## Building

```sh
pip install -e . briefcase==0.4.7
python scripts/wheels.py                             # heocr (pinned) and proxy_tools as wheels, for Briefcase
python scripts/build_tesseract.py --out vendor      # or download CI's tesseract-<os> artifact into vendor/
python scripts/vendor.py --tesseract vendor          # Tesseract, configs, models and licences into resources/
python -m unittest discover -s tests -t .

briefcase create macOS app && briefcase build macOS app
briefcase package macOS app --identity "Developer ID Application: …"   # signed, hardened runtime
```

**Notarisation** needs a `notarytool` keychain profile. With one, `briefcase package macOS app --identity "…" --notarize` signs, notarises and staples the DMG.

**Windows:** `briefcase create windows app && briefcase build windows app && briefcase package windows app --adhoc-sign` makes an unsigned MSI. CI has a placeholder step for signing once a certificate exists.

**Universal macOS builds:**
- The app is built for arm64 first.
- `build_tesseract.py --arch x86_64` cross-builds Tesseract for Intel, and `vendor.py` joins every `tesseract-<arch>` it finds with `lipo`.
- Then set `universal_build = true` in `pyproject.toml`.

## Tests

`python -m unittest discover -s tests -t .` runs:
- one fixture of each type, all invented text: a text-layer PDF, a DOCX, a scanned PDF, PNG, JPEG and TIFF;
- a DOC without LibreOffice;
- the Markdown renderer, including escaping;
- the offline guard;
- the strings.

CI also builds both apps and converts the same fixtures with the built app's own Python, Tesseract and models (`HeOCR --smoke report.json FILE…`). The Windows job does so after installing the MSI too.
