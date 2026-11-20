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
from uuid import uuid4

from heocr_desktop import engine, exports, i18n, licences, menus, render, reveal

UI = Path(__file__).resolve().parent / "ui"
APP_NAME = "HeOCR"
PROJECT_LINKS = {
    "website": "https://heocr.org",
    "github": "https://github.com/HeOCR/heocr-desktop",
}


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
    """List the licensed models present in the installed heocr and app resources."""
    from heocr.models import MODELS, bundled_dir

    directory = bundled_dir()
    models = [
        {"name": model.name, "origin": "", "licence": model.licence}
        for model in MODELS.values()
        if model.bundled and (directory / f"{model.name}.traineddata").is_file()
    ]
    try:
        info = json.loads((engine.RESOURCES / "BUILD_INFO.json").read_text("utf-8"))
        files = info["tessdata"]["files"]
    except (OSError, ValueError, KeyError):
        return models
    models.extend(
        {"name": Path(name).stem, "origin": pin.get("origin", ""), "licence": "Apache-2.0"}
        for name, pin in sorted(files.items())
    )
    return models


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
    html = html.replace("/*APP_STYLE*/", (UI / "runtime.css").read_text("utf-8"))
    html = html.replace("/*SCRIPT*/", (UI / "app.js").read_text("utf-8"))
    return html.replace("/*BOOT*/", "window.HEOCR_BOOT = " + json.dumps(boot, ensure_ascii=False) + ";")


class Api:
    """Methods the page calls (``window.pywebview.api.*``). Private state only: pywebview
    exposes every public attribute to the page."""

    def __init__(self) -> None:
        self._window = None
        self._result: engine.Result | None = None
        self._source: Path | None = None
        self._saved: tuple[str, Path] | None = None
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
        self._saved = None
        self._result = None
        self._push("heocr.started", {"name": self._source.name})
        threading.Thread(target=self._run, args=(self._source,), daemon=True).start()
        return True

    def cancel(self) -> None:
        self._cancel.set()

    def retry(self) -> bool:
        return self.start(str(self._source)) if self._source is not None else False

    def result(self) -> dict:
        r = self._result
        if r is None or r.doc is None:
            return {}
        doc = r.doc
        picture_page = None
        if len(doc.unread) == 1:
            part = doc.unread[0]
            if part.reason == "image_region_ocr_low_confidence" and part.page is not None:
                picture_page = part.page + 1
        return {
            "kind": r.kind,
            "format": r.format,
            "pages": doc.page_count if doc.page_count is not None else len(doc.pages),
            "routes": r.routes,
            "sources": r.sources,
            "unread": r.unread,
            "unread_picture_page": picture_page,
            "seconds": max(0.1, round(r.seconds, 1)),
            "ocr_blocks": r.sources.get("ocr", 0),
            "ocr_available": r.ocr_available,
            "notes": r.notes,
            "direction": render.document_direction(doc.text),
            "html": render.document_html(doc) if r.kind == "ok" else "",
            "text": doc.text if r.kind == "ok" else "",
            "markdown": doc.markdown if r.kind == "ok" else "",
            "formats": list(exports.formats()),
        }

    def save(self, kind: str) -> dict | None:
        import webview

        r = self._result
        if r is None or r.doc is None or kind not in exports.formats():
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
        target = Path(target)
        target.write_bytes(exports.export(r.doc, kind))
        path = reveal.local_file(target)
        token = None
        if self._result is r:
            self._saved = None
            if path is not None:
                token = uuid4().hex
                self._saved = (token, path)
        return {"name": target.name, "reveal": token}

    def reveal_saved(self, token: str) -> bool:
        saved = self._saved
        return bool(saved and saved[0] == token and reveal.show(saved[1]))

    def open_project_link(self, link: str) -> bool:
        """Send a known project URL to the system's browser."""
        if not isinstance(link, str) or link not in PROJECT_LINKS:
            return False
        url = PROJECT_LINKS[link]
        try:
            if sys.platform == "darwin":
                return subprocess.run(["/usr/bin/open", url], check=False, timeout=5).returncode == 0
            if sys.platform == "win32":
                os.startfile(url)
                return True
        except (OSError, subprocess.SubprocessError):
            pass
        return False

    def third_party(self) -> str:
        return licences.about_text(engine.RESOURCES)

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
            result = engine.convert(path, report=self._progress, cancel=self._cancel)
            if self._cancel.is_set():
                # Unpaginated formats may complete without reaching a cancel checkpoint.
                raise engine.Cancelled()
            self._result = result
            self._push("heocr.finished", {"kind": result.kind})
        except engine.Cancelled as stopped:
            self._push("heocr.finished", {"kind": "cancelled", "done": stopped.done, "total": stopped.total})
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
        if files:
            window.evaluate_js("heocr.dropFailed()")

    window.dom.document.events.drop += DOMEventHandler(on_drop, prevent_default=True)
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
        min_size=(720, 520),
        text_select=True,
        background_color="#F7F7F5",
    )
    api._window = window

    def menu_action(action: str) -> None:
        window.evaluate_js(f"heocr.action({json.dumps(action)})")

    webview.settings["SHOW_DEFAULT_MENUS"] = False
    menu = menus.build(language, menu_action, window.destroy, sys.platform)
    webview.start(_bind_drop, (window, api), private_mode=True, http_server=False, menu=menu)


if __name__ == "__main__":
    main()
