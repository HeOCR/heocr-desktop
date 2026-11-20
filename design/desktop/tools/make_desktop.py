"""HeOCR desktop mockups: one page with every screen in it; each mockup file is that page in one state.
Also writes strings/strings.json and the in-app icons. All sample text is invented."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ANDROID = HERE.parent.parent / "android" / "tools"
sys.path.insert(0, str(ANDROID))
import make_screens as A  # noqa: E402  the Android set's icons and the invented document

NEW_ICONS = {
    "drop": ('<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M12 10v7M9 14l3 3 3-3"/>', False, "Drop a file here"),
    "language": ('<rect x="3.5" y="3.5" width="17" height="17"/><path d="M3.5 12h17M12 3.5v17"/>', False, "Interface language"),
    "zoom-in": ('<rect x="4" y="4" width="12" height="12"/><path d="M15 15l6 6M10 7v6M7 10h6"/>', False, "Larger text"),
    "zoom-out": ('<rect x="4" y="4" width="12" height="12"/><path d="M15 15l6 6M7 10h6"/>', False, "Smaller text"),
    "json-file": ('<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M10.5 11H9v3l-1 1 1 1v3h1.5M13.5 11H15v3l1 1-1 1v3h-1.5"/>', False, "JSON record"),
    "markdown-file": ('<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M8.5 18v-6l2 3 2-3v6M15.5 12v6"/>', False, "Markdown file"),
}
ICONS = {**A.ICONS, **NEW_ICONS}
USED = ["open-file", "copy", "save", "word-doc", "text-file", "info", "close", "warning", "check", "external", "private", "image-file", "retry", "camera"]


def ico(name, cls=""):
    inner, flip, _ = ICONS[name]
    return f'<svg class="ico{" flip" if flip else ""}{" " + cls if cls else ""}" viewBox="0 0 24 24" aria-hidden="true">{inner}</svg>'


# key: (Hebrew, English, source). source: "app" = already in src/heocr_desktop/i18n.py, unchanged; "android" = from the Android
# design's strings.json; "new" = written for this design, Hebrew needs the owner's review.
T = {
    "tagline": ("טקסט עברי מכל מסמך", "Hebrew text out of any document", "app"),
    "lede": ("גוררים קובץ לחלון, ומקבלים את הטקסט שבו: כותרות, פסקאות, רשימות וטבלאות.", "Drop a file into the window and get its text out: headings, paragraphs, lists and tables.", "new"),
    "drop": ("גררו קובץ לכאן", "Drop a file here", "app"), "or": ("או", "or", "app"), "open": ("פתיחת קובץ…", "Open file…", "app"),
    "drop_hint": ("PDF, וורד (DOCX), תמונות, אקסל (XLSX), פאוורפוינט (PPTX) ודפי אינטרנט שמורים (HTML)", "PDF, Word (DOCX), images, Excel (XLSX), PowerPoint (PPTX) and saved web pages (HTML)", "new"),
    "offline_a": ("עובד במלואו ללא חיבור לרשת.", "Works fully offline.", "app"),
    "offline_b": ("הקבצים שלכם לא יוצאים מהמחשב: בלי רשת, בלי טלמטריה.", "Your files never leave this computer: no network, no telemetry.", "app"),
    "lang_toggle": ("English", "עברית", "app"), "about": ("אודות", "About", "app"), "close": ("סגירה", "Close", "app"),
    "drop_now": ("שחררו כדי לקרוא את הקובץ", "Drop to read the file", "new"), "drop_sub": ("אפשר לשחרר בכל מקום בחלון", "Anywhere in the window", "new"),
    "reading": ("קורא…", "Reading…", "app"), "page_of": ("עמוד 2 מתוך 3", "Page 2 of 3", "app"), "cancel": ("ביטול", "Cancel", "app"),
    "elapsed": ("זמן שעבר", "Time so far", "android"),
    "reading_hint": ("הקריאה נעשית במחשב הזה. עמוד סרוק יכול לקחת כמה שניות.", "The reading happens on this computer. A scanned page can take a few seconds.", "new"),
    "copy": ("העתקה", "Copy", "app"), "copy_all": ("העתקת כל הטקסט", "Copy all text", "new"), "copied": ("הועתק", "Copied", "app"),
    "save": ("שמירה", "Save", "new"), "save_as": ("שמירה בשם…", "Save as…", "new"),
    "save_docx": ("קובץ וורד (DOCX)", "Word file (DOCX)", "new"), "save_txt": ("טקסט (TXT)", "Text (TXT)", "new"),
    "save_md": ("Markdown (MD), עם הטבלאות", "Markdown (MD), tables kept", "new"), "save_json": ("רשומת JSON מלאה", "Full JSON record", "new"),
    "saved": ("נשמר", "Saved", "app"), "show_file": ("הצגה בתיקייה", "Show in folder", "new"),
    "new_file": ("קובץ אחר", "Another file", "app"),
    "view_formatted": ("מעוצב", "Formatted", "app"), "view_text": ("טקסט", "Text", "app"), "view_markdown": ("Markdown", "Markdown", "app"),
    "route": ("איך נקרא", "How it was read", "app"), "route_text_layer": ("שכבת טקסט", "text layer", "app"), "route_ocr": ("OCR", "OCR", "app"), "route_office": ("קובץ מסמך", "document file", "app"),
    "pages": ("3 עמודים", "3 pages", "app"), "seconds": ("41.2 שנ׳", "41.2 s", "app"),
    "ocr_note": ("טקסט שנקרא ב-OCR עלול לכלול טעויות. כדאי לבדוק אותו לפני שמסתמכים עליו.", "Text read by OCR may have mistakes. Check it before you rely on it.", "app"),
    "unread": ("<strong>חלק אחד לא נקרא:</strong> תמונה בעמוד 3. הפרטים ברשומת ה־JSON.", "<strong>1 part not read:</strong> a picture on page 3. Details are in the JSON record.", "new"),
    "index": ("עמודים", "Pages", "new"), "page": ("עמוד", "Page", "app"),
    "zoom_in": ("הגדלת הטקסט", "Larger text", "new"), "zoom_out": ("הקטנת הטקסט", "Smaller text", "new"), "zoom_reset": ("גודל רגיל", "Actual size", "new"),
    "m_unsupported_t": ("הקובץ הזה צריך המרה", "This file needs converting first", "new"),
    "needs_converter": ("קובצי וורד ישנים (‎.doc), ‏RTF וקובצי OpenDocument עדיין לא נתמכים: קריאתם דורשת את LibreOffice, שלא כלול ביישום. פתחו את הקובץ בוורד או ב-LibreOffice, שמרו אותו כ-‎.docx או כ-PDF, וגררו לכאן את הקובץ החדש.",
                        "Older Word files (.doc), RTF and OpenDocument files aren't supported yet: reading them needs LibreOffice, which this app does not include. Open the file in Word or LibreOffice, save it as .docx or PDF, and drop that here.", "app"),
    "m_damaged_t": ("לא ניתן היה לקרוא את הקובץ", "This file could not be read", "new"),
    "unreadable": ("לא ניתן היה לקרוא את הקובץ. ייתכן שהוא פגום, מוגן בסיסמה, או בפורמט ש-HeOCR עדיין לא קורא.", "This file could not be read. It may be damaged, password-protected, or a format HeOCR does not read yet.", "app"),
    "m_empty_t": ("לא נמצא טקסט", "No text found", "new"), "empty": ("לא נמצא טקסט בקובץ.", "No text was found in this file.", "app"),
    "m_empty_hint": ("אם זה צילום, כדאי לנסות תמונה חדה יותר, ישרה ובאור טוב.", "If it is a photo, try a sharper one, straight on and in good light.", "new"),
    "m_cancelled_t": ("הקריאה הופסקה", "Reading stopped", "new"), "cancelled": ("הופסק.", "Stopped.", "app"),
    "m_cancelled_b": ("הפסקת את הקריאה אחרי עמוד 2 מתוך 3. שום דבר לא נשמר.", "You stopped the reading after page 2 of 3. Nothing was saved.", "new"),
    "read_again": ("קריאה מחדש", "Read it again", "new"), "choose_other": ("בחירת קובץ אחר…", "Choose another file…", "new"),
    "about_body": ("HeOCR קורא טקסט עברי מקובצי PDF, וורד ותמונות, בעזרת צינור העיבוד הפתוח heocr ו-Tesseract OCR. הוא פועל כולו על המחשב הזה ולעולם לא מתחבר לאינטרנט. חינמי וקוד פתוח, ברישיון Apache 2.0.",
                   "HeOCR reads Hebrew text out of PDFs, Word files and images, with the open-source heocr pipeline and Tesseract OCR. It runs entirely on this computer and never connects to the internet. Free and open source under the Apache License 2.0.", "app"),
    "version": ("גרסה 0.1.0 (heocr 0.1.2,‏ Tesseract 5.5.3)", "Version 0.1.0 (heocr 0.1.2, Tesseract 5.5.3)", "app"),
    "about_models": ("מודלי OCR", "OCR models", "app"), "about_components": ("רכיבים כלולים והרישיונות שלהם", "Included components and their licences", "app"),
    "about_links": ("קישורים (נפתחים בדפדפן)", "Links (open in your browser)", "new"), "licence": ("רישיון", "Licence", "new"),
}
MENUS = {  # label: (Hebrew, English), items: (key in T or (he, en), mac shortcut, win shortcut)
    "app (macOS only)": (("HeOCR", "HeOCR"), [(("אודות HeOCR", "About HeOCR"), "", ""), (("יציאה מ-HeOCR", "Quit HeOCR"), "⌘Q", "")]),
    "file": (("קובץ", "File"), [(("פתיחה…", "Open…"), "⌘O", "Ctrl+O"), (("שמירה", "Save"), "⌘S", "Ctrl+S"), (("שמירה בשם…", "Save As…"), "⇧⌘S", "Ctrl+Shift+S"),
                                (("סגירת הקובץ", "Close File"), "⌘W", "Ctrl+W"), (("יציאה", "Exit"), "", "Alt+F4")]),
    "edit": (("עריכה", "Edit"), [(("העתקה", "Copy"), "⌘C", "Ctrl+C"), (("העתקת כל הטקסט", "Copy All Text"), "⇧⌘C", "Ctrl+Shift+C"), (("בחירת הכול", "Select All"), "⌘A", "Ctrl+A")]),
    "view": (("תצוגה", "View"), [(("מעוצב", "Formatted"), "⌘1", "Ctrl+1"), (("טקסט", "Text"), "⌘2", "Ctrl+2"), (("Markdown", "Markdown"), "⌘3", "Ctrl+3"),
                                 (("הגדלת הטקסט", "Larger Text"), "⌘+", "Ctrl++"), (("הקטנת הטקסט", "Smaller Text"), "⌘−", "Ctrl+−"), (("גודל רגיל", "Actual Size"), "⌘0", "Ctrl+0"),
                                 (("English", "עברית"), "", "")]),
    "help": (("עזרה", "Help"), [(("האתר של HeOCR", "HeOCR Website"), "", ""), (("HeOCR ב-GitHub", "HeOCR on GitHub"), "", ""), (("אודות HeOCR", "About HeOCR"), "", "")]),
}
HEADINGS = [(1, "ספריית השכונה: סדרי החורף", False), (1, "מה משתנה", True), (1, "שעות הפתיחה", True), (2, "השאלה והחזרה", False), (3, "איך מגיעים", False)]
PLAIN = """ספריית השכונה: סדרי החורף

