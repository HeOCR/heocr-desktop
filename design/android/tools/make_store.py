"""HeOCR Android store graphics: Play feature graphic (1024x500) and framed phone screenshots (1080x2400),
English and Hebrew. Writes HTML compositions to store_build/ and a job list for store.js, which captures
the mockup screens and renders the PNGs into the fastlane tree."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
FASTLANE = OUT / "store/fastlane/metadata/android"
BUILD = HERE / "store_build"
LOCALE = {"en": "en-US", "he": "iw-IL"}

SHOTS = [  # (mockup, theme, scroll target selector or None, caption, sub)
    ("01b-home-copy-only", "light", None, {"he": ("טקסט עברי מכל מסמך", "מצלמים דף או פותחים קובץ"), "en": ("Hebrew text out of any document", "Photograph a page or open a file")}),
    ("03-reading", "light", None, {"he": ("הקריאה נעשית בטלפון עצמו", "בלי אינטרנט, עמוד אחרי עמוד"), "en": ("Read on the phone itself", "No internet, page by page")}),
    ("04b-result-copy-only", "light", None, {"he": ("הטקסט, בסדר הקריאה", "כותרות, פסקאות ורשימות, מימין לשמאל"), "en": ("The text, in reading order", "Headings, paragraphs and lists, right to left")}),
    ("04b-result-copy-only", "light", ".table-wrap", {"he": ("טבלאות מוצגות כטבלאות", "טבלה רחבה נגללת לצדדים"), "en": ("Tables are shown as tables", "A wide table scrolls sideways")}),
    ("11-about", "light", None, {"he": ("שום דבר לא יוצא מהטלפון", "לאפליקציה אין הרשאת אינטרנט"), "en": ("Nothing leaves the phone", "The app has no internet permission")}),
    ("04b-result-copy-only", "night", None, {"he": ("גם במצב כהה", "לפי ההגדרה של הטלפון"), "en": ("In dark mode too", "Follows the phone's setting")}),
]

MARK = ('<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="7" y="7" width="34" height="34" fill="none" stroke="var(--accent)" stroke-width="2"/>'
        + "".join(f'<rect x="{x}" y="{y}" width="6" height="6" fill="var(--accent)"/>' for x, y in ((4, 4), (38, 4), (4, 38), (38, 38)))
        + '<path d="M16 18H32V32.5M16 24.5V32.5" fill="none" stroke="var(--text)" stroke-width="4.5"/></svg>')
CSS = OUT.as_uri() + "/css"
HEAD = f'''<meta charset="utf-8"><link rel="stylesheet" href="{CSS}/tokens.css"><link rel="stylesheet" href="{CSS}/fonts.css">
<style>
*{{box-sizing:border-box}} html,body{{margin:0}}
body{{background:var(--bg);color:var(--text);font-family:var(--font-body);overflow:hidden}}
.grid{{background:linear-gradient(var(--grid) 2px,transparent 2px) 0 0/100% var(--g),linear-gradient(90deg,var(--grid) 2px,transparent 2px) 0 0/var(--g) 100% var(--bg)}}
.bb{{position:relative;display:inline-block;outline:var(--o) solid var(--accent);outline-offset:var(--off)}}
.bb::after{{content:"";position:absolute;inset:calc(-1*(var(--off) + var(--o)/2 + var(--h)/2));
 background:linear-gradient(var(--accent) 0 0) 0 0/var(--h) var(--h) no-repeat,linear-gradient(var(--accent) 0 0) 100% 0/var(--h) var(--h) no-repeat,
 linear-gradient(var(--accent) 0 0) 0 100%/var(--h) var(--h) no-repeat,linear-gradient(var(--accent) 0 0) 100% 100%/var(--h) var(--h) no-repeat}}
.lock{{display:inline-flex;align-items:center;direction:ltr;font-family:var(--font-mono);font-weight:700;letter-spacing:-.03em}}
.lock b{{color:var(--accent)}}
</style>'''


def shot_html(lang, cap, sub, raw, theme):
    d = "rtl" if lang == "he" else "ltr"
    t = "dark" if theme == "night" else "light"
    return f'''<!doctype html><html lang="{lang}" dir="{d}" data-theme="{t}"><head>{HEAD}<style>
body{{width:1080px;height:2400px;--g:60px;--o:4px;--off:18px;--h:20px}}
.top{{height:470px;padding:96px 84px 0;display:flex;flex-direction:column;gap:44px;align-items:flex-start}}
h1{{margin:0;font:700 64px/1.2 var(--font-body);max-width:900px}}
html[lang=en] h1{{font-family:var(--font-display);letter-spacing:-.03em;font-size:56px}}
p{{margin:0;font-size:38px;line-height:1.3;color:var(--muted)}}
.phone{{position:absolute;left:122px;top:478px;width:836px;height:1842px;border:6px solid var(--text);border-radius:8px;overflow:hidden;background:var(--bg)}}
.phone img{{display:block;width:824px;height:1830px}}
</style></head><body class="grid"><div class="top"><h1><span class="bb">{cap}</span></h1><p>{sub}</p></div>
<div class="phone"><img src="{raw.as_uri()}" alt=""></div></body></html>'''


FEATURE = {"he": ("טקסט עברי מכל מסמך", "מצילומים, מקובצי PDF ומקובצי וורד.", "עובד במלואו בלי אינטרנט."),
           "en": ("Hebrew text out of any document", "From photos, PDFs and Word files.", "Works fully offline.")}


def feature_html(lang):
    d = "rtl" if lang == "he" else "ltr"
    h, a, b = FEATURE[lang]
    lines = "".join(f'<i style="width:{w}%"></i>' for w in (62, 100, 100, 78, 100, 100, 54, 100, 70))
    return f'''<!doctype html><html lang="{lang}" dir="{d}" data-theme="light"><head>{HEAD}<style>
body{{width:1024px;height:500px;--g:32px;--o:3px;--off:12px;--h:13px;display:flex;align-items:center;gap:56px;padding:0 64px}}
.txt{{flex:1;display:flex;flex-direction:column;align-items:flex-start;gap:30px}}
.lock{{font-size:34px;gap:14px}} .lock svg{{width:52px;height:52px}}
h1{{margin:6px 0 0;font:700 46px/1.2 var(--font-body)}}
html[lang=en] h1{{font-family:var(--font-display);letter-spacing:-.03em;font-size:36px;max-width:500px}}
p{{margin:0;font-size:23px;line-height:1.45;color:var(--muted)}} p strong{{color:var(--text);display:block}}
.page{{flex:none;width:300px;height:372px;border:2px solid var(--line-strong);background:var(--bg);padding:38px 34px;position:relative}}
.page i{{display:block;height:11px;margin-bottom:22px;background:var(--line)}} .page i:nth-child(-n+4){{background:var(--muted)}}
.cur{{position:absolute;inset-inline:22px;top:163px;height:33px;border:3px solid var(--accent);background:color-mix(in srgb,var(--accent) 8%,transparent)}}
</style></head><body class="grid"><div class="txt"><span class="lock">{MARK}<span>He<b>OCR</b></span></span>
<h1><span class="bb">{h}</span></h1><p>{a}<strong>{b}</strong></p></div>
<div class="page">{lines}<div class="cur"></div></div></body></html>'''


if __name__ == "__main__":
    BUILD.mkdir(exist_ok=True)
    caps, comps = [], []
    for lang in ("en", "he"):
        img = FASTLANE / LOCALE[lang] / "images"
        f = BUILD / f"feature-{lang}.html"
        f.write_text(feature_html(lang), encoding="utf-8")
        comps.append(dict(html=str(f), out=str(img / "featureGraphic.png"), w=1024, h=500))
        for k, (name, theme, sel, text) in enumerate(SHOTS, 1):
            raw = BUILD / f"raw-{lang}-{k}.png"
            caps.append(dict(page=str(OUT / "mockups" / lang / f"{name}.html"), theme=theme, sel=sel, out=str(raw)))
            f = BUILD / f"shot-{lang}-{k}.html"
            f.write_text(shot_html(lang, *text[lang], raw, theme), encoding="utf-8")
            comps.append(dict(html=str(f), out=str(img / "phoneScreenshots" / f"{k}.png"), w=1080, h=2400))
    (HERE / "store_jobs.json").write_text(json.dumps(dict(captures=caps, compositions=comps)))
    print(len(caps), "captures", len(comps), "compositions")
