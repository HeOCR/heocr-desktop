"""The app's work, without any window: find the bundled Tesseract, read a file with heocr, and
summarise what heocr did.

Everything runs on this machine. heocr is called with its defaults (the release gate's settings), and
the bundled Tesseract and models are used when present: ``resources/tesseract`` and
``resources/tessdata`` next to this file.
"""
from __future__ import annotations

import contextlib
import json
import os
import shutil
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

import heocr

RESOURCES = Path(__file__).resolve().parent / "resources"
EXE = "tesseract.exe" if sys.platform == "win32" else "tesseract"

# What the open-file dialog offers. heocr decides the format from the content, never the name.
OPEN_TYPES = ("pdf", "docx", "doc", "png", "jpg", "jpeg", "tif", "tiff")

# Readable labels for heocr's routes and sources.
ROUTES = {
    "text_layer": "text_layer",
    "ocr": "ocr",
    "office_xml": "office",
    "converted_docx": "office",
    "converted_xlsx": "office",
    "converted_pptx": "office",
    "html": "html",
}


def bundled_tesseract() -> Path | None:
    exe = RESOURCES / "tesseract" / EXE
    return exe if exe.is_file() else None


def bundled_tessdata() -> Path | None:
    folder = RESOURCES / "tessdata"
    return folder if (folder / "heb.traineddata").is_file() else None


def configure() -> dict:
    """Point heocr at the bundled Tesseract and models. Returns what is in use, for the About view."""
    exe, data = bundled_tesseract(), bundled_tessdata()
    if exe and data:
        os.environ["HEOCR_TESSERACT"] = str(exe)
        os.environ["TESSDATA_PREFIX"] = str(data)
    return {
        "tesseract": "bundled" if exe else ("system" if shutil.which("tesseract") else "none"),
        "models": sorted(p.stem for p in data.glob("*.traineddata")) if data else [],
        "libreoffice": bool(shutil.which("soffice") or shutil.which("libreoffice")
                            or Path("/Applications/LibreOffice.app").exists()),
        "heocr": heocr.__version__,
    }


def page_count(path) -> int | None:
    """Pages to expect, for the progress bar: PDF pages or image frames. None when unknown."""
    path = Path(path)
    try:
        with path.open("rb") as f:
            head = f.read(8)
    except OSError:
        return None
    if head.startswith(b"%PDF"):
        try:
            import pypdfium2
            pdf = pypdfium2.PdfDocument(str(path))
            try:
                return len(pdf)
            finally:
                pdf.close()
        except Exception:  # noqa: BLE001 - the progress bar falls back to indeterminate
            return None
    try:
        from PIL import Image
        with Image.open(path) as im:
            return int(getattr(im, "n_frames", 1) or 1)
    except Exception:  # noqa: BLE001
        return None


class Progress:
    """Pages started, counted through heocr's per-page time check (called once before each page)."""

    def __init__(self, total: int | None):
        self.total = total
        self.done = 0
        self.lock = threading.Lock()

    def tick(self):
        with self.lock:
            self.done += 1

    def fraction(self) -> float | None:
        if not self.total:
            return None
        with self.lock:
            return min(self.done, self.total) / self.total


@contextlib.contextmanager
def _counting(progress: Progress):
    """Count heocr's page-loop time checks. Internal to heocr 0.1, so it is optional: when a module no
    longer has the hook, the bar is indeterminate instead."""
    patched = []
    for name in ("heocr.pdf.reader", "heocr.images"):
        mod = sys.modules.get(name)
        if mod is None:
            try:
                __import__(name)
                mod = sys.modules[name]
            except ImportError:
                continue
        original = getattr(mod, "time_up", None)
        if not callable(original):
            continue

        def counted(doc, _original=original):
            progress.tick()
            return _original(doc)

        mod.time_up = counted
        patched.append((mod, original))
    try:
        yield
    finally:
        for mod, original in patched:
            mod.time_up = original


@dataclass
class Result:
    text: str
    markdown: str
    record: dict
    format: str
    pages: int
    routes: list = field(default_factory=list)   # [(route, [page numbers])], or [(route, None)] without pages
    unread: list = field(default_factory=list)   # [(reason, detail)]
    flags: list = field(default_factory=list)

    def json(self) -> str:
        return json.dumps(self.record, ensure_ascii=False, indent=2) + "\n"


def summarise(doc) -> tuple[list, list]:
    routes: dict[str, list] = {}
    if doc.pages:
        for p in doc.pages:
            routes.setdefault(ROUTES.get(p.route, p.route or "unknown"), []).append(p.index + 1)
    else:
        for b in doc.blocks:
            routes.setdefault(ROUTES.get(b.source, b.source or "unknown"), None)
    unread = [(u.reason, getattr(u, "detail", "") or "") for u in doc.unread]
    return list(routes.items()), unread


def convert(path, progress: Progress | None = None) -> Result:
    path = Path(path)
    with _counting(progress) if progress else contextlib.nullcontext():
        doc = heocr.extract(path)
    routes, unread = summarise(doc)
    return Result(text=doc.text, markdown=doc.markdown, record=doc.to_dict(), format=doc.format,
                  pages=doc.page_count or len(doc.pages), routes=routes, unread=unread, flags=list(doc.flags))
