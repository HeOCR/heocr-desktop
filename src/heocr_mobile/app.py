"""HeOCR for Android: open, share or photograph a document and get its Hebrew text out.

The reading is the desktop's: the same ``heocr_desktop.engine`` around heocr, with the bundled
Tesseract and models. Documents come from the system picker, from another app's share sheet
("Share" → HeOCR), from "Open with", or from the camera (docs/mobile-design.md, section 5).
"""

from __future__ import annotations

import asyncio
import functools
import traceback
from pathlib import Path

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from heocr_desktop import diagnostics, engine, exports, i18n
from heocr_mobile import __version__, device, view

# Mobile-only strings, in the desktop's format. New ones go to the maintainer for a native read.
# Hebrew reviewed by the maintainer on 2026-11-19: all five strings below.
MOBILE_STRINGS = {
    "en": {
        "open": "Open a file",
        "take_photo": "Take a photo",
        "sample": "Try a sample",
        "offline": "Works fully offline: nothing you read leaves this phone.",
        "welcome": "Open a PDF, a Word file (DOCX) or an image, share one to HeOCR from another app, or take a photo.",
        "diagnostics": "Copy diagnostics",
        "diagnostics_copied": "Diagnostics copied: how the last file was read, without its text.",
        "incomplete": "The file arrived incomplete from the app that shared it. Try again, or open it with \u201cOpen a file\u201d.",
    },
    "he": {
        "open": "פתיחת קובץ",
        "take_photo": "צילום",
        "sample": "דוגמה",
        "offline": "עובד במלואו בלי אינטרנט: שום דבר שנקרא לא יוצא מהטלפון.",
        "welcome": "פתחו קובץ PDF, קובץ וורד (DOCX) או תמונה, שתפו קובץ ל־HeOCR מאפליקציה אחרת, או צלמו.",
        "diagnostics": "העתקת פרטי אבחון",
        "diagnostics_copied": "פרטי האבחון הועתקו: איך נקרא הקובץ האחרון, בלי הטקסט שלו.",
        "incomplete": "הקובץ הגיע חלקי מהאפליקציה ששיתפה אותו. נסו שוב, או פתחו אותו ב„פתיחת קובץ”.",
    },
}


