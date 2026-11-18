"""Write one invented-text fixture of each type into a folder, for the packaged app's smoke run.

    python scripts/make_fixtures.py OUTDIR

Writes text.pdf (text layer), scan.pdf, page.png, page.jpg, page.tif and doc.docx, plus expected.json:
what each file must yield. All text is invented.
"""
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.synth.docx import Docx, para, table  # noqa: E402
from tests.synth.pdf import PdfPage, lines_block, make_pdf  # noqa: E402
from tests.test_core import LINES, OCR_WORDS, hebrew_font, image_with  # noqa: E402


def main(out: str) -> None:
    d = Path(out)
    d.mkdir(parents=True, exist_ok=True)
    (d / "text.pdf").write_bytes(make_pdf([PdfPage(lines=lines_block(LINES))]))
    body = [para("כותרת מסמך מומצא", style="Heading1"), para("פסקה ראשונה במסמך לדוגמה."),
            table([["עמודה א", "עמודה ב"], ["תא אחד", "תא שני"]], borders=True)]
    (d / "doc.docx").write_bytes(Docx(body=body).build())
    im = image_with(OCR_WORDS, hebrew_font())
    for name, fmt in (("page.png", "PNG"), ("page.jpg", "JPEG"), ("page.tif", "TIFF")):
        buf = io.BytesIO()
        im.save(buf, fmt, dpi=(300, 300))
        (d / name).write_bytes(buf.getvalue())
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PDF", resolution=300)
    (d / "scan.pdf").write_bytes(buf.getvalue())
    expected = {"text.pdf": {"route": "text_layer", "contains": LINES},
                "doc.docx": {"route": "office", "contains": ["פסקה ראשונה במסמך לדוגמה."]},
                **{n: {"route": "ocr", "any_of": OCR_WORDS, "at_least": 2}
                   for n in ("page.png", "page.jpg", "page.tif", "scan.pdf")}}
    (d / "expected.json").write_text(json.dumps(expected, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
