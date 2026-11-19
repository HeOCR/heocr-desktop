"""HeOCR for Android: open, share or photograph a document and get its Hebrew text out.

The reading is the desktop's: the same ``heocr_desktop.engine`` around heocr, with the bundled
Tesseract and models. Documents come from the system picker, from another app's share sheet
("Share" → HeOCR), from "Open with", or from the camera (docs/mobile-design.md, section 5).

The whole screen is one WebView page (design/android/SPEC.md, approach B; ``heocr_mobile.screens``).
Every control is a link with an app address; ``navigate`` cancels the navigation and runs the action.
"""

from __future__ import annotations

import asyncio
import functools
import json
import time
import traceback
from html import escape
from pathlib import Path

import toga
from toga.style import Pack

from heocr_desktop import diagnostics, engine, exports, i18n
from heocr_mobile import __version__, back, device, screens, view

# heocr:<action> -> the HeOCR method that runs it (design/android/SPEC.md, section 9).
ACTIONS = {
    "photo": "take_photo", "open": "open_file", "sample": "read_sample", "cancel": "cancel",
    "home": "go_home", "back": "on_back", "about": "show_about", "save-docx": "save_docx", "save-txt": "save_txt",
    "copy": "copy", "diagnostics": "copy_diagnostics", "licences": "show_licences",
    "more": "open_sheet", "dismiss": "close_sheet", "next": "next_step",
}
TOAST_SECONDS = 4


