"""The HeOCR window: drop a file or open one, read it with heocr, copy or save the result.

The interface is one local HTML page inside the system web view (WebKit on macOS, WebView2 on
Windows), passed as a string: no web server, no URL, and a content security policy that lets it
load nothing at all. Python does the reading; the page only shows it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import traceback
from importlib import metadata
from pathlib import Path

from heocr_desktop import engine, exports, i18n, render

UI = Path(__file__).resolve().parent / "ui"
APP_NAME = "HeOCR"


def app_version() -> str:
    try:
        return metadata.version("heocr-desktop")
    except metadata.PackageNotFoundError:
        from heocr_desktop import __version__

        return __version__


def tesseract_version() -> str:
    path = engine.tesseract_path()
    if path is None:
        return "—"
    try:
        out = subprocess.run([str(path), "--version"], capture_output=True, timeout=20, check=False)
        first = (out.stdout or out.stderr).decode("utf-8", "replace").splitlines()
        return first[0].replace("tesseract", "").strip() if first else "?"
    except (OSError, subprocess.SubprocessError):
        return "?"


def bundled_models() -> list[dict]:
    """The OCR models inside the app, with their origin and sha256 (from the build's pins)."""
    try:
        info = json.loads((engine.RESOURCES / "BUILD_INFO.json").read_text("utf-8"))
        files = info["tessdata"]["files"]
    except (OSError, ValueError, KeyError):
        return []
    return [{"name": name, "origin": pin.get("origin", ""), "sha256": pin["sha256"]} for name, pin in sorted(files.items())]


def page_html(language: str) -> str:
    """The whole interface as one HTML string, styles and script inline."""
    import heocr

    boot = {
        "language": language,
        "strings": i18n.STRINGS,
        "version": app_version(),
        "heocr": heocr.__version__,
        "tesseract": tesseract_version(),
        "platform": sys.platform,
        "suffixes": list(engine.SUPPORTED_SUFFIXES),
        "models": bundled_models(),
    }
    html = (UI / "index.html").read_text("utf-8")
    html = html.replace("/*STYLE*/", (UI / "app.css").read_text("utf-8"))
    html = html.replace("/*SCRIPT*/", (UI / "app.js").read_text("utf-8"))
    return html.replace("/*BOOT*/", "window.HEOCR_BOOT = " + json.dumps(boot, ensure_ascii=False) + ";")


class Api:
    """Methods the page calls (``window.pywebview.api.*``). Private state only: pywebview
    exposes every public attribute to the page."""

    def __init__(self) -> None:
        self._window = None
        self._result: engine.Result | None = None
        self._source: Path | None = None
        self._cancel = threading.Event()
        self._busy = threading.Lock()
        self._last_push = 0.0

    # -- page -> app -------------------------------------------------------------------

    def set_language(self, language: str) -> None:
        i18n.save_language(language)

    def open_file(self) -> None:
        import webview

        patterns = ";".join(f"*.{s}" for s in engine.SUPPORTED_SUFFIXES)
        chosen = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=False,
            file_types=(f"Documents ({patterns})", "All files (*.*)"),
        )
        if chosen:
            self.start(chosen[0] if isinstance(chosen, (list, tuple)) else chosen)

    def start(self, path: str) -> bool:
        if not path or not self._busy.acquire(blocking=False):
            return False
        self._cancel.clear()
        self._source = Path(path)
        self._result = None
        self._push("heocr.started", {"name": self._source.name})
        threading.Thread(target=self._run, args=(self._source,), daemon=True).start()
        return True

    def cancel(self) -> None:
        self._cancel.set()

    def result(self) -> dict:
        r = self._result
        if r is None or r.doc is None:
            return {}
        doc = r.doc
        return {
            "kind": r.kind,
            "format": r.format,
            "pages": doc.page_count if doc.page_count is not None else len(doc.pages),
            "routes": r.routes,
            "sources": r.sources,
            "unread": r.unread,
            "seconds": max(0.1, round(r.seconds, 1)),
            "ocr_blocks": r.sources.get("ocr", 0),
            "ocr_available": r.ocr_available,
            "notes": r.notes,
            "direction": render.document_direction(doc.text),
            "html": render.document_html(doc) if r.kind == "ok" else "",
            "text": doc.text if r.kind == "ok" else "",
            "markdown": doc.markdown if r.kind == "ok" else "",
        }

    def save(self, kind: str) -> str | None:
        import webview

        r = self._result
        if r is None or r.doc is None or kind not in exports.FORMATS:
            return None
        stem = self._source.stem if self._source else "heocr"
        target = self._window.create_file_dialog(
            webview.FileDialog.SAVE,
            save_filename=f"{stem}.{kind}",
            directory=str(self._source.parent) if self._source else "",
        )
        if not target:
            return None
        target = target[0] if isinstance(target, (list, tuple)) else target
        Path(target).write_bytes(exports.export(r.doc, kind))
        return Path(target).name

    def third_party(self) -> str:
        path = Path(__file__).resolve().parent / "resources" / "THIRD_PARTY_LICENSES.md"
        try:
            return path.read_text("utf-8")
        except OSError:
            return ""

    # -- app -> page -------------------------------------------------------------------

    def _push(self, function: str, payload: dict) -> None:
        if self._window is not None:
            self._window.evaluate_js(f"{function}({json.dumps(payload, ensure_ascii=False)})")

    def _progress(self, progress: engine.Progress) -> None:
        now = time.monotonic()
        if progress.stage == "pages" and now - self._last_push < 0.15:
            return  # at most a few updates a second
        self._last_push = now
        self._push("heocr.progress", {"stage": progress.stage, "done": progress.done, "total": progress.total})

    def _run(self, path: Path) -> None:
        try:
            self._result = engine.convert(path, report=self._progress, cancel=self._cancel)
            self._push("heocr.finished", {"kind": self._result.kind})
        except engine.Cancelled:
            self._push("heocr.finished", {"kind": "cancelled"})
        except Exception:  # noqa: BLE001 - shown to the user, never crashes the window
            traceback.print_exc()
            self._push("heocr.finished", {"kind": "error"})
        finally:
            self._busy.release()


def _bind_drop(window, api: Api) -> None:
    from webview.dom import DOMEventHandler

    def on_drop(event) -> None:
        files = (event.get("dataTransfer") or {}).get("files") or []
        for item in files:
            path = item.get("pywebviewFullPath")
            if path:
                api.start(path)
                return
        window.evaluate_js("heocr.dropFailed()")

    def ignore(_event) -> None:
        return None

    document = window.dom.document
    document.events.dragenter += DOMEventHandler(ignore, True, True)
    document.events.dragover += DOMEventHandler(ignore, True, True)
    document.events.drop += DOMEventHandler(on_drop, True, True)
    # A file named on the command line (Windows "Open with", release screenshots) opens at once.
    first = next((a for a in sys.argv[1:] if not a.startswith("-") and Path(a).is_file()), None)
    if first:
        api.start(first)


def main() -> None:
    engine.install_offline_guard()
    engine.hide_child_consoles()

    smoke = os.environ.get("HEOCR_DESKTOP_SMOKE")
    if smoke:
        from heocr_desktop.smoke import run

        sys.exit(run(smoke))

    import webview

    language = i18n.load_language()
    api = Api()
    window = webview.create_window(
        APP_NAME,
        html=page_html(language),
        js_api=api,
        width=1100,
        height=780,
        min_size=(640, 480),
        text_select=True,
        background_color="#F7F7F5",
    )
    api._window = window
    webview.start(_bind_drop, (window, api), private_mode=True, http_server=False)


if __name__ == "__main__":
    main()
