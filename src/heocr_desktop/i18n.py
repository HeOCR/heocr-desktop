"""Interface strings in Hebrew and English.

The window starts in Hebrew until the user chooses English. The choice is kept in a small
settings file in the user's own folder; nothing else is stored.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "unread_picture_title": "{n} part not read:",
        "unread_picture_body": "a picture on page {page}. Details are in the JSON record.",
        "unread_details": "Details are in the JSON record.",
        "m_unsupported_t": "This file needs converting first",
        "m_damaged_t": "This file could not be read",
        "m_empty_t": "No text found",
        "m_empty_hint": "If it is a photo, try a sharper one, straight on and in good light.",
        "m_cancelled_t": "Reading stopped",
        "m_cancelled_b": "You stopped the reading after page {done} of {total}. Nothing was saved.",
        "read_again": "Read it again",
        "nothing_saved": "Nothing was saved.",
        "zoom_in": "Larger text",
        "zoom_out": "Smaller text",
        "show_file": "Show in folder",
        "copy_all": "Copy all text",
        "index": "Pages",
        "title": "HeOCR",
        "tagline": "Hebrew text out of any document",
        "drop": "Drop a file here",
        "drop_hint": "PDF, Word (DOCX), images, Excel (XLSX), PowerPoint (PPTX) and saved web pages (HTML)",
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
        "save_docx": "Word file (DOCX)",
        "save_txt": "Text (TXT)",
        "save_md": "Markdown (MD), tables kept",
        "save_json": "Full JSON record",
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
        "unread_n": "{n} parts not read.",
        "unread_1": "1 part not read.",
        "ocr_note": "Text read by OCR may have mistakes. Check it before you rely on it.",
        "needs_converter": "Older Word files (.doc), RTF and OpenDocument files aren't supported yet: reading them needs LibreOffice, which this app does not include. Open the file in Word or LibreOffice, save it as .docx or PDF, and drop that here.",
        "unreadable": "This file could not be read. It may be damaged, password-protected, or a format HeOCR does not read yet.",
        "empty": "No text was found in this file.",
        "error": "Something went wrong while reading this file.",
        "no_ocr": "OCR is not available in this build, so scanned pages were not read.",
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
        "about_links": "Links (open in your browser)",
        "version": "Version {v} (heocr {h}, Tesseract {t})",
        "files_supported": "Supported files",
        "lede": "Drop a file into the window and get its text out: headings, paragraphs, lists and tables.",
        "offline_a": "Works fully offline.",
        "offline_b": "Your files never leave this computer: no network, no telemetry.",
        "drop_now": "Drop to read the file",
        "drop_sub": "Anywhere in the window",
        "elapsed": "Time so far",
        "reading_hint": "The reading happens on this computer. A scanned page can take a few seconds.",
        "save": "Save",
        "save_as": "Save as…",
        "choose_other": "Choose another file…",
        "licence": "Licence",
    },
    "he": {
        "unread_picture_title": "חלק {n} לא נקרא:",
        "unread_picture_body": "תמונה בעמוד {page}. הפרטים ברשומת ה־JSON.",
        "unread_details": "הפרטים ברשומת ה־JSON.",
        "m_unsupported_t": "הקובץ הזה צריך המרה",
        "m_damaged_t": "לא ניתן היה לקרוא את הקובץ",
        "m_empty_t": "לא נמצא טקסט",
        "m_empty_hint": "אם זה צילום, כדאי לנסות תמונה חדה יותר, ישרה ובאור טוב.",
        "m_cancelled_t": "הקריאה הופסקה",
        "m_cancelled_b": "הפסקת את הקריאה אחרי עמוד {done} מתוך {total}. שום דבר לא נשמר.",
        "read_again": "קריאה מחדש",
        "nothing_saved": "שום דבר לא נשמר.",
        "zoom_in": "הגדלת הטקסט",
        "zoom_out": "הקטנת הטקסט",
        "show_file": "הצגה בתיקייה",
        "copy_all": "העתקת כל הטקסט",
        "index": "עמודים",
        "title": "HeOCR",
        "tagline": "טקסט עברי מכל מסמך",
        "drop": "גררו קובץ לכאן",
        "drop_hint": "PDF, וורד (DOCX), תמונות, אקסל (XLSX), פאוורפוינט (PPTX) ודפי אינטרנט שמורים (HTML)",
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
        "save_docx": "קובץ וורד (DOCX)",
        "save_txt": "טקסט (TXT)",
        "save_md": "Markdown (MD), עם הטבלאות",
        "save_json": "רשומת JSON מלאה",
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
        "unread_n": "{n} חלקים לא נקראו.",
        "unread_1": "חלק אחד לא נקרא.",
        "ocr_note": "טקסט שנקרא ב-OCR עלול לכלול טעויות. כדאי לבדוק אותו לפני שמסתמכים עליו.",
        "needs_converter": "קובצי וורד ישנים (‎.doc), ‏RTF וקובצי OpenDocument עדיין לא נתמכים: קריאתם דורשת את LibreOffice, שלא כלול ביישום. פתחו את הקובץ בוורד או ב-LibreOffice, שמרו אותו כ-‎.docx או כ-PDF, וגררו אותו לכאן.",
        "unreadable": "לא ניתן היה לקרוא את הקובץ. ייתכן שהוא פגום, מוגן בסיסמה, או בפורמט ש-HeOCR עדיין לא קורא.",
        "empty": "לא נמצא טקסט בקובץ.",
        "error": "משהו השתבש בזמן קריאת הקובץ.",
        "no_ocr": "OCR אינו זמין בגרסה זו, ולכן עמודים סרוקים לא נקראו.",
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
        "about_links": "קישורים (נפתחים בדפדפן)",
        "version": "גרסה {v} (heocr {h},‏ Tesseract {t})",
        "files_supported": "קבצים נתמכים",
        "lede": "גוררים קובץ לחלון, ומקבלים את הטקסט שבו: כותרות, פסקאות, רשימות וטבלאות.",
        "offline_a": "עובד במלואו ללא חיבור לרשת.",
        "offline_b": "הקבצים שלכם לא יוצאים מהמחשב: בלי רשת, בלי טלמטריה.",
        "drop_now": "שחררו כדי לקרוא את הקובץ",
        "drop_sub": "אפשר לשחרר בכל מקום בחלון",
        "elapsed": "זמן שעבר",
        "reading_hint": "הקריאה נעשית במחשב הזה. עמוד סרוק יכול לקחת כמה שניות.",
        "save": "שמירה",
        "save_as": "שמירה בשם…",
        "choose_other": "בחירת קובץ אחר…",
        "licence": "רישיון",
    },
}


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
    return "he"


def save_language(language: str) -> None:
    if language not in STRINGS:
        return
    path = settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"language": language}), "utf-8")
    except OSError:
        pass
