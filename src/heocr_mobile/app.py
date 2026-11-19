"""HeOCR for Android, M0: take a photo (or read the invented sample page) and get its Hebrew text.

The reading is the desktop's: the same ``heocr_desktop.engine`` around heocr, the same bundled
Tesseract version and models. Opening files and the share sheet come in M1
(docs/mobile-design.md, section 8).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from heocr_desktop import engine, i18n
from heocr_mobile import device, view

# Mobile-only strings, in the desktop's format. New ones go to the maintainer for a native read.
MOBILE_STRINGS = {
    "en": {"take_photo": "Take a photo", "sample": "Try a sample"},
    "he": {"take_photo": "צילום", "sample": "דוגמה"},
}


class HeOCR(toga.App):
    def startup(self):
        device.prepare()
        self.lang = device.language()
        self.t = {**i18n.STRINGS[self.lang], **MOBILE_STRINGS[self.lang]}
        self.text = ""
        self.status = toga.Label(self.t["offline"], style=Pack(margin=8))
        self.webview = toga.WebView(style=Pack(flex=1))
        buttons = toga.Box(
            children=[
                toga.Button(self.t["take_photo"], on_press=self.take_photo, style=Pack(flex=1, margin=4)),
                toga.Button(self.t["sample"], on_press=self.read_sample, style=Pack(flex=1, margin=4)),
                toga.Button(self.t["copy"], on_press=self.copy, style=Pack(flex=1, margin=4)),
            ],
            style=Pack(direction=ROW),
        )
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = toga.Box(children=[buttons, self.status, self.webview], style=Pack(direction=COLUMN))
        self.main_window.show()

    async def take_photo(self, widget):
        if not self.camera.has_permission:
            await self.camera.request_permission()
        photo = await self.camera.take_photo()
        if photo is None:
            return
        path = Path(self.paths.cache) / "photo.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        photo.save(path)
        await self.read(path)

    async def read_sample(self, widget):
        await self.read(device.RESOURCES / "sample" / "sample.png")

    async def read(self, path: Path):
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
        except Exception:  # noqa: BLE001 - shown to the user; details stay on the phone
            self.status.text = self.t["error"]
            return
        if result.kind != "ok":
            self.text = ""
            self.status.text = self.t.get(result.kind, self.t["error"])
            self.webview.set_content("about:blank", "")
            return
        self.text = result.doc.text
        notes = [self.t["ocr_note"]] if "ocr" in result.routes or "ocr" in result.sources else []
        self.status.text = self.t["seconds"].format(s=round(result.seconds, 1))
        self.webview.set_content("about:blank", view.page(result.doc, self.t, notes))

    async def copy(self, widget):
        if self.text:
            device.copy_text(self.text)
            self.status.text = self.t["copied"]


def main():
    return HeOCR("HeOCR", "io.github.heocr.heocr_mobile")