החל מהשבוע הבא הספרייה עוברת לשעות החורף. האולם הגדול ייפתח מוקדם יותר בימי שלישי, ופינת הקריאה לילדים תישאר פתוחה גם אחר הצהריים.

מה משתנה

1. אפשר להשאיל ספרים עד רבע שעה לפני הסגירה.
2. ספרים מחזירים בתיבה שליד הכניסה, בכל שעה.
3. שעת הסיפור עוברת ליום רביעי אחר הצהריים.

שעות הפתיחה

יום\tבוקר\tאחר הצהריים\tהערות
ראשון\t9:00–12:30\t16:00–19:00\tהאולם הגדול בלבד
שלישי\t8:30–12:30\t16:00–20:00\tכולל פינת הילדים
רביעי\tסגור\t16:00–19:00\tשעת סיפור ב־17:00
שישי\t9:00–12:00\tסגור\t

השאלה והחזרה

כל קוראת וכל קורא יכולים להשאיל עד ארבעה ספרים לשלושה שבועות."""
MD = """# ספריית השכונה: סדרי החורף

החל מהשבוע הבא הספרייה עוברת לשעות החורף. האולם הגדול ייפתח מוקדם יותר בימי שלישי, ופינת הקריאה לילדים תישאר פתוחה גם אחר הצהריים.

