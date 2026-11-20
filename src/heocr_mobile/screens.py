"""Every screen of the Android app as one self-contained HTML page (design/android, SPEC sections 7 to 9).

The markup is the design's (``design/android/tools/make_screens.py``), filled with the app's own values.
Strings come from ``ui_strings.json``, a copy of ``design/android/strings/strings.json``: the maintainer
reviewed and approved every Hebrew string in it on 2026-11-19. Counts, times and versions reuse the
desktop's reviewed strings (``heocr_desktop.i18n``), and file names, sizes and versions are data.

Every action is a link with an app address (``heocr:open``, ``heocr:copy``…). The app intercepts the
navigation and runs the action (``heocr_mobile.app.HeOCR.navigate``). The page has no script and loads
nothing: the stylesheet carries the two typefaces as data URIs (``font-src data:``).
"""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

from heocr_desktop import render

HERE = Path(__file__).resolve().parent
# design/android/css/app-standalone.css: tokens, the embedded fonts, the result view and every screen.
CSS = (HERE / "app.css").read_text("utf-8")
CSP = "default-src 'none'; style-src 'unsafe-inline'; font-src data:"
UI = json.loads((HERE / "ui_strings.json").read_text("utf-8"))

# ------------------------------------------------------------------ icons (design/android/icons/in-app)
ICONS = {
    "camera": ('<path d="M3 8h4l1.5-3h7L17 8h4v11H3z"/><rect x="9" y="10.5" width="6" height="6"/>', False),
    "open-file": ('<path d="M3 5h7l2 3h9v11H3z"/>', False),
    "sample": ('<path d="M5 3h14v18H5z"/><rect x="8" y="7" width="8" height="5"/><path d="M8 16h8"/>', False),
    "copy": ('<path d="M9 9h11v11H9z"/><path d="M15 9V4H4v11h5"/>', False),
    "share": ('<path d="M8 11l8-4M8 13l8 4"/><rect x="3" y="9.5" width="5" height="5"/><rect x="16" y="3.5" width="5" height="5"/><rect x="16" y="15.5" width="5" height="5"/>', False),
    "word-doc": ('<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M8.5 11.5l1.3 5.5 2.2-4 2.2 4 1.3-5.5"/>', False),
    "text-file": ('<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 12h6M9 15h6M9 18h3"/>', False),
    "info": ('<rect x="3.5" y="3.5" width="17" height="17"/><path d="M12 11v6"/><path d="M12 7v1"/>', False),
    "close": ('<path d="M6 6l12 12M18 6L6 18"/>', False),
    "warning": ('<path d="M12 3.5L21.5 20h-19z"/><path d="M12 10v4.5"/><path d="M12 17v.5"/>', False),
    "check": ('<path d="M4.5 12.5l5 5L19.5 7"/>', False),
    "diagnostics": ('<path d="M9 5H5v16h14V5h-4"/><rect x="9" y="3" width="6" height="4"/><path d="M8 14h2.5l1.5-3 2 6 1.5-3H16"/>', False),
    "back": ('<path d="M20 12H5M11 6l-6 6 6 6"/>', True),
    "more": ('<rect x="10.5" y="4" width="3" height="3" class="f"/><rect x="10.5" y="10.5" width="3" height="3" class="f"/><rect x="10.5" y="17" width="3" height="3" class="f"/>', False),
    "external": ('<path d="M11 5H5v14h14v-6"/><path d="M14 4h6v6M20 4l-9 9"/>', True),
    "private": ('<rect x="5" y="10" width="14" height="10"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>', False),
    "image-file": ('<rect x="3.5" y="4.5" width="17" height="15"/><path d="M3.5 16l5-5 4 4 3-3 5 5"/><rect x="14" y="7.5" width="3" height="3"/>', False),
    "chevron": ('<path d="M9 5l7 7-7 7"/>', True),
    "retry": ('<path d="M19 12a7 7 0 1 1-2.05-4.95"/><path d="M19 4v5h-5"/>', False),
}

