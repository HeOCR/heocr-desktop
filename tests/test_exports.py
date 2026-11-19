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
