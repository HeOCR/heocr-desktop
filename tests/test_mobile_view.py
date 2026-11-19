"""The Android app's reading page (heocr_mobile.view): plain HTML, labels filled, no script."""

from types import SimpleNamespace

from heocr_desktop import i18n
from heocr_mobile import view


def test_page_fills_labels_and_carries_no_script(monkeypatch):
    markup = (
        '<div class="page-break" data-i18n="page_n" data-n="2"></div>'
        '<h2 class="section" data-i18n="section_footnote"></h2>'
        '<p dir="rtl" class="block">גינה קהילתית</p>'
    )
    monkeypatch.setattr(view.render, "document_html", lambda doc: markup)
    html = view.page(SimpleNamespace(text="גינה קהילתית"), i18n.STRINGS["he"], ["הערה"])
    assert 'data-n="2">עמוד 2</div>' in html
    assert 'data-i18n="section_footnote">הערות שוליים</h2>' in html
    assert "<script" not in html and "default-src 'none'" in html
    assert '<html dir="rtl">' in html and '<p class="note">הערה</p>' in html