MARK = ('<svg viewBox="0 0 48 48" aria-hidden="true"><rect x="7" y="7" width="34" height="34" class="lg-box"/>'
        + "".join(f'<rect x="{x}" y="{y}" width="6" height="6" class="lg-h"/>' for x, y in ((4, 4), (38, 4), (4, 38), (38, 38)))
        + '<path d="M16 18H32V32.5M16 24.5V32.5" class="lg-ink"/></svg>')

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".gif"}


def ico(name: str, cls: str = "") -> str:
    inner, flip = ICONS[name]
    c = "ico" + (" flip" if flip else "") + (" " + cls if cls else "")
    return f'<svg class="{c}" viewBox="0 0 24 24" aria-hidden="true">{inner}</svg>'


def strings(lang: str) -> dict:
    """The approved interface strings for ``he`` or ``en``. Values may hold inline markup (strong, bdi)."""
    return UI[lang]


# The app's screens never zoom (one CSS pixel per dp, whatever the WebView's own heuristics decide); the
# reading itself can be pinch-zoomed up to five times, never below its width.
VIEWPORT_FIXED = "width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1, user-scalable=no"
VIEWPORT_ZOOM = "width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=5"


def html(lang: str, body: str, zoom: bool = False) -> str:
    direction = "rtl" if lang == "he" else "ltr"
    return (
        f'<!doctype html><html lang="{lang}" dir="{direction}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="{VIEWPORT_ZOOM if zoom else VIEWPORT_FIXED}">'
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'
        f'<style>{CSS}</style></head><body class="app">{body}</body></html>'
    )


# ------------------------------------------------------------------ pieces
def appbar_home(t: dict) -> str:
    return (f'<header class="appbar"><a class="lockup" href="heocr:home" role="button" aria-label="HeOCR">{MARK}<span class="ltr">He<b>OCR</b></span></a>'
            f'<span class="spacer"></span><a class="iconbtn" href="heocr:about" role="button" aria-label="{t["about"]}">{ico("info")}</a></header>')


def appbar_back(t: dict, title: str, file: bool = False, about: bool = True, back: str = "home") -> str:
    end = f'<a class="iconbtn" href="heocr:about" role="button" aria-label="{t["about"]}">{ico("info")}</a>' if about else ""
    cls = "title fname" if file else "title"
    return (f'<header class="appbar"><a class="iconbtn" href="heocr:{back}" role="button" aria-label="{t["back"]}">{ico("back")}</a>'
            f'<span class="{cls}"><bdi>{title}</bdi></span>{end}</header>')


def size_text(size: int | None) -> str:
    if not size:
        return ""
    if size < 1024 * 1024:
        return f"{max(1, round(size / 1024))} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def file_card(name: str, size: int | None, chip: str = "") -> str:
    suffix = Path(name).suffix.lower()
    icon = "image-file" if suffix in IMAGE_SUFFIXES else "text-file"
    meta = " · ".join(x for x in (escape(suffix.lstrip(".").upper()), f'<span class="num">{size_text(size)}</span>' if size else "") if x)
    return (f'<div class="file">{ico(icon)}<div><div class="name" dir="auto">{escape(name)}</div>'
            f'<div class="meta"><bdi dir="ltr">{meta}</bdi></div>{chip}</div></div>')


def scan() -> str:
    lines = "<i></i>" * 9
    return f'<div class="hero scan" aria-hidden="true"><div class="sheet-lines">{lines}<div class="read">{lines}</div><div class="cursor"></div></div></div>'


def segments(done: int, total: int) -> str:
    return "".join('<i class="done"></i>' if i < done else '<i class="now"></i>' if i == done else "<i></i>" for i in range(max(total, 1)))


