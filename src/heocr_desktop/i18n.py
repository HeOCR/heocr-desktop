"""Interface strings in Hebrew and English, and the OS language.

The window starts in the OS language (Hebrew if the user's first preferred language is
Hebrew, otherwise English) and has a toggle. The choice is kept in a small settings file in the
user's own folder; nothing else is stored.
"""

from __future__ import annotations

import json
import locale
import os
import sys
from pathlib import Path

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "title": "HeOCR",
        "tagline": "Hebrew text out of any document",
        "drop": "Drop a file here",
        "drop_hint": "PDF, Word (.docx), or an image (PNG, JPG, TIFF)",
        "open": "Open file…",
        "or": "or",
        "offline": "Works fully offline. Your files never leave this computer: no network, no telemetry.",
        "reading": "Reading…",
        "page_of": "Page {done} of {total}",
        "page_n_progress": "Page {done}",
        "finishing": "Finishing…",
        "cancel": "Cancel",
        "cancelled": "Stopped.",
        "copy": "Copy",
        "copied": "Copied",
        "save_txt": "Save .txt",
        "save_md": "Save .md",
        "save_json": "Save .json",
        "saved": "Saved",
        "new_file": "Another file",
        "view_formatted": "Formatted",
        "view_text": "Text",
        "view_markdown": "Markdown",
        "lang_toggle": "עברית",
        "about": "About",
        "close": "Close",
        "route": "How it was read",
        "route_text_layer": "text layer",
        "route_ocr": "OCR",
        "route_none": "not read",
        "route_office": "document file",
        "pages": "{n} pages",
        "page": "1 page",
        "seconds": "{s} s",
        "unread_n": "{n} parts not read (see Save .json)",
        "unread_1": "1 part not read (see Save .json)",
        "ocr_note": "Text read by OCR may have mistakes. Check it before you rely on it.",
        "needs_converter": "Older Word files (.doc), RTF and OpenDocument files aren't supported yet: reading them needs LibreOffice, which this app does not include. Open the file in Word or LibreOffice, save it as .docx or PDF, and drop that here.",
        "unreadable": "This file could not be read. It may be damaged, password-protected, or a format HeOCR does not read yet.",
        "empty": "No text was found in this file.",
        "error": "Something went wrong while reading this file.",
        "no_ocr": "OCR is not available in this build, so scanned pages were not read.",
        "note_numbers_not_rechecked": "Numbers in this file were not read a second time (a known issue in heocr 0.1.0rc1): check them against the original.",
        "figure_not_read": "[picture not read]",
        "page_n": "Page {n}",
        "slide_n": "Slide {n}",
        "section_footnote": "Footnotes",
        "section_endnote": "Endnotes",
        "section_comment": "Comments",
        "section_header": "Headers",
        "section_footer": "Footers",
        "section_notes": "Speaker notes",
        "section_navigation": "Navigation",
        "about_body": "HeOCR reads Hebrew text out of PDFs, Word files and images, with the open-source heocr pipeline and Tesseract OCR. It runs entirely on this computer and never connects to the internet. Free and open source under the Apache License 2.0.",
        "about_components": "Included components and their licences",
        "about_models": "OCR models",
        "about_site": "heocr.github.io",
        "version": "Version {v} (heocr {h}, Tesseract {t})",
        "files_supported": "Supported files",
    },
    "he": {
        "title": "HeOCR",
        "tagline": "טקסט עברי מכל מסמך",
        "drop": "גררו קובץ לכאן",
        "drop_hint": "PDF, וורד (‎.docx) או תמונה (PNG,‏ JPG,‏ TIFF)",
        "open": "פתיחת קובץ…",
        "or": "או",
        "offline": "עובד במלואו ללא חיבור לרשת. הקבצים שלכם לא יוצאים מהמחשב: בלי רשת, בלי טלמטריה.",
        "reading": "קורא…",
        "page_of": "עמוד {done} מתוך {total}",
        "page_n_progress": "עמוד {done}",
        "finishing": "מסיים…",
        "cancel": "ביטול",
        "cancelled": "הופסק.",
        "copy": "העתקה",
        "copied": "הועתק",
        "save_txt": "שמירה כ-‎.txt",
        "save_md": "שמירה כ-‎.md",
        "save_json": "שמירה כ-‎.json",
        "saved": "נשמר",
        "new_file": "קובץ אחר",
        "view_formatted": "מעוצב",
        "view_text": "טקסט",
        "view_markdown": "Markdown",
        "lang_toggle": "English",
        "about": "אודות",
        "close": "סגירה",
        "route": "איך נקרא",
        "route_text_layer": "שכבת טקסט",
        "route_ocr": "OCR",
        "route_none": "לא נקרא",
        "route_office": "קובץ מסמך",
        "pages": "{n} עמודים",
        "page": "עמוד אחד",
        "seconds": "{s} שנ׳",
        "unread_n": "{n} חלקים לא נקראו (פרטים בשמירה כ-‎.json)",
        "unread_1": "חלק אחד לא נקרא (פרטים בשמירה כ-‎.json)",
        "ocr_note": "טקסט שנקרא ב-OCR עלול לכלול טעויות. כדאי לבדוק אותו לפני שמסתמכים עליו.",
        "needs_converter": "קובצי וורד ישנים (‎.doc), ‏RTF וקובצי OpenDocument עדיין לא נתמכים: קריאתם דורשת את LibreOffice, שלא כלול ביישום. פתחו את הקובץ בוורד או ב-LibreOffice, שמרו אותו כ-‎.docx או כ-PDF, וגררו אותו לכאן.",
        "unreadable": "לא ניתן היה לקרוא את הקובץ. ייתכן שהוא פגום, מוגן בסיסמה, או בפורמט ש-HeOCR עדיין לא קורא.",
        "empty": "לא נמצא טקסט בקובץ.",
        "error": "משהו השתבש בזמן קריאת הקובץ.",
        "no_ocr": "OCR אינו זמין בגרסה זו, ולכן עמודים סרוקים לא נקראו.",
        "note_numbers_not_rechecked": "המספרים בקובץ לא נקראו פעם שנייה (תקלה ידועה ב-heocr 0.1.0rc1): כדאי לבדוק אותם מול המקור.",
        "figure_not_read": "[תמונה שלא נקראה]",
        "page_n": "עמוד {n}",
        "slide_n": "שקופית {n}",
        "section_footnote": "הערות שוליים",
        "section_endnote": "הערות סיום",
        "section_comment": "הערות",
        "section_header": "כותרות עליונות",
        "section_footer": "כותרות תחתונות",
        "section_notes": "הערות דובר",
        "section_navigation": "ניווט",
        "about_body": "HeOCR קורא טקסט עברי מקובצי PDF, וורד ותמונות, בעזרת צינור העיבוד הפתוח heocr ו-Tesseract OCR. הוא פועל כולו על המחשב הזה ולעולם לא מתחבר לאינטרנט. חינמי וקוד פתוח, ברישיון Apache 2.0.",
        "about_components": "רכיבים כלולים והרישיונות שלהם",
        "about_models": "מודלי OCR",
        "about_site": "heocr.github.io",
        "version": "גרסה {v} (heocr {h},‏ Tesseract {t})",
        "files_supported": "קבצים נתמכים",
    },
}


