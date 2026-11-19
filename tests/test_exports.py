"""What Save writes: .txt carries a UTF-8 byte-order mark (Windows Notepad), the others plain UTF-8."""

import json
from types import SimpleNamespace

import pytest

from heocr_desktop import exports

DOC = SimpleNamespace(text="גינה קהילתית\n4,250 שקלים\n", markdown="# גינה\n", to_dict=lambda: {"text": "גינה"})


def test_txt_has_a_utf8_bom_and_decodes_back():
    data = exports.export(DOC, "txt")
    assert data.startswith(b"\xef\xbb\xbf")
    assert data.decode("utf-8-sig") == DOC.text


def test_md_and_json_are_plain_utf8():
    assert exports.export(DOC, "md") == "# גינה\n".encode("utf-8")
    assert json.loads(exports.export(DOC, "json").decode("utf-8")) == {"text": "גינה"}


def test_unknown_format_is_refused():
    with pytest.raises(ValueError):
        exports.export(DOC, "pdf")


def test_word_comes_first_only_when_heocr_can_write_it(monkeypatch):
    import heocr

    monkeypatch.delattr(heocr.Document, "to_docx", raising=False)
    assert exports.formats() == ("txt", "md", "json")
    monkeypatch.setattr(heocr.Document, "to_docx", lambda self: b"PK\x03\x04", raising=False)
    assert exports.formats()[0] == "docx"
    doc = SimpleNamespace(to_docx=lambda: b"PK\x03\x04")
    assert exports.export(doc, "docx") == b"PK\x03\x04"