def guarded(handler):
    """A button's handler that cannot fail silently: Toga drops exceptions from async handlers, so
    log the error's type and where it happened (never document text), and show the error message."""

    @functools.wraps(handler)
    async def run(self, *args, **kwargs):
        try:
            return await handler(self, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            where = traceback.extract_tb(exc.__traceback__)[-1]
            print(f"HeOCR {handler.__name__}: error {type(exc).__name__} at {Path(where.filename).name}:{where.lineno}", flush=True)
            self.message("error")

    return run


def _button(label, handler):
    return toga.Button(label, on_press=handler, style=Pack(flex=1, margin=4))


class HeOCR(toga.App):
    def startup(self):
        device.prepare()
        self.lang = device.language()
        self.t = {**i18n.STRINGS[self.lang], **MOBILE_STRINGS[self.lang]}
        self.text = ""
        self.doc = None
        self.name = "heocr"
        self.busy = False
        self.last = None  # (engine result, input bytes, declared bytes) of the last reading, for diagnostics
        self.status = toga.Label("", style=Pack(margin=(4, 8)))
        self.webview = toga.WebView(style=Pack(flex=1))
        rows = [
            toga.Box(children=[_button(self.t["open"], self.open_file), _button(self.t["take_photo"], self.take_photo)], style=Pack(direction=ROW)),
            # Save: Word first when heocr can write it, then text (exports.formats()).
            toga.Box(
                children=[_button(self.t[f"save_{kind}"], self.saver(kind)) for kind in exports.formats() if kind in ("docx", "txt")],
                style=Pack(direction=ROW),
            ),
            toga.Box(children=[_button(self.t["copy"], self.copy), _button(self.t["sample"], self.read_sample)], style=Pack(direction=ROW)),
        ]
        self.main_window = toga.MainWindow(title=self.formal_name, on_gain_focus=self.on_focus)
        self.main_window.content = toga.Box(children=[*rows, self.status, self.webview], style=Pack(direction=COLUMN))
        self.webview.set_content("about:blank", view.welcome(self.t, self.lang))
        # In the app's menu (⋮), not on the screen: for a bug report, how the last file was read.
        self.commands.add(toga.Command(self.copy_diagnostics, text=self.t["diagnostics"]))
        self.main_window.show()

    # -- where documents come from ---------------------------------------------------------

    def on_focus(self, window, **kwargs):
        """A document shared to HeOCR, or opened with it: at launch, or while the app was open."""
        activity = self._impl.native
        uri = device.incoming_uri(activity.getIntent())
        if uri is None:
            return
        # Mark it handled, so coming back to the app later does not read it again.
        activity.setIntent(device._jclass("android.content.Intent")())
        asyncio.get_running_loop().create_task(self.read_uri(uri))

    @guarded
    async def open_file(self, widget):
        done = asyncio.get_running_loop().create_future()
        self._impl.start_activity(device.open_document_intent(), on_complete=lambda code, data: done.set_result(data))
        data = await done
        uri = data.getData() if data is not None else None
        if uri is not None:
            await self.read_uri(uri)

    @guarded
    async def take_photo(self, widget):
        if not self.camera.has_permission:
            await self.camera.request_permission()
        photo = await self.camera.take_photo()
        if photo is None:
            return
        path = Path(self.paths.cache) / "photo.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        photo.save(path)
        await self.read(path, "photo.jpg")

    @guarded
    async def read_sample(self, widget):
        await self.read(device.RESOURCES / "sample" / "sample.png", "sample.png")

    @guarded
    async def read_uri(self, uri):
        try:
            name = device.display_name(uri)
            declared = device.declared_size(uri)
            path, copied = device.copy_to(uri, Path(self.paths.cache) / "incoming")
        except Exception as exc:  # noqa: BLE001 - shown to the user; details stay on the phone
            print(f"HeOCR incoming document: error {type(exc).__name__}", flush=True)
            self.message("unreadable")
            return
        # Sizes only, never content: a short copy would read as a broken file.
        print(f"HeOCR incoming {name}: copied={copied} declared={declared}", flush=True)
        if declared is not None and declared > 0 and copied != declared:
            self.message("incomplete")
            return
        await self.read(path, name, copied, declared)

    def message(self, key: str):
        """A longer message goes in the page, where it wraps; the status line keeps short text only."""
        self.text = ""
        self.doc = None
        self.status.text = ""
        self.webview.set_content("about:blank", view.message(self.t, self.lang, self.t.get(key, self.t["error"])))

    # -- reading ---------------------------------------------------------------------------

    async def read(self, path: Path, name: str, copied: int | None = None, declared: int | None = None):
        if self.busy:
            return
        self.busy = True
        loop = asyncio.get_running_loop()
        self.status.text = self.t["reading"]

        def report(progress):
            if progress.stage == "pages" and progress.total:
                message = self.t["page_of"].format(done=progress.done + 1, total=progress.total)
            else:
                message = self.t.get(progress.stage, self.t["reading"])
            loop.call_soon_threadsafe(setattr, self.status, "text", message)

        try:
            result = await loop.run_in_executor(None, engine.convert, path, report)
        except Exception as exc:  # noqa: BLE001 - shown to the user; details stay on the phone
            print(f"HeOCR read {name}: error {type(exc).__name__}", flush=True)
            self.message("error")
            return
        finally:
            self.busy = False
        self.last = (result, copied if copied is not None else path.stat().st_size, declared)
        # One line in the device log per reading (the file's name, never its text), for CI and bug reports.
        models = sorted({str(m) for m in view.ocr_models(result.doc)}) if result.doc is not None else []
        print(f"HeOCR read {name}: {result.kind} routes={result.routes} models={models} seconds={result.seconds:.1f}", flush=True)
        if result.kind != "ok":
            self.message(result.kind)
            return
        self.text = result.doc.text
        self.doc = result.doc
        self.name = Path(name).stem or "heocr"
        notes = [self.t["ocr_note"]] if "ocr" in result.routes or "ocr" in result.sources else []
        self.status.text = f"{name} · " + self.t["seconds"].format(s=round(result.seconds, 1))
        self.webview.set_content("about:blank", view.page(result.doc, self.t, notes))

    def saver(self, kind: str):
        async def handler(widget):
            await self.save(kind)

        return handler

    @guarded
    async def save(self, kind: str):
        """Save the reading where the user chooses: Word (.docx) or text (.txt), the same bytes as the desktop."""
        if self.doc is None:
            return
        done = asyncio.get_running_loop().create_future()
        intent = device.create_document_intent(f"{self.name}.{kind}", exports.MIME[kind])
        self._impl.start_activity(intent, on_complete=lambda code, data: done.set_result(data))
        data = await done
        uri = data.getData() if data is not None else None
        if uri is None:
            return
        try:
            device.write_to(uri, exports.export(self.doc, kind))
        except Exception as exc:  # noqa: BLE001 - shown to the user
            print(f"HeOCR save: error {type(exc).__name__}", flush=True)
            self.message("error")
            return
        self.status.text = self.t["saved"]

    @guarded
    async def copy_diagnostics(self, command, **kwargs):
        """Copy how the last file was read (structure only, no text), for a safe bug report."""
        if self.last is None:
            return
        result, copied, declared = self.last
        report = diagnostics.report(result, app="heocr_mobile", app_version=__version__, input_bytes=copied, declared_bytes=declared)
        device.copy_text(diagnostics.text(report))
        self.status.text = ""
        self.webview.set_content("about:blank", view.message(self.t, self.lang, self.t["diagnostics_copied"]))

    @guarded
    async def copy(self, widget):
        if self.text:
            device.copy_text(self.text)
            self.status.text = self.t["copied"]


def main():
    return HeOCR("HeOCR", "io.github.heocr.heocr_mobile")
