""""Copy diagnostics" sends how a file was read, never what it says."""

import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from heocr_desktop import diagnostics

heocr = pytest.importorskip("heocr")
FIX = Path(__file__).resolve().parent / "fixtures"
HEBREW = re.compile(r"[֐-׿]")


@pytest.mark.parametrize("name", ["garden.docx", "garden.pdf"])
def test_the_report_has_the_structure_and_no_text(name):
    doc = heocr.extract(str(FIX / name), ocr=False, convert=False)
    result = SimpleNamespace(doc=doc, kind="ok", seconds=0.5)
    report = diagnostics.report(result, app="test", app_version="0", input_bytes=123, declared_bytes=123)
    out = diagnostics.text(report)
    assert report["format"] in ("docx", "pdf") and report["blocks"]
    assert not HEBREW.search(out), "Hebrew text leaked into the diagnostics"
    for word in ("summary", "volunteers", "Friday", doc.sha256):
        assert word not in out
    if name.endswith(".pdf"):
        assert [p["route"] for p in report["pages"]] == ["text_layer"]
        assert diagnostics.page_structure(doc)[0]["route"] == "text_layer"


def test_unsafe_values_are_dropped():
    assert diagnostics._safe({"ok": 1, "code": "text_layer", "prose": "a sentence, with commas", "x" * 70: 1}) == {"ok": 1, "code": "text_layer"}
