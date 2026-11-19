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
    assert '<html dir="rtl">' in html and '<p class="note" dir="auto">הערה</p>' in html


def test_notes_keep_their_own_direction_and_welcome_follows_the_ui(monkeypatch):
    monkeypatch.setattr(view.render, "document_html", lambda doc: '<p dir="rtl" class="block">גינה</p>')
    html = view.page(SimpleNamespace(text="גינה"), i18n.STRINGS["en"], ["Text read by OCR may have mistakes."])
    assert '<p class="note" dir="auto">Text read by OCR' in html
    strings = {"welcome": "פתחו קובץ", "offline": "בלי אינטרנט"}
    assert '<html dir="rtl">' in view.welcome(strings, "he")
    assert '<html dir="ltr">' in view.welcome(strings, "en")


def test_ocr_models_come_from_the_record():
    doc = SimpleNamespace(components={"tesseract:heocr_modern_v1.traineddata": "sha256:x", "tesseract:eng.traineddata": "sha256:y", "Pillow": "13.0.0"})
    assert view.ocr_models(doc) == {"heocr_modern_v1", "eng"}
