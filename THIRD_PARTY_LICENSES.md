# Third-party components in HeOCR desktop

HeOCR desktop is Apache-2.0. This is every component its macOS app and Windows installer contain, with each one's licence. **All are permissive. None is copyleft.** The licence texts ship inside the app: Python packages carry theirs in their `*.dist-info` folders; Tesseract, Leptonica and the image libraries have theirs in `resources/licenses/`.

- **Audited:** 2026-11-18, on the macOS universal2 bundle (Briefcase 0.4.7, Python 3.12 support revision 13) and on the contents of the Windows x64 MSI built in CI (every PE file identified by its version resource; every licence text in the cabinet scanned for GPL terms).
- **Method:** each Python package's own licence metadata and files; each native library's licence from its vcpkg `copyright` file; `otool -L` / `dumpbin /dependents` on every executable we build, to check it links only to the OS.

## The pipeline

| Component | Version | Licence | Notes |
|---|---|---|---|
| heocr | 0.1.2 (`ac1ad20`) | Apache-2.0 | Its NOTICE ships in its `dist-info`. heocr's own audit of its dependencies: [THIRD_PARTY_LICENSES.md](https://github.com/HeOCR/heocr/blob/main/THIRD_PARTY_LICENSES.md) |
| pypdfium2 | 5.15.2 | Apache-2.0 or BSD-3-Clause | Bundles PDFium (BSD-3-Clause) with Abseil, Highway, AGG, Dragonbox, fast_float, FreeType (FTL), HarfBuzz (MIT), ICU (Unicode-3.0), Little CMS (MIT), libjpeg-turbo, OpenJPEG, libpng, libtiff, simdutf, zlib, Brotli, libyuv and LLVM libc pieces, all permissive; listed in heocr's audit |
| Pillow | 13.0.0 | MIT-CMU (HPND) | Bundles libjpeg-turbo, libtiff, libwebp, OpenJPEG, libpng, zlib-ng, FreeType (FTL), HarfBuzz, Little CMS, libavif, Brotli, liblzma (0BSD), libxcb/libXau (MIT); listed in heocr's audit |
| defusedxml | 0.7.1 | PSF-2.0 | |

## OCR

| Component | Version | Licence | Notes |
|---|---|---|---|
| Tesseract OCR | 5.5.3 | Apache-2.0 | Built from the release tarball by `scripts/build_tesseract.py`: one static executable; no libcurl, no libarchive, no OpenMP, no training tools. Its `configs` folder ships with it |
| tessdata_best `heb` (`e12c65a`), tessdata_fast `eng` | 4.1.0 | Apache-2.0 | sha256 `dbaa827a…` and `7d4322bd…`, pinned in `tesseract/pins.json`: the files heocr's release gate ran with |
| Leptonica | 1.87.0 | Leptonica licence (BSD-2-Clause style) | Static, via vcpkg 2026.10.16 |
| libpng | 1.6.59 | PNG Reference Library License v2 | Static, inside Tesseract |
| zlib | 1.3.2 | zlib | Static, inside Tesseract |
| libjpeg-turbo | 3.2.0 | IJG, BSD-3-Clause and zlib | Static, inside Tesseract |
| libtiff | 4.7.2 | libtiff licence (BSD-style) | Static, inside Tesseract |
| liblzma (XZ Utils) | from vcpkg | 0BSD | Static, inside Tesseract (libtiff's LZMA codec) |
| giflib | 6.1.3 | MIT | Static, inside Tesseract |
| libwebp | 1.6.0 | BSD-3-Clause | Static, inside Tesseract |
| OpenJPEG | 2.5.4 | BSD-2-Clause | Static, inside Tesseract |
| libspng | from vcpkg | BSD-2-Clause | Static, inside Tesseract |

heocr passes Tesseract PNG images only; Leptonica's other image libraries come with its vcpkg port.

## The window

| Component | Version | Licence | Platform |
|---|---|---|---|
| pywebview | 6.2.1 | BSD-3-Clause | both |
| bottle | 0.13.4 | MIT | both (a pywebview dependency; the app never starts its server) |
| proxy_tools | 0.1.0 | MIT | both |
| typing_extensions | 4.16.0 | PSF-2.0 | both |
| PyObjC (core, Cocoa, Quartz, WebKit, Security, UniformTypeIdentifiers) | 13.0 | MIT | macOS |
| pythonnet, clr_loader | 3.2.1, 0.3.1 | MIT | Windows |
| distlib launcher (`t64.exe`, the console-script stubs pip writes) | from pip | PSF-2.0 / MIT | Windows |
| cffi, pycparser | 2.1.1, from PyPI | MIT, BSD-3-Clause | Windows |
| Microsoft WebView2 SDK 1.0.3856.49 (`WebView2Loader.dll`, `Microsoft.Web.WebView2.Core.dll`, `.WinForms.dll`) | inside pywebview | BSD-3-Clause (its NuGet package's LICENSE.txt; its NOTICE lists ANTLR 3 and StringTemplate 4, both BSD-3-Clause) | Windows. Published by Microsoft as binaries. pywebview omits the texts, so the app ships them (`third_party/webview2/`). The WebView2 runtime itself is part of Windows 10 and 11 and is not bundled |

## Python

| Component | Licence | Notes |
|---|---|---|
| CPython 3.12 | PSF-2.0 | From Briefcase's support packages (macOS: Python-Apple-support; Windows: python.org's embeddable distribution). Its `LICENSE.txt` ships with it and lists the libraries below |
| OpenSSL 3 | Apache-2.0 | `_ssl`, `_hashlib`; the app never opens a connection |
| libffi | MIT | `ctypes` |
| SQLite | Public domain | |
| XZ Utils (liblzma) | 0BSD | |
| bzip2 | bzip2 licence (BSD-style) | |
| libmpdec | BSD-2-Clause | `decimal` |
| Expat | MIT | |
| Microsoft Visual C++ runtime (`vcruntime140*.dll`) | Microsoft redistributable | Windows only: ships with every python.org Windows Python; a system runtime, not modified |

On macOS the app removes the parts of Python it never uses: Tcl/Tk, curses (ncurses), IDLE and the test suite (`cleanup_paths` in `pyproject.toml`). Python's `readline` module links to macOS's own libedit.

## Copyleft words found, and why none apply

- **FreeType** (inside PDFium and Pillow) is dual-licensed; its FTL applies, not the GPLv2 alternative.
- **pypdfium2** ships `BUILD_LICENSES/cibw_musl/libgcc_and_libstdc++.txt` (GCC's licence with the Runtime Library Exception) in every wheel; it applies to its musl-Linux builds, not to the macOS or Windows binaries, and the exception allows use in non-GPL programs anyway.
- **Microsoft's WebView2 NOTICE** carries Microsoft's standard sentence about LGPL libraries; the components it lists are BSD-3-Clause.

## Not bundled, on purpose

- **LibreOffice** (MPL-2.0), which heocr can use for DOC, RTF, ODT, XLS, ODS, PPT and ODP. The app turns conversion off and says so for those files.
- **HeOCR's trained models**, which heocr can download on request. The app never downloads anything; it runs stock Tesseract `heb`, heocr's default.

## Acknowledgements the licences ask for

FreeType (inside PDFium and Pillow):

> Portions of this software are copyright © 2025 The FreeType Project (www.freetype.org). All rights reserved.
