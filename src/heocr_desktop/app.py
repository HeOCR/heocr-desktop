"""The HeOCR window: one page, a drop zone and an open button, the text with its structure, and save.

The interface is an inline HTML page in the system's web view (pywebview: WebKit on macOS, WebView2 on
Windows). Files dropped on the window arrive as paths through pywebview's DOM events; the conversion runs
on a background thread, and the page polls its state.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
from importlib import resources
from pathlib import Path

from . import __version__, core, i18n, offline, render


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.state = "idle"       # idle | busy | done | error
        self.name = ""
        self.source: Path | None = None
        self.progress: core.Progress | None = None
        self.result: core.Result | None = None
        self.error = ""


class Api:
    """What the page may call (window.pywebview.api). Private attributes are not exposed."""

    def __init__(self, info: dict, lang: str):
        self._info = info
        self._lang = lang
        self._state = State()
        self._window = None

    # -- set-up --------------------------------------------------------------------------------
    def set_lang(self, lang: str) -> bool:
        if lang in i18n.STRINGS:
            self._lang = lang
        return True

    # -- reading -------------------------------------------------------------------------------
    def open_dialog(self) -> bool:
        import webview
        types = ("Documents (" + ";".join(f"*.{t}" for t in core.OPEN_TYPES) + ")", "All files (*.*)")
        picked = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=False, file_types=types)
        if not picked:
            return False
        path = picked[0] if isinstance(picked, (list, tuple)) else picked
        return self.start(str(path))

    def start(self, path: str) -> bool:
        st = self._state
        with st.lock:
            if st.state == "busy":
                return False
            p = Path(path)
            st.state, st.name, st.source, st.result, st.error = "busy", p.name, p, None, ""
            st.progress = core.Progress(core.page_count(p))
        threading.Thread(target=self._run, args=(p,), daemon=True).start()
        return True

    def _run(self, path: Path) -> None:
        st = self._state
        try:
            result = core.convert(path, st.progress)
            with st.lock:
                st.result, st.state = result, "done"
        except Exception as e:  # noqa: BLE001 - shown to the user, never silent
            with st.lock:
                st.error, st.state = f"{type(e).__name__}: {e}", "error"

    def status(self) -> dict:
        st = self._state
        with st.lock:
            out = {"state": st.state, "name": st.name}
            if st.state == "busy" and st.progress:
                out.update(fraction=st.progress.fraction(), done=st.progress.done, total=st.progress.total)
            elif st.state == "done" and st.result:
                r = st.result
                page = i18n.STRINGS[self._lang]["page"]
                out["result"] = {"name": st.name, "text": r.text, "html": render.to_html(r.markdown, page),
                                 "routes": r.routes, "unread": r.unread, "flags": r.flags, "pages": r.pages}
                st.state = "shown"
            elif st.state == "error":
                out["error"] = st.error
                st.state = "idle"
            return out

    # -- output ----------------------------------------------------------------------------------
    def save(self, kind: str) -> bool:
        import webview
        st = self._state
        if not st.result or kind not in ("txt", "md", "json"):
            return False
        body = {"txt": st.result.text, "md": st.result.markdown, "json": st.result.json()}[kind]
        stem = st.source.stem if st.source else "heocr"
        picked = self._window.create_file_dialog(webview.FileDialog.SAVE, save_filename=f"{stem}.{kind}")
        if not picked:
            return False
        path = picked[0] if isinstance(picked, (list, tuple)) else picked
        Path(path).write_text(body, encoding="utf-8", newline="\n")
        return True

    def copy(self, text: str) -> bool:
        """Clipboard fallback when the web view refuses: the system's own tools."""
        try:
            if sys.platform == "darwin":
                subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True, timeout=10)
            elif sys.platform == "win32":
                subprocess.run(["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                               input=text.encode("utf-8"), check=True, timeout=20)
            else:
                return False
            return True
        except (OSError, subprocess.SubprocessError):
            return False

    def about(self) -> dict:
        info = self._info
        versions = (f"HeOCR {__version__} · heocr {info['heocr']} · Tesseract: {info['tesseract']}"
                    f" · models: {', '.join(info['models']) or 'none'}"
                    f" · LibreOffice: {'found' if info['libreoffice'] else 'not installed'}")
        return {"versions": versions, "licences": third_party()}


def third_party() -> str:
    try:
        return resources.files("heocr_desktop").joinpath("THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return "THIRD_PARTY_LICENSES.md"


def page_html(lang: str) -> str:
    template = resources.files("heocr_desktop").joinpath("ui.html").read_text(encoding="utf-8")
    boot = json.dumps({"lang": lang, "strings": i18n.STRINGS}, ensure_ascii=False)
    return template.replace("/*BOOT*/null", boot.replace("</", "<\\/"))


def main() -> None:
    offline.enforce()
    import webview
    from webview.dom import DOMEventHandler

    info = core.configure()
    lang = i18n.system_language()
    api = Api(info, lang)
    window = webview.create_window("HeOCR", html=page_html(lang), js_api=api, width=1040, height=760,
                                   min_size=(640, 480))
    api._window = window

    def on_drop(event):
        files = (event.get("dataTransfer") or {}).get("files") or []
        for f in files:
            path = f.get("pywebviewFullPath")
            if path and api.start(path):
                window.evaluate_js("window.heocrStarted && window.heocrStarted()")
                return

    def on_loaded():
        window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)
        window.dom.document.events.dragover += DOMEventHandler(lambda e: None, True, True)

    window.events.loaded += on_loaded
    webview.start(private_mode=True)


if __name__ == "__main__":
    main()
