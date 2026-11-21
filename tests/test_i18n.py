import re

from heocr_desktop import i18n


def test_english_fallback_is_limited_to_strings_awaiting_hebrew_approval():
    pending = {
        "open_folder", "batch_start", "batch_hint", "batch_done", "batch_saved", "batch_file",
        "batch_empty", "batch_read_error", "batch_write_error", "file_dialog_documents",
        "file_dialog_all_files", "unsupported_title", "unsupported", "unreadable",
        "batch_report_title", "batch_report_read", "batch_report_pages", "batch_report_remaining",
        "batch_report_failures", "batch_report_write_error",
    }
    en, he = i18n.STRINGS["en"], i18n.STRINGS["he"]
    assert set(he) <= set(en)
    assert set(en) - set(he) == pending
    assert all(i18n.text("he", key) == en[key] for key in pending)
    assert i18n.text("he", "open") == he["open"]


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