def os_language() -> str:
    """``he`` when the user's first preferred OS language is Hebrew, else ``en``."""
    codes: list[str] = []
    try:
        if sys.platform == "darwin":
            from Foundation import NSLocale  # pyobjc, shipped with pywebview on macOS

            codes = [str(c) for c in NSLocale.preferredLanguages()]
        elif sys.platform == "win32":
            import ctypes

            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            codes = ["he" if (lang_id & 0x3FF) == 0x0D else "en"]
    except Exception:  # noqa: BLE001 - any failure falls back to the locale
        codes = []
    if not codes:
        for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
            if os.environ.get(var):
                codes = [os.environ[var]]
                break
    if not codes:
        try:
            codes = [locale.getlocale()[0] or ""]
        except ValueError:
            codes = []
    first = (codes[0] if codes else "").lower()
    return "he" if first.startswith(("he", "iw")) else "en"


def settings_path() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "HeOCR" / "settings.json"


def load_language() -> str:
    forced = os.environ.get("HEOCR_DESKTOP_LANG")  # screenshots and tests
    if forced in STRINGS:
        return forced
    try:
        saved = json.loads(settings_path().read_text("utf-8")).get("language")
        if saved in STRINGS:
            return saved
    except (OSError, ValueError, AttributeError):
        pass
    return os_language()


def save_language(language: str) -> None:
    if language not in STRINGS:
        return
    path = settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"language": language}), "utf-8")
    except OSError:
        pass
