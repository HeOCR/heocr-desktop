from pathlib import Path

import heocr

from heocr_desktop import render

FIX = Path(__file__).resolve().parent / "fixtures"


def test_docx_html_has_headings_table_and_directions():
    doc = heocr.extract(str(FIX / "garden.docx"), ocr=False, convert=False)
    html = render.document_html(doc)
    assert html.count("<h1") == 1 and html.count("<h2") == 2
    assert "<table" in html and "<td" in html
    assert 'dir="auto"' in html or 'dir="rtl"' in html
    assert render.document_direction(doc.text) == "rtl"


def test_text_is_escaped():
    class Block:
        kind, role, source, label, level, note_id, page, slide, direction = "text", "body", "office_xml", None, None, None, None, None, None
        text = "<script>alert(1)</script> & שלום"
        flags = []

    out = render.block_html(Block())
    assert "<script>" not in out and "&lt;script&gt;" in out and "&amp;" in out


def test_direction():
    assert render.document_direction("שלום עולם hi") == "rtl"
    assert render.document_direction("hello there עולם") == "ltr"
    assert render.document_direction("") == "ltr"
