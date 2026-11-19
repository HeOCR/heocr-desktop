"""HeOCR for Android: open, share or photograph a document and get its Hebrew text out.

The reading is the desktop's: the same ``heocr_desktop.engine`` around heocr, with the bundled
Tesseract and models. Documents come from the system picker, from another app's share sheet
("Share" → HeOCR), from "Open with", or from the camera (docs/mobile-design.md, section 5).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from heocr_desktop import engine, exports, i18n
from heocr_mobile import device, view

# Mobile-only strings, in the desktop's format. New ones go to the maintainer for a native read.
# Hebrew reviewed by the maintainer on 2026-11-19: all five strings below.
MOBILE_STRINGS = {
    "en": {
        "open": "Open a file",
        "take_photo": "Take a photo",
        "sample": "Try a sample",
        "offline": "Works fully offline: nothing you read leaves this phone.",
        "welcome": "Open a PDF, a Word file (DOCX) or an image, share one to HeOCR from another app, or take a photo.",
    },
    "he": {
        "open": "פתיחת קובץ",
        "take_photo": "צילום",
        "sample": "דוגמה",
        "offline": "עובד במלואו בלי אינטרנט: שום דבר שנקרא לא יוצא מהטלפון.",
        "welcome": "פתחו קובץ PDF, קובץ וורד (DOCX) או תמונה, שתפו קובץ ל־HeOCR מאפליקציה אחרת, או צלמו.",
    },
}


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
        self.status = toga.Label("", style=Pack(margin=(4, 8)))
        self.webview = toga.WebView(style=Pack(flex=1))
        rows = [
            toga.Box(children=[_button(self.t["open"], self.open_file), _button(self.t["take_photo"], self.take_photo)], style=Pack(direction=ROW)),
            toga.Box(children=[_button(self.t["copy"], self.copy), _button(self.t["save_txt"], self.save_txt)], style=Pack(direction=ROW)),
            toga.Box(children=[_button(self.t["sample"], self.read_sample)], style=Pack(direction=ROW)),
        ]
        self.main_window = toga.MainWindow(title=self.formal_name, on_gain_focus=self.on_focus)
        self.main_window.content = toga.Box(children=[*rows, self.status, self.webview], style=Pack(direction=COLUMN))
        self.webview.set_content("about:blank", view.welcome(self.t, self.lang))
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

    async def open_file(self, widget):
        done = asyncio.get_running_loop().create_future()
        self._impl.start_activity(device.open_document_intent(), on_complete=lambda code, data: done.set_result(data))
        data = await done
        uri = data.getData() if data is not None else None
        if uri is not None:
            await self.read_uri(uri)

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

    async def read_sample(self, widget):
        await self.read(device.RESOURCES / "sample" / "sample.png", "sample.png")

    async def read_uri(self, uri):
        try:
            name = device.display_name(uri)
            path = device.copy_to(uri, Path(self.paths.cache) / "incoming")
        except Exception as exc:  # noqa: BLE001 - shown to the user; details stay on the phone
            print(f"HeOCR incoming document: error {type(exc).__name__}", flush=True)
            self.message("unreadable")
            return
        await self.read(path, name)

    def message(self, key: str):
        """A longer message goes in the page, where it wraps; the status line keeps short text only."""
        self.text = ""
        self.doc = None
        self.status.text = ""
        self.webview.set_content("about:blank", view.message(self.t, self.lang, self.t.get(key, self.t["error"])))

    # -- reading ---------------------------------------------------------------------------

    async def read(self, path: Path, name: str):
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

    async def save_txt(self, widget):
        """Save the text as a .txt file where the user chooses (UTF-8 with a BOM, as on the desktop)."""
        if self.doc is None:
            return
        done = asyncio.get_running_loop().create_future()
        intent = device.create_document_intent(f"{self.name}.txt", exports.MIME["txt"])
        self._impl.start_activity(intent, on_complete=lambda code, data: done.set_result(data))
        data = await done
        uri = data.getData() if data is not None else None
        if uri is None:
            return
        try:
            device.write_to(uri, exports.export(self.doc, "txt"))
        except Exception as exc:  # noqa: BLE001 - shown to the user
            print(f"HeOCR save: error {type(exc).__name__}", flush=True)
            self.message("error")
            return
        self.status.text = self.t["saved"]

    async def copy(self, widget):
        if self.text:
            device.copy_text(self.text)
            self.status.text = self.t["copied"]


def main():
    return HeOCR("HeOCR", "io.github.heocr.heocr_mobile")
