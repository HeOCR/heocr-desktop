# Third-party components in HeOCR

HeOCR (the app) is Apache-2.0. It bundles the components below, all under permissive licences; none is
copyleft. The full licence texts are inside the app: Tesseract's components under
`resources/licenses/`, and each Python package's in its own `*.dist-info` folder.

## Reading documents

| Component | Version | Licence | What it does |
|---|---|---|---|
| heocr | 0.1.0rc1 | Apache-2.0 | Reads the document and decides the route |
| pypdfium2, with PDFium | 5.15.2 | Apache-2.0 or BSD-3-Clause; PDFium BSD-3-Clause, its parts listed in the package's `LICENSES/` | PDF pages, text layer and rendering |
| Pillow, with its image libraries | 13.0.0 | MIT-CMU (HPND). Bundled: libjpeg-turbo (IJG and BSD-3), libpng (PNG licence), libtiff (libtiff licence), libwebp (BSD-3), OpenJPEG (BSD-2), libavif (BSD-2), FreeType (FreeType Licence), HarfBuzz (MIT), Little CMS (MIT), Brotli (MIT), XZ (0BSD), zlib-ng (zlib), libxcb and libXau (MIT) | Images |
| defusedxml | 0.7.1 | PSF-2.0 | Safe XML for Word documents |

## OCR

| Component | Version | Licence | Notes |
|---|---|---|---|
| Tesseract OCR | 5.5.3 | Apache-2.0 | Built from source, statically, with no training tools, no libarchive and no curl |
| Leptonica | 1.87.0 | BSD-2-Clause (Leptonica licence) | PNG and zlib support only |
| libpng | 1.6.58 | PNG Reference Library License v2 | |
| zlib | 1.3.1 | zlib | Windows only; macOS provides its own |
| `heb.traineddata`, from tessdata_best 4.1.0 | 4.1.0 | Apache-2.0 | Hebrew; sha256 `dbaa827a…abdae5`, the model heocr's release gate used |
| `eng.traineddata`, from tessdata_fast 4.1.0 | 4.1.0 | Apache-2.0 | heocr's second reading of numbers |

## The window

| Component | Licence | Platform |
|---|---|---|
| pywebview 6.2.1 | BSD-3-Clause | both |
| bottle, proxy_tools | MIT, BSD-3-Clause | both (pywebview's dependencies) |
| PyObjC | MIT | macOS |
| pythonnet, clr_loader, cffi | MIT | Windows |
| Microsoft Edge WebView2 SDK (loader and interop assemblies, inside pywebview) | BSD-3-Clause | Windows |
| Python | PSF-2.0 | both (from the BeeWare support package) |

## Not included

- **LibreOffice** (MPL-2.0, copyleft). Without it, DOC, RTF and ODT files are not read, and the app says so. When LibreOffice is installed on the computer, heocr uses it.
- No network component, and no telemetry.