def elapsed_text(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


# ------------------------------------------------------------------ screens
def home(t: dict, lang: str, word: bool) -> str:
    """1 Home. The lede promises a Word file only when the app can write one."""
    lede = t["home_lede"] if word else t["home_lede_now"]
    return html(lang, appbar_home(t) + f'''
<main class="screen">
<div class="band"><h1><span class="bb">{t["tagline"]}</span></h1><p class="lede">{lede}</p></div>
<a class="hero capture" href="heocr:photo" role="button">{ico("camera", "lg")}<strong>{t["capture"]}</strong><span>{t["capture_sub"]}</span></a>
<div class="ways"><a class="btn secondary" href="heocr:open" role="button">{ico("open-file")}{t["open"]}</a><a class="btn secondary" href="heocr:sample" role="button">{ico("sample")}{t["sample"]}</a></div>
<div class="facts">
<div class="fact">{ico("private")}<p><strong>{t["offline_a"]}</strong><span>{t["offline_b"]}</span></p></div>
<div class="fact">{ico("text-file")}<p><strong>{t["reads_a"]}</strong><span>{t["reads_b"]}</span></p></div>
</div>
</main>''')


def reading(t: dict, d: dict, lang: str, name: str, size: int | None, shared: bool, done: int = 0, total: int = 0, seconds: float = 0) -> str:
    """2 Received a shared file, or 3 Reading. ``total`` is 0 until heocr knows the page count.

    The count and the segments change by re-rendering at each page; the elapsed time is set from
    outside (``#elapsed``, ``app.HeOCR.tick``)."""
    if total > 1:
        count = d["page_of"].format(done=done + 1, total=total)
    elif shared and total == 0:
        count = t["starting"]
    else:
        count = d["reading"]
    chip = f'<div class="chips" style="margin-top: 6px"><span class="chip ok">{ico("check", "sm")}{t["shared_chip"]}</span></div>' if shared else ""
    title = t["shared_title"] if shared else t["reading_title"]
    sub = f'<p class="muted">{t["shared_sub"]}</p>' if shared else ""
    hint = "" if shared else f'<p class="muted" style="font-size: 14.5px">{t["reading_hint"]}</p>'
    return html(lang, appbar_home(t) + f'''
<main class="screen">
<h2>{title}</h2>
{file_card(name, size, chip)}
{sub}
{scan()}
<div class="progress" role="status"><div class="count"><strong>{escape(count)}</strong><span class="num" id="elapsed" aria-label="{t["elapsed"]}">{elapsed_text(seconds)}</span></div>
<div class="pages">{segments(done, total)}</div></div>
{hint}
</main>
<footer class="actionbar"><a class="btn secondary" href="heocr:cancel" role="button">{ico("close")}{t["cancel"]}</a></footer>''')


_PLACEHOLDER = re.compile(r'(<(\w+)[^>]*?data-i18n="(\w+)"(?: data-n="(\d+)")?[^>]*>)(</\2>)')


def document(doc, d: dict, ocr_note: str | None) -> str:
    """The rendered document, with the desktop's ``data-i18n`` labels filled in."""
    body = render.document_html(doc)

    def fill(match: re.Match) -> str:
        text = d.get(match.group(3), "")
        if match.group(4):
            text = text.format(n=match.group(4))
        return f"{match.group(1)}{escape(text)}{match.group(5)}"

    body = _PLACEHOLDER.sub(fill, body)
    note = f'<p class="note" dir="auto">{escape(ocr_note)}</p>' if ocr_note else ""
    return f'<article class="doc" dir="{render.document_direction(doc.text)}">{note}{body}</article>'


def more_sheet(t: dict, formats: list[str]) -> str:
    def row(icon, a, b, href):
        return f'<a class="row" href="heocr:{href}" role="button">{ico(icon)}<div><strong>{a}</strong><span>{b}</span></div></a>'

    rows = row("text-file", t["save_txt"], t["save_txt_sub"], "save-txt") if "txt" in formats else ""
    return (f'<section class="sheet" id="more" role="dialog" aria-label="{t["sheet_title"]}">'
            f'<div class="grip"></div><h2>{t["sheet_title"]}</h2>'
            + rows
            + row("diagnostics", t["diag"], t["diag_sub"], "diagnostics")
            + row("back", t["another"], t["another_sub"], "home") + "</section>"
            f'<a class="scrim" href="heocr:dismiss" role="button" aria-label="{t["close"]}"></a>')


def result(t: dict, d: dict, lang: str, doc, name: str, pages: int, seconds: float, ocr: bool, formats: list[str]) -> str:
    """4 Result: chips, the document, the action bar and the (hidden) More sheet.

    Save as Word leads when heocr can write Word files; until then Copy is the primary button
    (the design's interim bar, 04b). Share arrives with its own change (design step 3)."""
    chips = []
    if pages > 1:
        chips.append(escape(d["pages"].format(n=pages)))
    chips.append(f'<span class="num">{escape(d["seconds"].format(s=round(seconds, 1)))}</span>')
    if ocr:
        chips.append("OCR")
    chips_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    if "docx" in formats:
        lead = f'<a class="btn" href="heocr:save-docx" role="button">{ico("word-doc")}{t["save_word"]}</a><a class="iconbtn framed" href="heocr:copy" role="button" aria-label="{t["copy"]}">{ico("copy")}</a>'
    else:
        lead = f'<a class="btn" href="heocr:copy" role="button">{ico("copy")}{t["copy"]}</a>'
    share = f'<a class="iconbtn framed" href="heocr:share" role="button" aria-label="{t["share"]}">{ico("share")}</a>'
    bar = f'<footer class="actionbar">{lead}{share}<a class="iconbtn framed" href="heocr:more" role="button" aria-label="{t["more"]}">{ico("more")}</a></footer>'
    return html(lang, appbar_back(t, escape(name), file=True) + f'''
<main class="screen result">
<div class="chips">{chips_html}</div>
{document(doc, d, t["ocr_note"] if ocr else None)}
</main>
{bar}{more_sheet(t, formats)}''', zoom=True)


def toast(text: str, sub: str = "", low: bool = False, action: tuple[str, str] | None = None) -> str:
    """A confirmation (8.10), inserted into the page from outside and removed after 4 seconds (8 with an
    action). ``action`` is (label, app address), e.g. Open for the saved file."""
    small = f'<small dir="auto">{sub}</small>' if sub else ""
    cls = "toast low" if low else "toast"
    link = f'<a href="heocr:{action[1]}" role="button">{action[0]}</a>' if action else ""
    return f'<div class="{cls}" role="status" id="toast">{ico("check")}<div>{text}{small}</div>{link}</div>'


# The four problem states (8.11): engine kind -> (strings, icon, primary, secondary).
def problem(t: dict, d: dict, lang: str, kind: str, photo: bool = False, body: str | None = None) -> str:
    if kind == "needs_converter":
        n, icon, primary = 2, "word-doc", ("open", "open-file", t["p2_a"])
        secondary = (t["home_btn"], "home", None)
    elif kind == "empty":
        n, icon = 3, "camera" if photo else "text-file"
        primary = ("photo", "camera", t["p3_a"]) if photo else ("open", "open-file", t["p1_a"])
        secondary = (t["open"], "open", "open-file") if photo else (t["home_btn"], "home", None)
    else:  # unreadable, an incomplete copy, or an error while reading
        n, icon, primary = 1, "warning", ("open", "open-file", t["p1_a"])
        secondary = (t["home_btn"], "home", None)
    text = body if body is not None else (t[f"p{n}_b"] if photo or n != 3 else escape(d["empty"]))
    hint = t[f"p{n}_h"] if photo or n != 3 else ""
    sec = f'<a class="btn secondary block" href="heocr:{secondary[1]}" role="button">{ico(secondary[2]) if secondary[2] else ""}{secondary[0]}</a>'
    return html(lang, appbar_home(t) + f'''
<main class="screen">
<div class="problem">
<div class="mark">{ico(icon)}</div>
<h2>{t[f"p{n}_t"]}</h2>
<p>{text}</p>
{f'<p class="hint">{hint}</p>' if hint else ""}
<div class="stack"><a class="btn block" href="heocr:{primary[0]}" role="button">{ico(primary[1])}{primary[2]}</a>{sec}</div>
</div>
</main>''')


MODEL_DOIS = ("10.5281/zenodo.24372349", "10.5281/zenodo.24372352")


def about(t: dict, lang: str, versions: dict[str, str], back: str = "home") -> str:
    """7 About: privacy, accuracy, the versions and licences of this build, help."""
    def lic(a, b, sub=""):
        s = f"<span>{sub}</span>" if sub else ""
        return f'<div class="row"><div><strong>{a}</strong>{s}</div><span class="end"><bdi dir="ltr">{b}</bdi></span></div>'

    items = "".join(f"<li>{x}</li>" for x in t["what_items"])
    dois = " · ".join(f'<bdi dir="ltr">{x}</bdi>' for x in MODEL_DOIS)
    kv = (f'<dt>{t["v_app"]}</dt><dd><bdi dir="ltr">{escape(versions["app"])}</bdi></dd>'
          f'<dt><bdi dir="ltr">heocr</bdi></dt><dd><bdi dir="ltr">{escape(versions["heocr"])}</bdi></dd>'
          f'<dt><bdi dir="ltr">Tesseract</bdi></dt><dd><bdi dir="ltr">{escape(versions["tesseract"])}</bdi></dd>')
    return html(lang, appbar_back(t, t["about"], about=False, back=back) + f'''
<main class="screen">
<div class="band"><h1><span class="bb">{t["about_title"]}</span></h1><p class="lede">{t["about_body"]}</p></div>
<p class="sectionhead">{t["privacy_h"]}</p>
<div class="fact" style="border: 0; padding: 0">{ico("private")}<p>{t["privacy"]}</p></div>
<p class="sectionhead">{t["accuracy_h"]}</p>
<p>{t["accuracy"]}</p>
<p>{t["niqqud"]}</p>
<p class="sectionhead">{t["version_h"]}</p>
<dl class="kv">{kv}</dl>
<p class="sectionhead">{t["licences_h"]}</p>
<div class="rows">
{lic('<bdi dir="ltr">heocr</bdi>', "Apache-2.0")}
{lic('<bdi dir="ltr">Tesseract OCR</bdi>', "Apache-2.0")}
{lic(t["lic_models"], "Apache-2.0", t["lic_models_sub"] + "<br>" + dois)}
{lic(t["lic_fonts"], "OFL 1.1", '<bdi dir="ltr">Noto Sans Hebrew, JetBrains Mono</bdi>')}
<a class="row" href="heocr:licences" role="button"><div><strong>{t["lic_all"]}</strong></div>{ico("chevron", "sm")}</a>
</div>
<p class="sectionhead">{t["help_h"]}</p>
<div class="rows">
<a class="row" href="https://heocr.github.io">{ico("external")}<div><strong><bdi dir="ltr">heocr.github.io</bdi></strong><span>{t["site_sub"]}</span></div></a>
<a class="row" href="heocr:diagnostics" role="button">{ico("diagnostics")}<div><strong>{t["diag"]}</strong><span>{t["diag_sub"]}</span></div></a>
</div>
<details class="what"><summary>{t["what"]}</summary><ul>{items}</ul><p>{t["what_not"]}</p></details>
</main>''')


def licences(t: dict, lang: str, markdown: str) -> str:
    """The full licence list (THIRD_PARTY_LICENSES.md), in the document style: headings, lists, text."""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append(f'<p dir="ltr">{" ".join(para)}</p>')
            para.clear()
        if items:
            out.append('<ul dir="ltr">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()

    for raw in markdown.splitlines():
        line = escape(raw.strip())
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", line)
        line = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", line)
        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)
        if not line or line.startswith("|---") or line.startswith("| ---"):
            flush()
        elif m := re.match(r"(#{1,4}) (.*)", line):
            flush()
            level = min(len(m.group(1)) + 1, 4)
            out.append(f'<h{level} dir="ltr">{m.group(2)}</h{level}>')
        elif m := re.match(r"[-*] (.*)", line):
            if para:
                flush()
            items.append(m.group(1))
        else:
            if items:
                flush()
            para.append(line.replace("|", " "))
    flush()
    return html(lang, appbar_back(t, t["lic_all"], about=False, back="about") + f'<main class="screen result"><article class="doc" dir="ltr">{"".join(out)}</article></main>', zoom=True)
