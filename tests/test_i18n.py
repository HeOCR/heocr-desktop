import re

from heocr_desktop import i18n


def test_english_and_hebrew_cover_the_same_strings():
    en, he = i18n.STRINGS["en"], i18n.STRINGS["he"]
    assert en.keys() == he.keys()


def test_placeholders_match():
    for key, he in i18n.STRINGS["he"].items():
        en = i18n.STRINGS["en"][key]
        assert set(re.findall(r"\{\w+\}", en)) == set(re.findall(r"\{\w+\}", he)), key


def test_forced_language(monkeypatch):
    monkeypatch.setenv("HEOCR_DESKTOP_LANG", "he")
    assert i18n.load_language() == "he"


def test_fresh_settings_start_in_hebrew_and_remember_english(monkeypatch, tmp_path):
    monkeypatch.delenv("HEOCR_DESKTOP_LANG", raising=False)
    monkeypatch.setattr(i18n, "settings_path", lambda: tmp_path / "settings.json")
    assert i18n.load_language() == "he"
    i18n.save_language("en")
    assert i18n.load_language() == "en"
