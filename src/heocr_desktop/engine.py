"""The app's bridge to heocr: bundled Tesseract, progress, cancel, and the offline guard.

heocr itself is used as released. Nothing here changes how it reads a document:

- **OCR** runs the Tesseract binary and models shipped inside the app (``resources/``), never
  one found on the system, so every user gets the same reading.
- **Conversion** (LibreOffice, for DOC/RTF/ODT/XLS/ODS/PPT/ODP) is off: the app ships no
  copyleft tool and starts no program it did not bring. Those files get a clear message.
- **Models** are never downloaded: the app runs stock Tesseract ``heb``, heocr's default.
- **Progress** comes from wrapping heocr's per-page step. The wrapper calls the original with
  the same arguments, so the reading is byte for byte what ``heocr.extract`` gives.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import heocr

RESOURCES = Path(__file__).resolve().parent / "resources"

# Formats heocr reads only through LibreOffice, which the app does not ship.
NEEDS_CONVERTER = {"doc", "rtf", "odt", "xls", "ods", "ppt", "odp"}

# What the open dialog offers. heocr decides the format from the content, never the name.
SUPPORTED_SUFFIXES = (
    "pdf", "docx", "doc", "png", "jpg", "jpeg", "tif", "tiff",
    "xlsx", "pptx", "html", "htm", "gif", "bmp", "webp", "jp2",
)


class Cancelled(Exception):
    """The user pressed Cancel."""


# -- the offline guard ---------------------------------------------------------------------


class NetworkBlocked(OSError):
    pass


_LOOPBACK = ("127.0.0.1", "::1", "localhost")


def _is_loopback(address) -> bool:
    host = address[0] if isinstance(address, tuple) and address else address
    return isinstance(host, str) and (host in _LOOPBACK or host.startswith("127."))


def install_offline_guard() -> None:
    """Refuse every network connection from this process, except loopback.

    The app makes no network calls. This turns that promise into a check: a library that
    tried would fail loudly instead of sending anything. Loopback stays open because some
    event loops build their wake-up pipe from a local socket pair.
    """
    if getattr(socket, "_heocr_offline", False):
        return
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def connect(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6) and not _is_loopback(address):
            raise NetworkBlocked(f"HeOCR is offline: refused a connection to {address!r}")
        return real_connect(self, address)

    def connect_ex(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6) and not _is_loopback(address):
            raise NetworkBlocked(f"HeOCR is offline: refused a connection to {address!r}")
        return real_connect_ex(self, address)

    def getaddrinfo(host, *args, **kwargs):
        if host is not None and not _is_loopback(host if isinstance(host, str) else str(host)):
            raise NetworkBlocked(f"HeOCR is offline: refused to look up {host!r}")
        return real_getaddrinfo(host, *args, **kwargs)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.getaddrinfo = getaddrinfo
    socket._heocr_offline = True


# -- Windows: no console window per Tesseract call -----------------------------------------


def hide_child_consoles() -> None:
    """On Windows a GUI app's console children each open a window; heocr runs Tesseract per line."""
    if sys.platform != "win32" or getattr(subprocess, "_heocr_hidden", False):
        return
    real_init = subprocess.Popen.__init__
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    def __init__(self, *args, **kwargs):
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | no_window
        return real_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = __init__
    subprocess._heocr_hidden = True


# -- bundled Tesseract ---------------------------------------------------------------------


def tesseract_path() -> Path | None:
    """The Tesseract shipped in the app, or ``None`` in a development checkout without one."""
    name = "tesseract.exe" if sys.platform == "win32" else "tesseract"
    candidate = RESOURCES / "tesseract" / name
    if candidate.is_file():
        return candidate
    # Development only: HEOCR_DESKTOP_DEV_TESSERACT points at a local build or a system one.
    dev = os.environ.get("HEOCR_DESKTOP_DEV_TESSERACT")
    return Path(dev) if dev else None


def tessdata_path() -> Path | None:
    folder = RESOURCES / "tessdata"
    if (folder / "heb.traineddata").is_file():
        return folder
    dev = os.environ.get("HEOCR_DESKTOP_DEV_TESSDATA")
    return Path(dev) if dev else None