def guarded(handler):
    """An action that cannot fail silently: Toga drops exceptions from async handlers, so log the
    error's type and where it happened (never document text), and show the problem screen."""

    @functools.wraps(handler)
    async def run(self, *args, **kwargs):
        try:
            return await handler(self, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            where = traceback.extract_tb(exc.__traceback__)[-1]
            self.last_error = f"{handler.__name__}:{type(exc).__name__}"
            print(f"HeOCR {handler.__name__}: error {type(exc).__name__} at {Path(where.filename).name}:{where.lineno}", flush=True)
            self.problem("error")

    return run


class HeOCR(toga.App):
    def startup(self):
        device.prepare()
        self.lang = device.language()
        self.t = screens.strings(self.lang)  # the design's approved strings
        self.d = i18n.STRINGS[self.lang]  # the desktop's: counts, times, document labels
        self.doc = None
        self.name = "heocr"
        self.source = None  # (path, name, photo) of the last reading, for "next" on a problem screen
        self.problem_kind = ""
        self.reading = None  # a token for the reading in progress; Cancel drops it
        self.last = None  # (engine result, input bytes, declared bytes) of the last reading, for diagnostics
        self.last_error = None
        self.screen = "home"
        self.before_about = "home"
        self.sheet = False
        self.result_page = ""
        self.toast_id = 0
        self.webview = toga.WebView(style=Pack(flex=1), on_navigation_starting=self.navigate)
        self.main_window = toga.MainWindow(title=self.formal_name, on_gain_focus=self.on_focus)
        self.main_window.content = self.webview
        back.handler = self.on_back
        activity = self._impl.native
        # Before the first page: the WebView's scale and text size (SPEC 3.7).
        zoom = device.configure_webview(self.webview._impl.native, activity)
        self.go_home_now()
        self.main_window.show()
        # The design draws its own app bar (SPEC 6.1): hide the Material one, colour the system bars.
        bar = activity.getSupportActionBar()
        if bar is not None:
            bar.hide()
        device.style_system_bars(activity)
        print(f"HeOCR screen: night={device.night(activity)} text_zoom={zoom}", flush=True)

    # -- the page and its links --------------------------------------------------------------

    def show(self, page: str, screen: str):
        self.screen = screen
        self.sheet = False
        self.webview.set_content("about:blank", page)
        print(f"HeOCR screen {screen}", flush=True)

    def js(self, code: str):
        """Change the page in place (a toast, the sheet, the elapsed time): the page itself has no script."""
        self.webview.evaluate_javascript(code)

    def navigate(self, widget, url: str, **kwargs) -> bool:
        """Every tap on a link: run the app action, open a website in the browser, never navigate."""
        url = str(url)
        if url.startswith("heocr:"):
            action = url[len("heocr:"):].split("?")[0]
            name = ACTIONS.get(action)
            print(f"HeOCR action {action}", flush=True)
            if name is not None:
                result = getattr(self, name)()
                if asyncio.iscoroutine(result):
                    asyncio.get_running_loop().create_task(result)
        elif url.startswith("https://"):
            device.open_in_browser(self._impl.native, url)
        return False

    def on_back(self) -> bool:
        """System Back (SPEC 3.5): sheet → close; reading → cancel; any other screen → Home; Home → leave.
        About opened from a result goes back to that result rather than losing it."""
        if self.sheet:
            self.close_sheet()
        elif self.screen == "reading":
            self.cancel()
        elif self.screen == "licences":
            self.show_about()
        elif self.screen == "about" and self.before_about == "result" and self.result_page:
            self.show(self.result_page, "result")
        elif self.screen != "home":
            self.go_home()
        else:
            return False
        return True

    def toast(self, text: str, sub: str = ""):
        """A confirmation over the page (SPEC 8.10), gone after four seconds. ``text`` and ``sub`` are markup."""
        self.toast_id += 1
        mine = self.toast_id
        markup = screens.toast(text, sub, low=self.screen != "result")
        self.js("(function(){var o=document.getElementById('toast');if(o)o.remove();"
                f"document.body.insertAdjacentHTML('beforeend',{json.dumps(markup)});}})()")

        async def leave():
            await asyncio.sleep(TOAST_SECONDS)
            if self.toast_id == mine:
                self.js("(function(){var o=document.getElementById('toast');if(o)o.remove();})()")

        asyncio.get_running_loop().create_task(leave())

    # -- screens -------------------------------------------------------------------------------

    def go_home_now(self):
        self.show(screens.home(self.t, self.lang, "docx" in exports.formats()), "home")

    def go_home(self):
        self.reading = None
        self.go_home_now()

    def show_about(self):
        if self.screen in ("home", "result"):
            self.before_about = self.screen
        back_to = "back" if self.before_about == "result" else "home"
        self.show(screens.about(self.t, self.lang, self.versions(), back=back_to), "about")

    def show_licences(self):
        text = (device.RESOURCES / "THIRD_PARTY_LICENSES.md").read_text("utf-8")
        self.show(screens.licences(self.t, self.lang, text), "licences")

    def open_sheet(self):
        self.sheet = True
        self.js("document.getElementById('more').classList.add('open')")

    def close_sheet(self):
        if self.sheet:
            self.sheet = False
            self.js("document.getElementById('more').classList.remove('open')")

    def problem(self, kind: str, body: str | None = None):
        self.reading = None
        self.problem_kind = kind
        photo = bool(self.source and self.source[2])
        self.show(screens.problem(self.t, self.d, self.lang, kind, photo=photo, body=body), "problem")

    def next_step(self):
        """The primary button of a problem screen: take the photo again, or choose another file."""
        if self.problem_kind == "empty" and self.source and self.source[2]:
            return self.take_photo()
        return self.open_file()

    def versions(self) -> dict[str, str]:
        import heocr

        tesseract = "unknown"
        try:
            info = json.loads((device.RESOURCES / "BUILD_INFO.json").read_text("utf-8"))
            tesseract = str(info["tesseract_builds"][0].get("tesseract", "unknown"))
        except (OSError, ValueError, KeyError, IndexError):
            pass
        return {"app": __version__, "heocr": getattr(heocr, "__version__", "unknown"), "tesseract": tesseract}

    # -- where documents come from ---------------------------------------------------------

    def on_focus(self, window, **kwargs):
        """A document shared to HeOCR, or opened with it: at launch, or while the app was open."""
        activity = self._impl.native
        uri = device.incoming_uri(activity.getIntent())
        if uri is None:
            return
        # Mark it handled, so coming back to the app later does not read it again.
        activity.setIntent(device._jclass("android.content.Intent")())
        asyncio.get_running_loop().create_task(self.read_uri(uri, shared=True))

    @guarded
    async def open_file(self):
        done = asyncio.get_running_loop().create_future()
        self._impl.start_activity(device.open_document_intent(), on_complete=lambda code, data: done.set_result(data))
        data = await done
        uri = data.getData() if data is not None else None
        if uri is not None:
            await self.read_uri(uri)

    @guarded
    async def take_photo(self):
        if not self.camera.has_permission:
            await self.camera.request_permission()
        photo = await self.camera.take_photo()
        if photo is None:
            return
        path = Path(self.paths.cache) / "photo.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        photo.save(path)
        await self.read(path, "photo.jpg", photo=True)

    @guarded
    async def read_sample(self):
        await self.read(device.RESOURCES / "sample" / "sample.png", "sample.png")

    @guarded
    async def read_uri(self, uri, shared: bool = False):
        try:
            name = device.display_name(uri)
            declared = device.declared_size(uri)
            path, copied = device.copy_to(uri, Path(self.paths.cache) / "incoming")
        except Exception as exc:  # noqa: BLE001 - shown to the user; details stay on the phone
            self.last_error = f"incoming:{type(exc).__name__}"
            print(f"HeOCR incoming document: error {type(exc).__name__}", flush=True)
            self.problem("unreadable")
            return
        # Sizes only, never content: a short copy would read as a broken file.
        print(f"HeOCR incoming {name}: copied={copied} declared={declared}", flush=True)
        if declared is not None and declared > 0 and copied != declared:
            self.last_error = "incoming:incomplete"
            self.problem("unreadable")
            return
        await self.read(path, name, copied, declared, shared=shared)

    # -- reading ---------------------------------------------------------------------------

    def cancel(self):
        """Stop waiting for the reading and go Home. heocr finishes in the background; its result is dropped."""
        if self.reading is not None:
            print("HeOCR read: cancelled", flush=True)
        self.go_home()

    async def read(self, path: Path, name: str, copied: int | None = None, declared: int | None = None,
                   shared: bool = False, photo: bool = False):
        if self.reading is not None:
            return
        token = self.reading = object()
        self.source = (path, name, photo)
        self.last_error = None
        loop = asyncio.get_running_loop()
        size = copied if copied is not None else path.stat().st_size
        started = time.monotonic()
        pages = {"done": 0, "total": 0}

        def render():
            # The count and the segments change by a new page at each page boundary (SPEC 3.3).
            if self.reading is token:
                seconds = time.monotonic() - started
                self.show(screens.reading(self.t, self.d, self.lang, name, size, shared, pages["done"], pages["total"], seconds), "reading")

        def report(progress):
            if progress.stage == "pages" and progress.total:
                pages.update(done=progress.done, total=progress.total)
                loop.call_soon_threadsafe(render)

        async def tick():
            # The elapsed time is set from outside, once a second.
            while self.reading is token:
                await asyncio.sleep(1)
                if self.reading is token:
                    value = json.dumps(screens.elapsed_text(time.monotonic() - started))
                    self.js(f"(function(){{var e=document.getElementById('elapsed');if(e)e.textContent={value};}})()")

        render()
        ticker = loop.create_task(tick())
        try:
            result = await loop.run_in_executor(None, engine.convert, path, report)
        except Exception as exc:  # noqa: BLE001 - shown to the user; details stay on the phone
            if self.reading is token:
                self.last_error = f"read:{type(exc).__name__}"
                print(f"HeOCR read {name}: error {type(exc).__name__}", flush=True)
                self.problem("error")
            return
        finally:
            ticker.cancel()
        if self.reading is not token:
            return  # cancelled: the user is already elsewhere
        self.reading = None
        self.last = (result, size, declared)
        # One line in the device log per reading (the file's name, never its text), for CI and bug reports.
        models = sorted({str(m) for m in view.ocr_models(result.doc)}) if result.doc is not None else []
        print(f"HeOCR read {name}: {result.kind} routes={result.routes} models={models} seconds={result.seconds:.1f}", flush=True)
        if result.kind != "ok":
            self.problem(result.kind)
            return
        self.doc = result.doc
        self.name = Path(name).stem or "heocr"
        ocr = "ocr" in result.routes or "ocr" in result.sources
        page_count = sum(result.routes.values()) if result.routes else 0
        self.result_page = screens.result(self.t, self.d, self.lang, result.doc, name, page_count, result.seconds, ocr, exports.formats())
        self.show(self.result_page, "result")

    # -- actions on a result ---------------------------------------------------------------

    def save_docx(self):
        return self.save("docx")

    def save_txt(self):
        return self.save("txt")

    @guarded
    async def save(self, kind: str):
        """Save the reading where the user chooses: Word (.docx) or text (.txt), the same bytes as the desktop."""
        self.close_sheet()
        if self.doc is None or kind not in exports.formats():
            return
        done = asyncio.get_running_loop().create_future()
        file_name = f"{self.name}.{kind}"
        intent = device.create_document_intent(file_name, exports.MIME[kind])
        self._impl.start_activity(intent, on_complete=lambda code, data: done.set_result(data))
        data = await done
        uri = data.getData() if data is not None else None
        if uri is None:
            return
        device.write_to(uri, exports.export(self.doc, kind))
        print(f"HeOCR saved {kind}", flush=True)
        self.toast(escape(self.d["saved"]), f"<bdi>{escape(file_name)}</bdi>")

    def copy(self):
        if self.doc is not None:
            device.copy_text(self.doc.text)
            print("HeOCR copied", flush=True)
            self.toast(self.t["copied"])

    def copy_diagnostics(self):
        """Copy how the last file was read (structure only, no text, no file name), for a bug report."""
        self.close_sheet()
        if self.last is not None:
            result, copied, declared = self.last
            report = diagnostics.report(result, app="heocr_mobile", app_version=__version__, input_bytes=copied, declared_bytes=declared)
        else:
            import heocr

            report = {"app": "heocr_mobile", "app_version": __version__, "heocr": getattr(heocr, "__version__", "unknown")}
        report["tesseract"] = self.versions()["tesseract"]
        report["phone"] = device.phone()
        report["error"] = self.last_error
        device.copy_text(diagnostics.text(report))
        print("HeOCR diagnostics copied", flush=True)
        self.toast(self.t["diag_done"], self.t["diag_done_sub"])


def main():
    return HeOCR("HeOCR", "io.github.heocr.heocr_mobile")