## מה משתנה

1. אפשר להשאיל ספרים עד רבע שעה לפני הסגירה.
2. ספרים מחזירים בתיבה שליד הכניסה, בכל שעה.
3. שעת הסיפור עוברת ליום רביעי אחר הצהריים.

## שעות הפתיחה

| יום | בוקר | אחר הצהריים | הערות |
|---|---|---|---|
| ראשון | 9:00–12:30 | 16:00–19:00 | האולם הגדול בלבד |
| שלישי | 8:30–12:30 | 16:00–20:00 | כולל פינת הילדים |
| רביעי | סגור | 16:00–19:00 | שעת סיפור ב־17:00 |
| שישי | 9:00–12:00 | סגור | |

## השאלה והחזרה

כל קוראת וכל קורא יכולים להשאיל עד ארבעה ספרים לשלושה שבועות."""
THIRD = """heocr 0.1.2 · Apache-2.0
Tesseract OCR 5.5.3 · Apache-2.0
Leptonica 1.87.0 · BSD-2-Clause
pypdfium2 5.15.2 / PDFium · Apache-2.0 / BSD-3-Clause
Pillow 13.0.0 · MIT-CMU
defusedxml 0.7.1 · PSF-2.0
pywebview 6.2.1 · BSD-3-Clause
Python 3.12 · PSF-2.0
Noto Sans Hebrew, JetBrains Mono · OFL-1.1"""


def kb(mac, win):
    return f'<kbd class="k-mac">{mac}</kbd><kbd class="k-win">{win}</kbd>'


def page(lang, classes, view="formatted", message="unsupported", docx=False, toast=("saved", "עלון-ספרייה.txt", True)):
    i = 0 if lang == "he" else 1
    t = lambda k: T[k][i]
    d = "rtl" if lang == "he" else "ltr"
    doc = A.DOC.format(ocr_note=t("ocr_note"), **A.DOC_L[lang])
    idx = "".join(f'<button type="button"{" aria-current=true" if n == 0 else ""} class="{"sub" if sub else ""}">{"" if sub else f"<span class=num>{p}</span>"}<span dir="auto">{h}</span></button>'
                  for n, (p, h, sub) in enumerate(HEADINGS))
    hid = lambda v: "" if view == v else " hidden"
    sel = lambda v: "true" if view == v else "false"
    item = lambda icon, key, short="", hot=False: f'<button type="button" role="menuitem"{" class=hot" if hot else ""}>{ico(icon)}<span>{t(key)}</span><small>{short}</small></button>'
    menu = ((item("word-doc", "save_docx", "", True) if docx else "") + item("text-file", "save_txt", "", not docx) + item("markdown-file", "save_md") + item("json-file", "save_json"))
    M = {"unsupported": ("word-doc", "m_unsupported_t", "needs_converter", None, "choose_other", None),
         "damaged": ("warning", "m_damaged_t", "unreadable", None, "choose_other", None),
         "empty": ("image-file", "m_empty_t", "empty", "m_empty_hint", "choose_other", None),
         "cancelled": ("close", "m_cancelled_t", "m_cancelled_b", None, "read_again", "choose_other")}[message]
    msg = (f'<div class="message"><div class="mark">{ico(M[0])}</div><div class="fname"><bdi>{"מכתב-ישן.doc" if message == "unsupported" else "עלון-ספרייה.pdf"}</bdi></div>'
           f'<h2 id="message-title">{t(M[1])}</h2><p id="message-text" class="selectable">{t(M[2])}</p>{f"""<p class="hint">{t(M[3])}</p>""" if M[3] else ""}'
           f'<div class="row"><button type="button" class="btn primary" id="message-again">{ico("retry") if message == "cancelled" else ico("open-file")}{t(M[4])}</button>'
           f'{f"""<button type="button" class="btn">{t(M[5])}</button>""" if M[5] else ""}</div></div>')
    tk, tfile, action = toast
    return f'''<!doctype html>
<html lang="{lang}" dir="{d}">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' 'unsafe-inline'; font-src data:; img-src data:">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HeOCR</title>
<link rel="stylesheet" href="../../css/tokens.css">
<link rel="stylesheet" href="../../css/fonts-embedded.css">
<link rel="stylesheet" href="../../css/result.css">
<link rel="stylesheet" href="../../css/desktop.css">
</head>
<body class="hw mac {classes}">
<header class="bar"><span class="lockup" aria-label="HeOCR">{A.MARK}<span>He<b>OCR</b></span></span><span class="spacer"></span>
<button type="button" class="btn quiet" id="lang">{ico("language")}{t("lang_toggle")}</button><button type="button" class="btn quiet" id="about-open">{ico("info")}{t("about")}</button></header>
<main>
<section id="view-start" class="view" aria-labelledby="start-title"><div class="start">
<h1 id="start-title">{t("tagline")}</h1><p class="lede">{t("lede")}</p>
<div class="dropzone" id="dropzone">{ico("drop", "lg")}<strong>{t("drop")}</strong><span class="or">{t("or")}</span>
<button type="button" class="btn primary large" id="open">{t("open")} {kb("⌘O", "Ctrl+O")}</button><p class="hint">{t("drop_hint")}</p></div>
<p class="promise">{ico("private")}<span><strong>{t("offline_a")}</strong> {t("offline_b")}</span></p>
</div></section>

<section id="view-reading" class="view" aria-live="polite"><div class="work">
<div class="filecard">{ico("text-file")}<div><div class="fname" id="work-name"><bdi>עלון-ספרייה.pdf</bdi></div><div class="meta">PDF · {t("pages")}</div></div></div>
<div class="scan" aria-hidden="true"><div class="sheet-lines">{"<i></i>" * 9}<div class="read">{"<i></i>" * 9}</div><div class="cursor"></div></div></div>
<div class="progressline" role="status"><strong id="work-status">{t("page_of")}</strong><span class="num" aria-label="{t("elapsed")}">0:24</span></div>
<div class="pages" id="meter"><i class="done"></i><i class="now"></i><i></i></div>
<p class="hint" style="color:var(--muted);font-size:13.5px">{t("reading_hint")}</p>
<div class="rowend"><button type="button" class="btn" id="cancel">{t("cancel")} {kb("Esc", "Esc")}</button></div>
</div></section>

<section id="view-result" class="view">
<div class="toolbar"><div class="filemeta"><div class="fname" id="result-name"><bdi>עלון-ספרייה.pdf</bdi></div>
<div class="chips" id="chips"><span class="chip">{t("pages")}</span><span class="chip">{t("seconds")}</span></div></div>
<div class="actions"><button type="button" class="btn" id="copy" title="{t("copy_all")} (⇧⌘C)">{ico("copy")}{t("copy")}</button>
<div class="menuwrap"><button type="button" class="btn primary" id="save" aria-haspopup="menu" aria-expanded="{"true" if "menu-open" in classes else "false"}" title="{t("save")} (⌘S)">{ico("save")}{t("save")}<i class="caret"></i></button>
<div class="menu" role="menu" aria-label="{t("save_as")}">{menu}</div></div>
<button type="button" class="btn quiet" id="again" title="{t("open")} (⌘O)">{ico("open-file")}<span class="lbl-long">{t("new_file")}</span></button></div></div>
<div class="viewbar"><div class="seg" role="tablist"><button type="button" role="tab" data-view="formatted" aria-selected="{sel("formatted")}">{t("view_formatted")}</button><button type="button" role="tab" data-view="text" aria-selected="{sel("text")}">{t("view_text")}</button><button type="button" role="tab" data-view="markdown" aria-selected="{sel("markdown")}">{t("view_markdown")}</button></div>
<div class="zoom"><button type="button" class="iconbtn" aria-label="{t("zoom_out")}" title="{t("zoom_out")} (⌘−)">{ico("zoom-out")}</button><span class="num">100%</span><button type="button" class="iconbtn" aria-label="{t("zoom_in")}" title="{t("zoom_in")} (⌘+)">{ico("zoom-in")}</button></div>
<span class="how">{t("route")}: <span class="chip">{t("route_ocr")}</span></span></div>
<div class="split"><nav class="index" aria-label="{t("index")}"><div class="lab">{t("index")}</div>{idx}</nav>
<div class="reader" tabindex="0"><div class="inner"><div class="notes" id="notes"><div class="notice">{ico("warning")}<p>{t("unread")}</p></div></div>
<article class="doc" dir="rtl" id="doc-formatted"{hid("formatted")}>
{doc}
</article>
<pre class="doc plain" id="doc-text" dir="rtl"{hid("text")}>{PLAIN}</pre>
<pre class="doc plain mono" id="doc-markdown" dir="rtl"{hid("markdown")}>{MD}</pre>
</div></div></div>
</section>

<section id="view-message" class="view" role="alert">{msg}</section>
</main>

<div class="dropveil" aria-hidden="true"><div class="frame">{ico("drop")}<strong>{t("drop_now")}</strong><span>{t("drop_sub")}</span></div></div>
<div class="toast" id="toast" role="status" aria-live="polite">{ico("check")}<div>{t(tk)}{f"<small><bdi>{tfile}</bdi></small>" if tfile else ""}</div>{f"""<button type="button">{t("show_file")}</button>""" if action else ""}</div>

<div class="scrim"></div>
<dialog id="about" aria-labelledby="about-title">
<h2 id="about-title" dir="ltr">{A.MARK}<span>He<b>OCR</b></span></h2>
<p class="muted" id="about-version">{t("version")}</p>
<p>{t("about_body")}</p>
<p class="promise">{ico("private")}<span><strong>{t("offline_a")}</strong> {t("offline_b")}</span></p>
<h3>{t("about_links")}</h3>
<div class="rows"><div><a href="https://heocr.org" dir="ltr">heocr.org {ico("external")}</a></div><div><a href="https://github.com/HeOCR/heocr-desktop" dir="ltr">github.com/HeOCR/heocr-desktop {ico("external")}</a></div></div>
<h3>{t("licence")}</h3>
<div class="rows"><div><span dir="ltr">HeOCR</span><span class="end">Apache-2.0</span></div></div>
<h3 class="about-h">{t("about_models")}</h3>
<div class="rows" id="models"><div><span dir="ltr">heb · tessdata_best 4.1.0</span><span class="end">Apache-2.0</span></div><div><span dir="ltr">eng · tessdata_fast 4.1.0</span><span class="end">Apache-2.0</span></div></div>
<details{" open" if "about-open" in classes else ""}><summary>{t("about_components")}</summary><pre id="third-party" dir="ltr">{THIRD}</pre></details>
<div class="dialog-actions"><button type="button" class="btn primary" id="about-close">{t("close")} {kb("Esc", "Esc")}</button></div>
</dialog>
</body>
</html>
'''


SCREENS = [
    ("01-start", "Start", dict(classes="is-start")),
    ("02-start-dragging", "A file dragged over the window", dict(classes="is-start is-dragging")),
    ("03-reading", "Reading", dict(classes="is-reading")),
    ("04-result-formatted", "Result: formatted", dict(classes="is-result")),
    ("05-result-text", "Result: plain text", dict(classes="is-result", view="text")),
    ("06-result-markdown", "Result: Markdown", dict(classes="is-result", view="markdown")),
    ("07-result-save-menu", "Result: the Save menu, today", dict(classes="is-result menu-open")),
    ("07b-result-save-menu-with-word", "Result: the Save menu once Word ships", dict(classes="is-result menu-open", docx=True)),
    ("08-result-saved", "Result: saved", dict(classes="is-result toast-on")),
    ("09-result-copied", "Result: copied", dict(classes="is-result toast-on", toast=("copied", None, False))),
    ("10-problem-unsupported", "Problem: needs converting (.doc, RTF, OpenDocument)", dict(classes="is-message", message="unsupported")),
    ("11-problem-damaged", "Problem: the file could not be read", dict(classes="is-message", message="damaged")),
    ("12-problem-no-text", "Problem: no text found", dict(classes="is-message", message="empty")),
    ("13-problem-cancelled", "Problem: reading stopped", dict(classes="is-message", message="cancelled")),
    ("14-about", "About", dict(classes="is-start about-open")),
]

if __name__ == "__main__":
    jobs = []
    for lang in ("he", "en"):
        d = OUT / "mockups" / lang
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.html"):
            old.unlink()
        for name, _, kw in SCREENS:
            (d / f"{name}.html").write_text(page(lang, **kw), encoding="utf-8")
            jobs.append(dict(lang=lang, name=name))
    (HERE / "jobs.json").write_text(json.dumps(jobs))
    s = OUT / "strings"
    s.mkdir(exist_ok=True)
    (s / "strings.json").write_text(json.dumps({
        "_note": "Every string in the mockups. source: 'app' = already in src/heocr_desktop/i18n.py and unchanged; 'android' = from design/android/strings/strings.json; "
                 "'new' = written for this design, and its Hebrew needs the owner's review. Sample values (page counts, versions, times) stand in for the app's placeholders.",
        "strings": {k: {"he": v[0], "en": v[1], "source": v[2]} for k, v in T.items()},
        "menus": {k: {"label": {"he": lab[0], "en": lab[1]}, "items": [{"he": it[0][0], "en": it[0][1], "mac": it[1], "windows": it[2]} for it in items]} for k, (lab, items) in MENUS.items()},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    ic = OUT / "icons/in-app"
    ic.mkdir(parents=True, exist_ok=True)
    listing = {}
    for name in USED + list(NEW_ICONS):
        inner, flip, use = ICONS[name]
        (ic / f"{name}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
                                        f'stroke-linecap="square" stroke-linejoin="miter">{inner.replace(chr(32) + "class=" + chr(34) + "f" + chr(34), " fill=" + chr(34) + "currentColor" + chr(34) + " stroke=" + chr(34) + "none" + chr(34))}</svg>\n', encoding="utf-8")
        listing[name] = {"mirrors_in_rtl": flip, "use": use, "from": "desktop" if name in NEW_ICONS else "android"}
    (ic / "icons.json").write_text(json.dumps(listing, indent=1), encoding="utf-8")
    rows = "".join(f'<tr><td>{title}</td><td><a href="he/{n}.html">עברית</a></td><td><a href="en/{n}.html">English</a></td></tr>' for n, title, _ in SCREENS)
    (OUT / "mockups/index.html").write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>HeOCR desktop mockups</title><link rel="stylesheet" href="../css/tokens.css"><link rel="stylesheet" href="../css/fonts-embedded.css">
<style>body{{margin:0;padding:24px;background:var(--bg);color:var(--text);font:400 15px/1.5 var(--font-body);max-width:760px}}h1{{font:700 22px/1.2 var(--font-mono)}}table{{border-collapse:collapse;width:100%}}td{{padding:9px 8px;border-bottom:1px solid var(--line)}}a{{color:var(--accent)}}p{{color:var(--muted)}}</style></head>
<body><h1>HeOCR desktop mockups</h1><p>Every file is the same page in one state: the state is the class on <code>&lt;body&gt;</code>. Resize the window to see the layout between 720 × 520 and 1600 × 1000. The pages follow the system light or dark setting. No script.</p><table>{rows}</table></body></html>''', encoding="utf-8")
    print(len(jobs), "pages")