# -- one conversion ------------------------------------------------------------------------


@dataclass
class Progress:
    done: int = 0
    total: int | None = None
    stage: str = "reading"  # reading | pages | finishing


@dataclass
class Result:
    doc: "heocr.Document | None"
    seconds: float
    kind: str  # ok | needs_converter | unreadable | empty
    format: str = ""
    routes: dict[str, int] = field(default_factory=dict)  # page route -> pages
    sources: dict[str, int] = field(default_factory=dict)  # block source -> blocks
    unread: int = 0
    ocr_available: bool = True
    notes: list[str] = field(default_factory=list)  # the app's own notes, e.g. "numbers_not_rechecked"


_hook_lock = threading.Lock()
_hook_state = threading.local()


def _install_page_hook() -> bool:
    """Wrap heocr's per-page step once, so each conversion can report its pages."""
    try:
        from heocr.pdf import reader
    except ImportError:  # pragma: no cover - a heocr without this module: progress stays indefinite
        return False
    with _hook_lock:
        if getattr(reader, "_heocr_desktop_hooked", False):
            return True
        original_page = getattr(reader, "_read_page", None)
        original_ocr = getattr(reader, "_ocr_page", None)
        if original_page is None:
            return False

        def _read_page(doc, index, *args, **kwargs):
            _tick(doc, index, image=False)
            return original_page(doc, index, *args, **kwargs)

        reader._read_page = _read_page
        if original_ocr is not None:
            # Images (and TIFF frames) are read through _ocr_page directly.
            def _ocr_page(doc, index, *args, **kwargs):
                if doc.format != "pdf":
                    _tick(doc, index, image=True)
                return original_ocr(doc, index, *args, **kwargs)

            reader._ocr_page = _ocr_page
        reader._heocr_desktop_hooked = True
        return True


def _tick(doc, index: int, image: bool) -> None:
    report = getattr(_hook_state, "report", None)
    if report is None:
        return
    if getattr(_hook_state, "cancel", None) is not None and _hook_state.cancel.is_set():
        raise Cancelled()
    report(Progress(done=index, total=doc.page_count, stage="pages"))


def summarize(doc) -> tuple[dict[str, int], dict[str, int]]:
    routes: dict[str, int] = {}
    for page in doc.pages:
        routes[page.route] = routes.get(page.route, 0) + 1
    sources: dict[str, int] = {}
    for block in doc.blocks:
        sources[block.source] = sources.get(block.source, 0) + 1
    return routes, sources


def convert(
    path: str | os.PathLike[str],
    report: Callable[[Progress], None] | None = None,
    cancel: threading.Event | None = None,
) -> Result:
    """Read one file with heocr, as the app does: bundled OCR, no conversion, no downloads."""
    _install_page_hook()
    tess = tesseract_path()
    tessdata = tessdata_path()
    if tessdata is not None:
        os.environ["TESSDATA_PREFIX"] = str(tessdata)
    _hook_state.report = report
    _hook_state.cancel = cancel
    started = time.monotonic()
    try:
        if report:
            report(Progress(stage="reading"))
        options = dict(ocr=tess is not None, tesseract=str(tess) if tess else None, convert=False, ocr_model=None)
        notes: list[str] = []
        doc = heocr.extract(str(path), **options)
    finally:
        _hook_state.report = None
        _hook_state.cancel = None
    if report:
        report(Progress(stage="finishing"))
    seconds = time.monotonic() - started
    routes, sources = summarize(doc)
    document_unread = {u.reason for u in doc.unread if u.scope == "document"}
    if doc.format in NEEDS_CONVERTER and "converter_unavailable" in document_unread:
        kind = "needs_converter"
    elif "not_read" in doc.flags or document_unread & {"format_not_supported", "pdf_unreadable", "pdf_encrypted"}:
        kind = "unreadable"
    elif not doc.text.strip():
        kind = "empty"
    else:
        kind = "ok"
    return Result(
        doc=doc,
        seconds=seconds,
        kind=kind,
        format=doc.format,
        routes=routes,
        sources=sources,
        unread=len(doc.unread),
        ocr_available=tess is not None,
        notes=notes,
    )
