"""Smoke conversions, one fixture of each type, on invented text only.

The OCR cases need Tesseract with ``heb``: the bundled one when ``resources/`` holds it, else one on the
PATH. ``HEOCR_DESKTOP_REQUIRE_OCR=1`` (set in CI) turns a missing Tesseract into a failure, not a skip.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from heocr_desktop import core, render
from tests.synth.docx import Docx, para, table
from tests.synth.pdf import PdfPage, lines_block, make_pdf

LINES = ["כותרת מומצאת לבדיקה", "שורה ראשונה של טקסט לדוגמה", "סכום של 1,250 שקלים"]
OCR_WORDS = ["שלום", "עולם", "בדיקה"]

FONTS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def hebrew_font(size=64):
    for f in FONTS:
        if Path(f).is_file():
            return ImageFont.truetype(f, size)
    return None


def ocr_ready() -> bool:
    info = core.configure()
    return info["tesseract"] != "none"


def image_with(words, font) -> Image.Image:
    im = Image.new("L", (1700, 400), 255)
    d = ImageDraw.Draw(im)
    # Words are placed right to left by hand. With raqm, Pillow shapes each Hebrew word itself; without
    # it, a word's letters are laid out left to right, so they are drawn reversed.
    from PIL import features
    shaped = features.check("raqm")
    x = 1600
    for w in words:
        glyphs = w if shaped else w[::-1]
        width = d.textlength(glyphs, font=font)
        d.text((x - width, 150), glyphs, fill=0, font=font)
        x -= width + 40
    return im


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, body: bytes) -> Path:
        p = self.d / name
        p.write_bytes(body)
        return p


class BornDigitalTest(Base):
    def test_pdf_text_layer(self):
        path = self.write("invented.pdf", make_pdf([PdfPage(lines=lines_block(LINES))]))
        progress = core.Progress(core.page_count(path))
        r = core.convert(path, progress)
        self.assertEqual(r.format, "pdf")
        for line in LINES:
            self.assertIn(line, r.text)
        self.assertEqual(r.routes, [("text_layer", [1])])
        self.assertEqual(progress.total, 1)
        self.assertEqual(progress.fraction(), 1.0)
        self.assertEqual(r.record["schema"], "heocr_document.v1")
        self.assertIn('"schema"', r.json())

    def test_two_pages_progress(self):
        pages = [PdfPage(lines=lines_block(LINES[:1])), PdfPage(lines=lines_block(LINES[1:]))]
        path = self.write("two.pdf", make_pdf(pages))
        progress = core.Progress(core.page_count(path))
        r = core.convert(path, progress)
        self.assertEqual(progress.total, 2)
        self.assertEqual(progress.done, 2)
        self.assertEqual(r.routes, [("text_layer", [1, 2])])
        self.assertIn('class="page-mark"', render.to_html(r.markdown))


class DocxTest(Base):
    def test_docx_structure(self):
        body = [para("כותרת מסמך מומצא", style="Heading1"), para("פסקה ראשונה במסמך לדוגמה."),
                table([["עמודה א", "עמודה ב"], ["תא אחד", "תא שני"]], borders=True)]
        styles = []
        path = self.write("invented.docx", Docx(body=body, styles=styles).build())
        r = core.convert(path)
        self.assertEqual(r.format, "docx")
        self.assertIn("פסקה ראשונה במסמך לדוגמה.", r.text)
        self.assertIn(("office", None), r.routes)
        html = render.to_html(r.markdown)
        self.assertIn("<table", html)
        self.assertIn("תא שני", html)


@unittest.skipUnless(hebrew_font(), "no font with Hebrew glyphs on this machine")
class OcrTest(Base):
    def setUp(self):
        super().setUp()
        if not ocr_ready():
            if os.environ.get("HEOCR_DESKTOP_REQUIRE_OCR") == "1":
                self.fail("Tesseract is required here, and none was found")
            self.skipTest("no Tesseract on this machine")

    def check(self, r):
        hits = sum(w in r.text for w in OCR_WORDS)
        self.assertGreaterEqual(hits, 2, r.text)
        self.assertEqual([route for route, _ in r.routes], ["ocr"])

    def test_png(self):
        buf = io.BytesIO()
        image_with(OCR_WORDS, hebrew_font()).save(buf, "PNG", dpi=(300, 300))
        self.check(core.convert(self.write("invented.png", buf.getvalue())))

    def test_jpeg_and_tiff(self):
        im = image_with(OCR_WORDS, hebrew_font())
        for fmt, name in (("JPEG", "invented.jpg"), ("TIFF", "invented.tif")):
            with self.subTest(fmt=fmt):
                buf = io.BytesIO()
                im.save(buf, fmt, dpi=(300, 300))
                self.check(core.convert(self.write(name, buf.getvalue())))

    def test_scanned_pdf(self):
        buf = io.BytesIO()
        image_with(OCR_WORDS, hebrew_font()).convert("RGB").save(buf, "PDF", resolution=300)
        r = core.convert(self.write("scan.pdf", buf.getvalue()))
        self.check(r)


class DocWithoutLibreOfficeTest(Base):
    def test_doc_is_reported_not_guessed(self):
        if shutil.which("soffice") or Path("/Applications/LibreOffice.app").exists():
            self.skipTest("LibreOffice is installed here")
        from tests.synth.cfb import make_cfb
        r = core.convert(self.write("invented.doc", make_cfb(["WordDocument", "1Table"])))
        self.assertEqual([reason for reason, _ in r.unread], ["converter_unavailable"])
        from heocr_desktop.i18n import STRINGS
        for lang in STRINGS:
            self.assertIn("unread_converter_unavailable", STRINGS[lang])


if __name__ == "__main__":
    unittest.main()
