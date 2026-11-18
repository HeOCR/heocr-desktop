import re

from heocr_desktop import i18n


def test_both_languages_have_every_string():
    assert set(i18n.STRINGS["en"]) == set(i18n.STRINGS["he"])


def test_placeholders_match():
    for key, en in i18n.STRINGS["en"].items():
        he = i18n.STRINGS["he"][key]
        assert set(re.findall(r"\{\w+\}", en)) == set(re.findall(r"\{\w+\}", he)), key


def test_forced_language(monkeypatch):
    monkeypatch.setenv("HEOCR_DESKTOP_LANG", "he")
    assert i18n.load_language() == "he"


def test_os_language_is_he_or_en():
    assert i18n.os_language() in ("he", "en")
