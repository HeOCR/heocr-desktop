"""Interface strings, Hebrew and English, and the system's language."""
from __future__ import annotations

import locale
import os
import subprocess
import sys

STRINGS = {
    "en": {
        "dir": "ltr",
        "title": "HeOCR",
        "tagline": "Hebrew text out of PDFs, Word documents and images.",
        "drop": "Drop a file here",
        "or": "or",
        "open": "Open a file…",
        "types": "PDF, DOCX, DOC, PNG, JPG, TIFF",
        "offline": "Works fully offline: your files never leave this computer. No network, no telemetry.",
        "reading": "Reading",
        "page": "Page",
        "pages_of": "page {done} of {total}",
        "copy": "Copy text",
        "copied": "Copied",
        "save_txt": "Save .txt",
        "save_md": "Save .md",
        "save_json": "Save .json",
        "saved": "Saved",
        "view_structured": "Structure",
        "view_text": "Plain text",
        "route_text_layer": "Read from the PDF's text layer",
        "route_ocr": "Read by OCR (Tesseract)",
        "route_office": "Read from the Word document",
        "route_html": "Read from the web page",
        "route_unknown": "Read",
        "pages": "pages",
        "unread_title": "Not read",
        "unread_converter_unavailable": "DOC, RTF and ODT files need LibreOffice, which is not included"
                                        " (its licence is copyleft). Install LibreOffice, or save the file"
                                        " as DOCX and open that.",
        "unread_ocr_route_unavailable": "OCR is not available on this computer.",
        "unverified": "OCR text is a reading, not a verified transcript: check names and numbers.",
        "error": "Could not read this file",
        "about": "About",
        "close": "Close",
        "lang_toggle": "עברית",
        "another": "Open another file",
        "about_body": "HeOCR reads Hebrew text from documents on your computer, with the heocr library"
                      " and Tesseract OCR. It makes no network connections and sends no data anywhere.",
        "versions": "Versions",
        "licences": "Licences",
    },
    "he": {
        "dir": "rtl",
        "title": "HeOCR",
        "tagline": "טקסט עברי מתוך קובצי PDF, מסמכי Word ותמונות.",
        "drop": "גררו לכאן קובץ",
        "or": "או",
        "open": "פתיחת קובץ…",
        "types": "PDF, DOCX, DOC, PNG, JPG, TIFF",
        "offline": "עובד במלואו ללא אינטרנט: הקבצים שלכם לא יוצאים מהמחשב. אין חיבור לרשת ואין איסוף נתונים.",
        "reading": "קורא",
        "page": "עמוד",
        "pages_of": "עמוד {done} מתוך {total}",
        "copy": "העתקת הטקסט",
        "copied": "הועתק",
        "save_txt": "שמירה כ־txt",
        "save_md": "שמירה כ־md",
        "save_json": "שמירה כ־json",
        "saved": "נשמר",
        "view_structured": "מבנה",
        "view_text": "טקסט פשוט",
        "route_text_layer": "נקרא משכבת הטקסט של ה־PDF",
        "route_ocr": "נקרא בזיהוי תווים (Tesseract)",
        "route_office": "נקרא ממסמך ה־Word",
        "route_html": "נקרא מדף האינטרנט",
        "route_unknown": "נקרא",
        "pages": "עמודים",
        "unread_title": "לא נקרא",
        "unread_converter_unavailable": "קובצי DOC,‏ RTF ו־ODT דורשים את LibreOffice, שאינו כלול"
                                        " (הרישיון שלו הוא קופילפט). התקינו LibreOffice, או שמרו את הקובץ"
                                        " כ־DOCX ופתחו אותו.",
        "unread_ocr_route_unavailable": "זיהוי תווים אינו זמין במחשב הזה.",
        "unverified": "טקסט מזיהוי תווים הוא קריאה ולא תמלול מאומת: בדקו שמות ומספרים.",
        "error": "לא ניתן לקרוא את הקובץ",
        "about": "אודות",
        "close": "סגירה",
        "lang_toggle": "English",
        "another": "פתיחת קובץ אחר",
        "about_body": "HeOCR קורא טקסט עברי ממסמכים במחשב שלכם, בעזרת ספריית heocr ומנוע זיהוי התווים"
                      " Tesseract. הוא אינו מתחבר לרשת ואינו שולח נתונים לשום מקום.",
        "versions": "גרסאות",
        "licences": "רישיונות",
    },
}


def system_language() -> str:
    """'he' when the system's preferred language is Hebrew, else 'en'."""
    langs = []
    if sys.platform == "darwin":
        try:
            out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True,
                                 text=True, timeout=5).stdout
            langs += [x.strip().strip('",()') for x in out.split() if x.strip().strip('",()')]
        except (OSError, subprocess.SubprocessError):
            pass
    elif sys.platform == "win32":
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lang_id & 0x3FF == 0x0D:  # LANG_HEBREW
                return "he"
        except (AttributeError, OSError):
            pass
    langs += [os.environ.get(v, "") for v in ("LC_ALL", "LC_MESSAGES", "LANG")]
    try:
        langs.append(locale.getlocale()[0] or "")
    except ValueError:
        pass
    for lang in langs:
        if lang:
            return "he" if lang.lower().startswith(("he", "iw")) else "en"
    return "en"
