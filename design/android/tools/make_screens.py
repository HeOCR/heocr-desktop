"""HeOCR Android mockups: one static HTML file per screen and language, built on css/*.css.
No script in any page. Also writes the in-app icons as standalone SVG files."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent

# ------------------------------------------------------------------ icons (24 dp grid)
ICONS = {
    # name: (inner svg, mirrors in RTL, note)
    "camera": ('<path d="M3 8h4l1.5-3h7L17 8h4v11H3z"/><rect x="9" y="10.5" width="6" height="6"/>', False, "Take a photo"),
    "open-file": ('<path d="M3 5h7l2 3h9v11H3z"/>', False, "Open a file"),
    "sample": ('<path d="M5 3h14v18H5z"/><rect x="8" y="7" width="8" height="5"/><path d="M8 16h8"/>', False, "Try a sample"),
    "copy": ('<path d="M9 9h11v11H9z"/><path d="M15 9V4H4v11h5"/>', False, "Copy"),
    "share": ('<path d="M8 11l8-4M8 13l8 4"/><rect x="3" y="9.5" width="5" height="5"/><rect x="16" y="3.5" width="5" height="5"/><rect x="16" y="15.5" width="5" height="5"/>', False, "Share"),
    "save": ('<path d="M12 3v12M7 10.5l5 5 5-5M4 20h16"/>', False, "Save"),
    "word-doc": ('<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M8.5 11.5l1.3 5.5 2.2-4 2.2 4 1.3-5.5"/>', False, "Word document"),
    "text-file": ('<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 12h6M9 15h6M9 18h3"/>', False, "Text file"),
    "info": ('<rect x="3.5" y="3.5" width="17" height="17"/><path d="M12 11v6"/><path d="M12 7v1"/>', False, "About / info"),
    "close": ('<path d="M6 6l12 12M18 6L6 18"/>', False, "Close / cancel"),
    "warning": ('<path d="M12 3.5L21.5 20h-19z"/><path d="M12 10v4.5"/><path d="M12 17v.5"/>', False, "Warning"),
    "check": ('<path d="M4.5 12.5l5 5L19.5 7"/>', False, "Check / done"),
    "diagnostics": ('<path d="M9 5H5v16h14V5h-4"/><rect x="9" y="3" width="6" height="4"/><path d="M8 14h2.5l1.5-3 2 6 1.5-3H16"/>', False, "Copy diagnostics"),
    # extensions beyond the brief's list
    "back": ('<path d="M20 12H5M11 6l-6 6 6 6"/>', True, "Back (points to the start side)"),
    "more": ('<rect x="10.5" y="4" width="3" height="3" class="f"/><rect x="10.5" y="10.5" width="3" height="3" class="f"/><rect x="10.5" y="17" width="3" height="3" class="f"/>', False, "More actions"),
    "external": ('<path d="M11 5H5v14h14v-6"/><path d="M14 4h6v6M20 4l-9 9"/>', True, "Opens in the browser"),
    "private": ('<rect x="5" y="10" width="14" height="10"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>', False, "Stays on the phone"),
    "image-file": ('<rect x="3.5" y="4.5" width="17" height="15"/><path d="M3.5 16l5-5 4 4 3-3 5 5"/><rect x="14" y="7.5" width="3" height="3"/>', False, "Image file"),
    "chevron": ('<path d="M9 5l7 7-7 7"/>', True, "Goes to another screen (points to the end side)"),
    "retry": ('<path d="M19 12a7 7 0 1 1-2.05-4.95"/><path d="M19 4v5h-5"/>', False, "Read again"),
}


def ico(name, cls=""):
    inner, flip, _ = ICONS[name]
    c = "ico" + (" flip" if flip else "") + (" " + cls if cls else "")
    return f'<svg class="{c}" viewBox="0 0 24 24" aria-hidden="true">{inner}</svg>'


def write_icons():
    d = OUT / "icons/in-app"
    d.mkdir(parents=True, exist_ok=True)
    for name, (inner, _, _) in ICONS.items():
        inner = inner.replace(' class="f"', ' fill="currentColor" stroke="none"')
        (d / f"{name}.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="square" stroke-linejoin="miter">{inner}</svg>\n', encoding="utf-8")
    (d / "icons.json").write_text(json.dumps({n: {"mirrors_in_rtl": f, "use": u} for n, (_, f, u) in ICONS.items()}, indent=2), encoding="utf-8")


MARK = ('<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="7" y="7" width="34" height="34" class="lg-box"/>'
        + "".join(f'<rect x="{x}" y="{y}" width="6" height="6" class="lg-h"/>' for x, y in ((4, 4), (38, 4), (4, 38), (38, 38)))
        + '<path d="M16 18H32V32.5M16 24.5V32.5" class="lg-ink"/></svg>')

# ------------------------------------------------------------------ strings
S = {
    "he": dict(
        dir="rtl", tagline="טקסט עברי מכל מסמך",
        home_lede="מצלמים דף או פותחים קובץ, ומקבלים את הטקסט שבו: להעתקה, לשיתוף או לשמירה כקובץ וורד.",
        home_lede_now="מצלמים דף או פותחים קובץ, ומקבלים את הטקסט שבו, מוכן להעתקה.",
        capture="צילום", capture_sub="מכתב, דף מספר או כל עמוד מודפס",
        open="פתיחת קובץ", sample="דוגמה", about="אודות", back="חזרה", cancel="ביטול", close="סגירה",
        offline_a="עובד במלואו בלי אינטרנט:", offline_b="שום דבר שנקרא לא יוצא מהטלפון.",
        reads_a="מה אפשר לקרוא", reads_b="קובצי PDF, קובצי וורד (DOCX) ותמונות. אפשר גם לשתף קובץ ל־HeOCR מאפליקציה אחרת.",
        file_name="עלון-ספרייה.pdf", file_meta="PDF · 3 עמודים · <span class=\"num\">412 KB</span>",
        shared_title="התקבל קובץ", shared_chip="שותף מאפליקציה אחרת", shared_sub="הקריאה מתחילה מיד. הקובץ נשאר בטלפון.", starting="מתחילים לקרוא…",
        reading_title="קוראים את המסמך", page_of="עמוד 2 מתוך 3", page_0="עמוד 1 מתוך 3", elapsed="זמן שעבר",
        reading_hint="הקריאה נעשית בטלפון עצמו, ולכן עמוד יכול לקחת עד כ־20 שניות. אפשר להשאיר את האפליקציה פתוחה ולחכות.",
        res_meta=["3 עמודים", "<span class=\"num\">41.2</span> שנ׳"],
        ocr_note="טקסט שנקרא ב-OCR עלול לכלול טעויות. כדאי לבדוק אותו לפני שמסתמכים עליו.",
        unread="<strong>חלק אחד לא נקרא:</strong> תמונה בעמוד 3. שאר המסמך נקרא.",
        save_word="שמירה כקובץ וורד", copy="העתקה", share="שיתוף", more="עוד פעולות",
        sheet_title="עוד פעולות", save_txt="שמירה כקובץ טקסט (TXT)", save_txt_sub="הטקסט בלבד, בלי עיצוב ובלי טבלאות",
        diag="העתקת פרטים טכניים", diag_sub="לדיווח על תקלה. בלי טקסט מהמסמך.",
        another="קריאת מסמך אחר", another_sub="חזרה למסך הראשי",
        copied="הטקסט הועתק", saved="נשמר בתיקיית ההורדות", saved_file="עלון-ספרייה.docx", open_it="פתיחה",
        p1_t="לא הצלחנו לקרוא את הקובץ", p1_b="ייתכן שהקובץ פגום או מוגן בסיסמה, או שזה סוג קובץ ש־HeOCR עדיין לא קורא.",
        p1_h="אפשר לקרוא קובצי PDF, קובצי וורד (DOCX) ותמונות.", p1_a="בחירת קובץ אחר", home_btn="חזרה למסך הראשי",
        p2_t="קובץ וורד ישן (DOC) לא נקרא בטלפון", p2_b="כדי לקרוא קובץ כזה צריך תוכנת המרה, והיא לא זמינה בטלפון.",
        p2_h="פתחו את הקובץ בוורד או באפליקציית מסמכים אחרת, שמרו אותו כ־DOCX או כ־PDF, ואז פתחו כאן את הקובץ החדש.", p2_a="פתיחת הקובץ החדש",
        p3_t="לא נמצא טקסט", p3_b="לא זיהינו טקסט בצילום הזה.",
        p3_h="כדאי לצלם באור טוב, ישר מול הדף, כשהטקסט חד וממלא את רוב התמונה.", p3_a="צילום מחדש",
        p4_t="רק חלק מהמסמך נקרא", p4_b="נקראו 2 מתוך 3 עמודים. עמוד 3 לא נקרא כי הקריאה הופסקה.",
        p4_h="אפשר לראות את מה שנקרא, או לקרוא שוב את כל המסמך.", p4_a="הצגת מה שנקרא", p4_s="קריאה מחדש של כל המסמך",
        about_title="אודות <bdi dir=\"ltr\" class=\"wm\">HeOCR</bdi>",
        about_body="HeOCR קורא טקסט עברי מצילומים, מקובצי PDF, מקובצי וורד ומתמונות, בטלפון עצמו. חינמי וקוד פתוח, ברישיון Apache 2.0.",
        privacy_h="פרטיות", privacy="לאפליקציה אין הרשאת אינטרנט, ו־Android עצמה אוכפת את זה. שום דבר שנקרא לא יוצא מהטלפון, והאפליקציה לא אוספת שום מידע.",
        accuracy_h="דיוק", accuracy="טקסט מזיהוי תווים (OCR) עלול לכלול טעויות. הדיוק של האפליקציה עדיין לא נמדד על קבוצת מבחן נפרדת.",
        version_h="גרסה", v_app="האפליקציה", licences_h="רישיונות",
        lic_models="מודלי הזיהוי", lic_models_sub="המודל העברי של HeOCR ומודלי Tesseract", lic_fonts="גופנים", lic_all="כל הרכיבים והרישיונות",
        site_sub="האתר נפתח בדפדפן, מחוץ לאפליקציה", help_h="עזרה",
        what="מה מועתק?", what_items=["גרסת האפליקציה, גרסת heocr וגרסת Tesseract", "גרסת Android ודגם הטלפון", "סוג הקובץ האחרון, מספר העמודים וזמן הקריאה", "קוד התקלה, אם הייתה"],
        what_not="לא מועתקים: שם הקובץ, הטקסט שנקרא או תמונות.",
        diag_done="הפרטים הטכניים הועתקו", diag_done_sub="בלי טקסט מהמסמך. אפשר להדביק אותם בדיווח על תקלה.",
    ),
    "en": dict(
        dir="ltr", tagline="Hebrew text out of any document",
        home_lede="Photograph a page or open a file, and get its text: to copy, to share, or to keep as a Word file.",
        home_lede_now="Photograph a page or open a file, and get its text, ready to copy.",
        capture="Take a photo", capture_sub="A letter, a page of a book, any printed page",
        open="Open a file", sample="Try a sample", about="About", back="Back", cancel="Cancel", close="Close",
        offline_a="Works fully offline:", offline_b="nothing you read leaves this phone.",
        reads_a="What it reads", reads_b="PDFs, Word files (.docx) and images. You can also share a file to HeOCR from another app.",
        file_name="עלון-ספרייה.pdf", file_meta="PDF · 3 pages · <span class=\"num\">412 KB</span>",
        shared_title="File received", shared_chip="Shared from another app", shared_sub="Reading starts right away. The file stays on this phone.", starting="Starting to read…",
        reading_title="Reading the document", page_of="Page 2 of 3", page_0="Page 1 of 3", elapsed="Time so far",
        reading_hint="The reading happens on the phone itself, so a page can take up to about 20 seconds. You can leave the app open and wait.",
        res_meta=["3 pages", "<span class=\"num\">41.2</span> s"],
        ocr_note="Text read by OCR may have mistakes. Check it before you rely on it.",
        unread="<strong>1 part wasn't read:</strong> a picture on page 3. The rest of the document was read.",
        save_word="Save as Word", copy="Copy", share="Share", more="More actions",
        sheet_title="More actions", save_txt="Save as text (.txt)", save_txt_sub="The text only, with no formatting and no tables",
        diag="Copy technical details", diag_sub="For a bug report. No text from the document.",
        another="Read another document", another_sub="Back to the first screen",
        copied="Text copied", saved="Saved to Downloads", saved_file="עלון-ספרייה.docx", open_it="Open",
        p1_t="We couldn't read this file", p1_b="It may be damaged or password-protected, or it is a kind of file HeOCR doesn't read yet.",
        p1_h="HeOCR reads PDFs, Word files (.docx) and images.", p1_a="Choose another file", home_btn="Back to the first screen",
        p2_t="Old Word files (.doc) can't be read on the phone", p2_b="Reading one needs a converter, and there isn't one on the phone.",
        p2_h="Open the file in Word or another documents app, save it as .docx or PDF, then open the new file here.", p2_a="Open the new file",
        p3_t="No text found", p3_b="We didn't find any text in this photo.",
        p3_h="Take the photo in good light, straight on, with the text sharp and filling most of the picture.", p3_a="Take the photo again",
        p4_t="Only part of the document was read", p4_b="2 of 3 pages were read. Page 3 wasn't read because the reading was stopped.",
        p4_h="You can see what was read, or read the whole document again.", p4_a="Show what was read", p4_s="Read the whole document again",
        about_title="About <bdi dir=\"ltr\" class=\"wm\">HeOCR</bdi>",
        about_body="HeOCR reads Hebrew text out of photos, PDFs, Word files and images, on the phone itself. Free and open source under the Apache License 2.0.",
        privacy_h="Privacy", privacy="The app has no internet permission, and Android itself enforces that. Nothing you read leaves this phone, and the app collects nothing.",
        accuracy_h="Accuracy", accuracy="Text read by OCR may have mistakes. The app's accuracy has not been measured on a held-out set yet.",
        version_h="Version", v_app="App", licences_h="Licences",
        lic_models="OCR models", lic_models_sub="HeOCR's Hebrew model and Tesseract's models", lic_fonts="Fonts", lic_all="All components and licences",
        site_sub="The website opens in your browser, outside the app", help_h="Help",
        what="What is copied?", what_items=["The app, heocr and Tesseract versions", "The Android version and phone model", "The last file's type, page count and reading time", "The error code, if there was one"],
        what_not="Not copied: the file name, the text that was read, or any picture.",
        diag_done="Technical details copied", diag_done_sub="No text from the document. You can paste them into a bug report.",
    ),
}

# ------------------------------------------------------------------ invented document (same markup as render.py + view.py)
DOC = '''<p class="note" dir="auto">{ocr_note}</p>
<div class="page-break" data-i18n="page_n" data-n="1">{page} 1</div>
<h1 dir="rtl" class="block ocr">ספריית השכונה: סדרי החורף</h1>
<p dir="rtl" class="block ocr">החל מהשבוע הבא הספרייה עוברת לשעות החורף. האולם הגדול ייפתח מוקדם יותר בימי שלישי, ופינת הקריאה לילדים תישאר פתוחה גם אחר הצהריים.</p>
<h2 dir="rtl" class="block ocr">מה משתנה</h2>
<p dir="rtl" class="block list-item ocr"><span class="label">1.</span> אפשר להשאיל ספרים עד רבע שעה לפני הסגירה.</p>
<p dir="rtl" class="block list-item ocr"><span class="label">2.</span> ספרים מחזירים בתיבה שליד הכניסה, בכל שעה.</p>
<p dir="rtl" class="block list-item ocr"><span class="label">3.</span> שעת הסיפור עוברת ליום רביעי אחר הצהריים.</p>
<h2 dir="rtl" class="block ocr">שעות הפתיחה</h2>
<div class="table-wrap"><table dir="rtl"><tr><td dir="auto" class="cell">יום</td><td dir="auto" class="cell">בוקר</td><td dir="auto" class="cell">אחר הצהריים</td><td dir="auto" class="cell">הערות</td></tr>
<tr><td dir="auto" class="cell">ראשון</td><td dir="auto" class="cell">9:00–12:30</td><td dir="auto" class="cell">16:00–19:00</td><td dir="auto" class="cell">האולם הגדול בלבד</td></tr>
<tr><td dir="auto" class="cell">שלישי</td><td dir="auto" class="cell">8:30–12:30</td><td dir="auto" class="cell">16:00–20:00</td><td dir="auto" class="cell">כולל פינת הילדים</td></tr>
<tr><td dir="auto" class="cell">רביעי</td><td dir="auto" class="cell">סגור</td><td dir="auto" class="cell flagged">16:00–19:00</td><td dir="auto" class="cell">שעת סיפור ב־17:00</td></tr>
<tr><td dir="auto" class="cell">שישי</td><td dir="auto" class="cell">9:00–12:00</td><td dir="auto" class="cell">סגור</td><td dir="auto" class="cell"></td></tr></table></div>
<div class="page-break" data-i18n="page_n" data-n="2">{page} 2</div>
<h2 dir="rtl" class="block ocr">השאלה והחזרה</h2>
<p dir="rtl" class="block ocr">כל קוראת וכל קורא יכולים להשאיל עד ארבעה ספרים לשלושה שבועות.<sup class="note-id">1</sup> את ההשאלה אפשר להאריך פעם אחת, כל עוד אף אחד לא מחכה לספר.</p>
<p dir="rtl" class="block list-item ocr"><span class="label">א.</span> ספרי עיון: עד שבועיים.</p>
<p dir="rtl" class="block list-item ocr"><span class="label">ב.</span> ספרי ילדים: עד שישה ספרים בכל פעם.</p>
<div class="page-break" data-i18n="page_n" data-n="3">{page} 3</div>
<h2 dir="rtl" class="block ocr">איך מגיעים</h2>
<p class="figure" data-i18n="figure_not_read">{figure}</p>
<p dir="rtl" class="block ocr">הכניסה לספרייה היא מהחצר הפנימית. לשאלות אפשר לפנות לדלפק בשעות הפתיחה.</p>
<h2 class="section" data-i18n="section_footnote">{footnotes}</h2>
<p dir="rtl" class="block ocr"><sup class="note-id">1</sup> בחופשות ייתכנו שינויים; הודעה תיתלה על דלת הספרייה.</p>
<h2 class="section" data-i18n="section_header">{headers}</h2>
<p dir="rtl" class="block ocr">ספריית השכונה · עלון חורף</p>
<h2 class="section" data-i18n="section_footer">{footers}</h2>
<p dir="rtl" class="block ocr">עמוד 1 מתוך 3</p>'''
DOC_L = {"he": dict(page="עמוד", figure="[תמונה שלא נקראה]", footnotes="הערות שוליים", headers="כותרות עליונות", footers="כותרות תחתונות"),
         "en": dict(page="Page", figure="[picture not read]", footnotes="Footnotes", headers="Headers", footers="Footers")}


# ------------------------------------------------------------------ pieces
def appbar_home(t):
    return (f'<header class="appbar"><a class="lockup" href="heocr:home" aria-label="HeOCR">{MARK}<span class="ltr">He<b>OCR</b></span></a>'
            f'<span class="spacer"></span><a class="iconbtn" href="heocr:about" aria-label="{t["about"]}">{ico("info")}</a></header>')


def appbar_back(t, title, file=False, about=True):
    end = f'<a class="iconbtn" href="heocr:about" aria-label="{t["about"]}">{ico("info")}</a>' if about else ''
    cls = "title fname" if file else "title"
    return (f'<header class="appbar"><a class="iconbtn" href="heocr:home" aria-label="{t["back"]}">{ico("back")}</a>'
            f'<span class="{cls}"><bdi>{title}</bdi></span>{end}</header>')


def file_card(t, chip=""):
    return (f'<div class="file">{ico("text-file")}<div><div class="name" dir="auto">{t["file_name"]}</div>'
            f'<div class="meta">{t["file_meta"]}</div>{chip}</div></div>')


def home(t, lang, lede="home_lede"):
    return appbar_home(t) + f'''
<main class="screen">
<div class="band"><h1><span class="bb">{t["tagline"]}</span></h1><p class="lede">{t[lede]}</p></div>
<a class="hero capture" href="heocr:photo">{ico("camera", "lg")}<strong>{t["capture"]}</strong><span>{t["capture_sub"]}</span></a>
<div class="ways"><a class="btn secondary" href="heocr:open">{ico("open-file")}{t["open"]}</a><a class="btn secondary" href="heocr:sample">{ico("sample")}{t["sample"]}</a></div>
<div class="facts">
<div class="fact">{ico("private")}<p><strong>{t["offline_a"]}</strong><span>{t["offline_b"]}</span></p></div>
<div class="fact">{ico("text-file")}<p><strong>{t["reads_a"]}</strong><span>{t["reads_b"]}</span></p></div>
</div>
</main>'''


def scan(lines_read=True):
    lines = "<i></i>" * 9
    return f'<div class="hero scan" aria-hidden="true"><div class="sheet-lines">{lines}<div class="read">{lines}</div><div class="cursor"></div></div></div>'


def shared(t, lang):
    chip = f'<div class="chips" style="margin-top: 6px"><span class="chip ok">{ico("check", "sm")}{t["shared_chip"]}</span></div>'
    return appbar_home(t) + f'''
<main class="screen">
<h2>{t["shared_title"]}</h2>
{file_card(t, chip)}
<p class="muted">{t["shared_sub"]}</p>
{scan()}
<div class="progress" role="status"><div class="count"><strong>{t["starting"]}</strong><span class="num" aria-label="{t["elapsed"]}">0:01</span></div>
<div class="pages"><i class="now"></i><i></i><i></i></div></div>
</main>
<footer class="actionbar"><a class="btn secondary" href="heocr:cancel">{ico("close")}{t["cancel"]}</a></footer>'''


def reading(t, lang):
    return appbar_home(t) + f'''
<main class="screen">
<h2>{t["reading_title"]}</h2>
{file_card(t)}
{scan()}
<div class="progress" role="status"><div class="count"><strong>{t["page_of"]}</strong><span class="num" aria-label="{t["elapsed"]}">0:24</span></div>
<div class="pages"><i class="done"></i><i class="now"></i><i></i></div></div>
<p class="muted" style="font-size: 14.5px">{t["reading_hint"]}</p>
</main>
<footer class="actionbar"><a class="btn secondary" href="heocr:cancel">{ico("close")}{t["cancel"]}</a></footer>'''


def result(t, lang, extra="", copy_only=False, open_sheet=False):
    chips = "".join(f'<span class="chip">{c}</span>' for c in t["res_meta"]) + '<span class="chip">OCR</span>'
    doc = DOC.format(ocr_note=t["ocr_note"], **DOC_L[lang])
    if copy_only:
        bar = f'''<footer class="actionbar"><a class="btn" href="heocr:copy">{ico("copy")}{t["copy"]}</a></footer>'''
    else:
        bar = f'''<footer class="actionbar"><a class="btn" href="heocr:save-docx">{ico("word-doc")}{t["save_word"]}</a>
<a class="iconbtn framed" href="heocr:copy" aria-label="{t["copy"]}">{ico("copy")}</a>
<a class="iconbtn framed" href="heocr:share" aria-label="{t["share"]}">{ico("share")}</a>
<a class="iconbtn framed" href="heocr:more" aria-label="{t["more"]}">{ico("more")}</a></footer>''' + more_sheet(t, open_sheet)
    return appbar_back(t, t["file_name"], file=True) + f'''
<main class="screen result">
<div class="chips">{chips}</div>
<div class="notice">{ico("warning", "sm")}<p>{t["unread"]}</p></div>
<article class="doc" dir="rtl">
{doc}
</article>
</main>
{bar}{extra}'''


def result_saved(t, lang):
    toast = (f'<div class="toast" role="status">{ico("check")}<div>{t["saved"]}<small dir="auto">{t["saved_file"]}</small></div>'
             f'<a href="heocr:open-saved">{t["open_it"]}</a></div>')
    return result(t, lang, toast)


def result_copied(t, lang):
    return result(t, lang, f'<div class="toast" role="status">{ico("check")}<div>{t["copied"]}</div></div>')


def more_sheet(t, open_=False):
    def row(icon, a, b, href):
        return f'<a class="row" href="heocr:{href}">{ico(icon)}<div><strong>{a}</strong><span>{b}</span></div></a>'
    cls = "sheet open" if open_ else "sheet"
    return (f'<section class="{cls}" id="more" role="dialog" aria-label="{t["sheet_title"]}">'
            f'<div class="grip"></div><h2>{t["sheet_title"]}</h2>'
            + row("text-file", t["save_txt"], t["save_txt_sub"], "save-txt")
            + row("diagnostics", t["diag"], t["diag_sub"], "diagnostics")
            + row("back", t["another"], t["another_sub"], "home") + '</section>'
            f'<a class="scrim" href="heocr:dismiss" aria-label="{t["close"]}"></a>')


def result_more(t, lang):
    return result(t, lang, open_sheet=True)


def problem(t, lang, n, icon, primary_icon, secondary=None):
    sec = secondary or (t["home_btn"], "home", None)
    sec_html = f'<a class="btn secondary block" href="heocr:{sec[1]}">{ico(sec[2]) if sec[2] else ""}{sec[0]}</a>'
    return appbar_home(t) + f'''
<main class="screen">
<div class="problem">
<div class="mark">{ico(icon)}</div>
<h2>{t[f"p{n}_t"]}</h2>
<p>{t[f"p{n}_b"]}</p>
<p class="hint">{t[f"p{n}_h"]}</p>
<div class="stack"><a class="btn block" href="heocr:next">{ico(primary_icon)}{t[f"p{n}_a"]}</a>{sec_html}</div>
</div>
</main>'''


def about(t, lang, extra=""):
    def lic(a, b, sub=""):
        s = f'<span>{sub}</span>' if sub else ''
        return f'<div class="row"><div><strong>{a}</strong>{s}</div><span class="end"><bdi dir="ltr">{b}</bdi></span></div>'
    items = "".join(f"<li>{x}</li>" for x in t["what_items"])
    return appbar_back(t, t["about"], about=False) + f'''
<main class="screen">
<div class="band"><h1><span class="bb">{t["about_title"]}</span></h1><p class="lede">{t["about_body"]}</p></div>
<p class="sectionhead">{t["privacy_h"]}</p>
<div class="fact" style="border: 0; padding: 0">{ico("private")}<p>{t["privacy"]}</p></div>
<p class="sectionhead">{t["accuracy_h"]}</p>
<p>{t["accuracy"]}</p>
<p class="sectionhead">{t["version_h"]}</p>
<dl class="kv"><dt>{t["v_app"]}</dt><dd><bdi dir="ltr">0.1.0</bdi></dd><dt><bdi dir="ltr">heocr</bdi></dt><dd><bdi dir="ltr">0.2.0rc1</bdi></dd><dt><bdi dir="ltr">Tesseract</bdi></dt><dd><bdi dir="ltr">5.5.3</bdi></dd></dl>
<p class="sectionhead">{t["licences_h"]}</p>
<div class="rows">
{lic('<bdi dir="ltr">heocr</bdi>', "Apache-2.0")}
{lic('<bdi dir="ltr">Tesseract OCR</bdi>', "Apache-2.0")}
{lic(t["lic_models"], "Apache-2.0", t["lic_models_sub"])}
{lic(t["lic_fonts"], "OFL 1.1", '<bdi dir="ltr">Noto Sans Hebrew, JetBrains Mono</bdi>')}
<a class="row" href="heocr:licences"><div><strong>{t["lic_all"]}</strong></div>{ico("chevron", "sm")}</a>
</div>
<p class="sectionhead">{t["help_h"]}</p>
<div class="rows">
<a class="row" href="https://heocr.github.io">{ico("external")}<div><strong><bdi dir="ltr">heocr.github.io</bdi></strong><span>{t["site_sub"]}</span></div></a>
<a class="row" href="heocr:diagnostics">{ico("diagnostics")}<div><strong>{t["diag"]}</strong><span>{t["diag_sub"]}</span></div></a>
</div>
<details class="what"><summary>{t["what"]}</summary><ul>{items}</ul><p>{t["what_not"]}</p></details>
</main>{extra}'''


def about_copied(t, lang):
    toast = f'<div class="toast low" role="status">{ico("check")}<div>{t["diag_done"]}<small>{t["diag_done_sub"]}</small></div></div>'
    return about(t, lang, toast).replace('<details class="what">', '<details class="what" open>').replace('<main class="screen">', '<main class="screen with-toast">')


SCREENS = {
    "01-home": home, "01b-home-copy-only": lambda t, l: home(t, l, "home_lede_now"), "02-shared-file": shared, "03-reading": reading, "04-result": result,
    "04b-result-copy-only": lambda t, l: result(t, l, copy_only=True),
    "05-result-saved": result_saved, "05b-result-copied": result_copied, "06-result-more": result_more,
    "07-problem-unreadable": lambda t, l: problem(t, l, 1, "warning", "open-file"),
    "08-problem-needs-converter": lambda t, l: problem(t, l, 2, "word-doc", "open-file"),
    "09-problem-no-text": lambda t, l: problem(t, l, 3, "camera", "camera", (S[l]["open"], "open", "open-file")),
    "10-problem-partial": lambda t, l: problem(t, l, 4, "warning", "text-file", (S[l]["p4_s"], "retry", "retry")),
    "11-about": about, "12-about-diagnostics-copied": about_copied,
}
TITLES = {"01-home": "Home", "01b-home-copy-only": "Home: until saving ships", "02-shared-file": "Received a shared file", "03-reading": "Reading in progress", "04-result": "Result",
          "04b-result-copy-only": "Result: until saving and sharing ship", "05-result-saved": "Result: saved as Word", "05b-result-copied": "Result: text copied", "06-result-more": "Result: more actions", "07-problem-unreadable": "Problem: file could not be read",
          "08-problem-needs-converter": "Problem: needs a converter", "09-problem-no-text": "Problem: no text found", "10-problem-partial": "Problem: partly read",
          "11-about": "About", "12-about-diagnostics-copied": "About: diagnostics copied"}


NAV = {"photo": "03-reading.html", "open": "03-reading.html", "sample": "03-reading.html", "retry": "03-reading.html",
       "cancel": "01-home.html", "home": "01-home.html", "about": "11-about.html", "save-docx": "05-result-saved.html",
       "copy": "05b-result-copied.html", "more": "#more", "diagnostics": "12-about-diagnostics-copied.html"}


def page(name, lang, body):
    t = S[lang]
    body = re.sub(r'href="heocr:([a-z-]+)"', lambda m: f'href="{NAV.get(m.group(1), "#_")}" role="button" data-action="heocr:{m.group(1)}"', body)
    body = body.replace('href="https://heocr.github.io"', 'href="#_" data-action="https://heocr.github.io"')
    return f'''<!doctype html>
<html lang="{lang}" dir="{t["dir"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' 'unsafe-inline'; font-src 'self'">
<title>HeOCR Android · {TITLES[name]} · {lang}</title>
<link rel="stylesheet" href="../../css/tokens.css">
<link rel="stylesheet" href="../../css/fonts.css">
<link rel="stylesheet" href="../../css/result.css">
<link rel="stylesheet" href="../../css/app.css">
</head>
<body class="app">
{body}
</body>
</html>
'''


if __name__ == "__main__":
    write_icons()
    jobs = []
    for lang in ("he", "en"):
        d = OUT / "mockups" / lang
        d.mkdir(parents=True, exist_ok=True)
        for name, fn in SCREENS.items():
            (d / f"{name}.html").write_text(page(name, lang, fn(S[lang], lang)), encoding="utf-8")
            jobs.append({"name": name, "lang": lang})
    (HERE / "screen_jobs.json").write_text(json.dumps(jobs))
    reused = ["tagline", "capture", "open", "sample", "about", "cancel", "close", "copy", "offline_a", "offline_b", "ocr_note"]
    strings = {"_note": "Strings used in the mockups. Keys listed in _already_reviewed reuse wording that is already in "
               "heocr_mobile/app.py or heocr_desktop/i18n.py; every other Hebrew string is new and needs the maintainer's review. "
               "Values may contain inline markup (strong, span.num, bdi).",
               "_already_reviewed": reused}
    for lang in ("he", "en"):
        strings[lang] = {k: v for k, v in S[lang].items() if k != "dir"}
        strings[lang]["document_labels"] = DOC_L[lang]
    d = OUT / "strings"
    d.mkdir(exist_ok=True)
    (d / "strings.json").write_text(json.dumps(strings, ensure_ascii=False, indent=2), encoding="utf-8")
    # the result view on its own: today's view.py page with only the drop-in stylesheet
    for lang in ("he", "en"):
        t = S[lang]
        (OUT / f"mockups/{lang}/result-view-drop-in.html").write_text(f'''<!doctype html>
<html lang="{lang}" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' 'unsafe-inline'; font-src data:">
<title>HeOCR Android · result view with the drop-in stylesheet · {lang}</title>
<link rel="stylesheet" href="../../css/result-standalone.css">
</head>
<body class="doc">
{DOC.format(ocr_note=t["ocr_note"], **DOC_L[lang])}
</body>
</html>
''', encoding="utf-8")
        jobs.append({"name": "result-view-drop-in", "lang": lang})
    (HERE / "screen_jobs.json").write_text(json.dumps(jobs))
    # mockup index
    rows = "".join(f'<tr><td>{TITLES[n]}</td><td><a href="he/{n}.html">עברית</a></td><td><a href="en/{n}.html">English</a></td></tr>' for n in SCREENS)
    (OUT / "mockups/index.html").write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HeOCR Android mockups</title><link rel="stylesheet" href="../css/tokens.css"><link rel="stylesheet" href="../css/fonts.css">
<style>body{{margin:0;padding:24px;background:var(--bg);color:var(--text);font:400 15px/1.5 var(--font-body);max-width:640px}}
h1{{font:700 22px/1.2 var(--font-mono)}}table{{border-collapse:collapse;width:100%}}td{{padding:10px 8px;border-bottom:1px solid var(--line)}}a{{color:var(--accent)}}p{{color:var(--muted)}}</style></head>
<body><h1>HeOCR Android mockups</h1>
<p>Open a screen in a narrow window (412 or 360 px wide), or in the browser's device mode. The pages follow the system light or dark setting.
Links are wired so you can click through; the action the app must handle is in each link's <code>data-action</code>. There is no script in any page.</p>
<table>{rows}</table></body></html>''', encoding="utf-8")
    print("screens", len(jobs), "icons", len(ICONS))
