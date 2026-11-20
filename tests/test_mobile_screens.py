"""The Android app's screens (heocr_mobile.screens): the design's markup, approved strings, no script."""

import re
from types import SimpleNamespace

import pytest

from heocr_desktop import i18n
from heocr_mobile import screens, view

ACTIONS = {"photo", "open", "sample", "cancel", "home", "back", "about", "save-docx", "save-txt", "copy",
           "diagnostics", "licences", "more", "dismiss", "next"}


def links(page: str) -> set[str]:
    return set(re.findall(r'href="heocr:([a-z-]+)"', page))


def check_page(page: str, lang: str):
    assert "<script" not in page
    assert "default-src 'none'; style-src 'unsafe-inline'; font-src data:" in page
    assert f'<html lang="{lang}" dir="{"rtl" if lang == "he" else "ltr"}">' in page
    assert re.search(r"<[^>]+\son[a-z]+=", re.sub(r"<style>.*?</style>", "", page, flags=re.S)) is None
    assert links(page) <= ACTIONS, links(page) - ACTIONS
    assert "@font-face" in page and "url(data:" in page  # the typefaces travel inside the page


def doc(monkeypatch, text="גינה קהילתית"):
    markup = (
        '<div class="page-break" data-i18n="page_n" data-n="2"></div>'
        '<h2 class="section" data-i18n="section_footnote"></h2>'
        f'<p dir="rtl" class="block">{text}</p>'
    )
    monkeypatch.setattr(screens.render, "document_html", lambda d: markup)
    return SimpleNamespace(text=text)


@pytest.mark.parametrize("lang", ["he", "en"])
def test_every_screen_is_self_contained(monkeypatch, lang):
    t, d = screens.strings(lang), i18n.STRINGS[lang]
    pages = {
        "home": screens.home(t, lang, word=False),
        "reading": screens.reading(t, d, lang, "מכתב.pdf", 412_000, False, 1, 3, 24),
        "shared": screens.reading(t, d, lang, "letter.pdf", 2_000_000, True),
        "result": screens.result(t, d, lang, doc(monkeypatch), "מכתב.pdf", 3, 41.24, True, ["txt", "md", "json"]),
        "about": screens.about(t, lang, {"app": "0.1.0", "heocr": "0.2.0rc1", "tesseract": "5.5.3"}),
        "licences": screens.licences(t, lang, "# Licences\n\n- **heocr**: Apache-2.0\n\nSome text."),
        **{kind: screens.problem(t, d, lang, kind) for kind in ("unreadable", "needs_converter", "empty", "error")},
    }
    for name, page in pages.items():
        check_page(page, lang)
    assert {"photo", "open", "sample", "about"} <= links(pages["home"])
    assert links(pages["reading"]) >= {"cancel"} and 'id="elapsed"' in pages["reading"]
    assert {"copy", "more", "save-txt", "diagnostics", "dismiss"} <= links(pages["result"])


def test_result_fills_labels_and_leads_with_word_only_when_it_can_save_one(monkeypatch):
    t, d = screens.strings("he"), i18n.STRINGS["he"]
    page = screens.result(t, d, "he", doc(monkeypatch), "מכתב.pdf", 3, 41.24, True, ["txt"])
    assert 'data-n="2">עמוד 2</div>' in page
    assert 'data-i18n="section_footnote">הערות שוליים</h2>' in page
    assert f'<p class="note" dir="auto">{t["ocr_note"]}</p>' in page
    assert "<span class=\"chip\">3 עמודים</span>" in page and "<span class=\"chip\">OCR</span>" in page
    assert "save-docx" not in links(page) and '<a class="btn" href="heocr:copy"' in page
    word = screens.result(t, d, "he", doc(monkeypatch), "מכתב.pdf", 1, 2.0, False, ["docx", "txt"])
    assert '<a class="btn" href="heocr:save-docx"' in word and "OCR</span>" not in word and "עמודים" not in word


def test_file_names_and_document_text_are_escaped(monkeypatch):
    t, d = screens.strings("en"), i18n.STRINGS["en"]
    page = screens.result(t, d, "en", doc(monkeypatch), "<b>x</b>.pdf", 1, 1.0, False, ["txt"])
    assert "<b>x</b>" not in page and "&lt;b&gt;x&lt;/b&gt;.pdf" in page
    reading = screens.reading(t, d, "en", '"><img>.png', None, False)
    assert '"><img>' not in reading


def test_reading_counts_pages_from_the_start_side():
    t, d = screens.strings("en"), i18n.STRINGS["en"]
    page = screens.reading(t, d, "en", "a.pdf", 1000, False, 1, 3, 65)
    assert "Page 2 of 3" in page and ">1:05<" in page
    assert '<div class="pages"><i class="done"></i><i class="now"></i><i></i></div>' in page
    single = screens.reading(t, d, "en", "a.png", 1000, False)
    assert d["reading"] in single and '<div class="pages"><i class="now"></i></div>' in single


def test_problem_states_offer_one_next_step():
    t, d = screens.strings("en"), i18n.STRINGS["en"]
    photo = screens.problem(t, d, "en", "empty", photo=True)
    assert t["p3_a"] in photo and {"photo", "open"} <= links(photo)
    converter = screens.problem(t, d, "en", "needs_converter")
    assert t["p2_t"] in converter and "open" in links(converter)
    file_empty = screens.problem(t, d, "en", "empty")
    assert d["empty"] in file_empty and t["p3_h"] not in file_empty


def test_about_carries_this_builds_versions_and_the_model_dois():
    t = screens.strings("he")
    page = screens.about(t, "he", {"app": "9.9.9", "heocr": "8.8.8", "tesseract": "7.7.7"}, back="back")
    for value in ("9.9.9", "8.8.8", "7.7.7", "10.5281/zenodo.24372349", "10.5281/zenodo.24372352", "OFL 1.1"):
        assert value in page
    assert 'href="https://heocr.github.io"' in page and 'href="heocr:back"' in page


def test_strings_are_the_reviewed_design_strings():
    import json
    from pathlib import Path

    design = json.loads((Path(__file__).resolve().parent.parent / "design/android/strings/strings.json").read_text("utf-8"))
    assert screens.UI == design and "_reviewed" in design


def test_ocr_models_come_from_the_record():
    d = SimpleNamespace(components={"tesseract:heocr_modern_v1.traineddata": "sha256:x", "tesseract:eng.traineddata": "sha256:y", "Pillow": "13.0.0"})
    assert view.ocr_models(d) == {"heocr_modern_v1", "eng"}


def test_app_screens_never_zoom_and_the_reading_can(monkeypatch):
    t, d = screens.strings("en"), i18n.STRINGS["en"]
    assert screens.VIEWPORT_FIXED in screens.home(t, "en", word=False)
    assert screens.VIEWPORT_FIXED in screens.about(t, "en", {"app": "1", "heocr": "2", "tesseract": "3"})
    page = screens.result(t, d, "en", doc(monkeypatch), "a.pdf", 1, 1.0, False, ["txt"])
    assert screens.VIEWPORT_ZOOM in page and "maximum-scale=1" not in page
