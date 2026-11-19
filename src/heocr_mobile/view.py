"""The reading as one self-contained HTML page for the app's WebView: no script, no network."""

from __future__ import annotations

import re
from html import escape

from heocr_desktop import render

CSS = """
body { font-family: sans-serif; margin: 12px; line-height: 1.5; color: #111; background: #fff; }
.block { margin: 0 0 0.6em; }
.page-break { margin: 1.2em 0 0.4em; color: #666; font-size: 0.85em; border-top: 1px solid #ddd; padding-top: 0.3em; }
h2.section { font-size: 1em; color: #444; }
table { border-collapse: collapse; margin: 0.6em 0; }
td, th { border: 1px solid #ccc; padding: 2px 6px; }
.figure { color: #666; font-style: italic; }
.note { color: #555; font-size: 0.9em; }
"""

_MODEL = re.compile(r"^tesseract:(.+)\.traineddata$")


def ocr_models(doc) -> set[str]:
    """The Tesseract models a reading used (``heb``, ``eng``, ``heocr_modern_v1``), from its record."""
    return {m.group(1) for key in getattr(doc, "components", {}) if (m := _MODEL.match(key))}


def _html(body: str, direction: str) -> str:
    return (
        f'<!doctype html><html dir="{direction}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )


def welcome(strings: dict[str, str], lang: str) -> str:
    """The page before any reading: what to do, and the offline promise (it wraps, unlike a label)."""
    direction = "rtl" if lang == "he" else "ltr"
    return _html(f'<p>{escape(strings["welcome"])}</p><p class="note">{escape(strings["offline"])}</p>', direction)


_PLACEHOLDER = re.compile(r'(<(\w+)[^>]*?data-i18n="(\w+)"(?: data-n="(\d+)")?[^>]*>)(</\2>)')


def page(doc, strings: dict[str, str], notes: list[str]) -> str:
    """The rendered document, with the desktop's ``data-i18n`` labels filled in."""
    body = render.document_html(doc)

    def fill(match: re.Match) -> str:
        text = strings.get(match.group(3), "")
        if match.group(4):
            text = text.format(n=match.group(4))
        return f"{match.group(1)}{escape(text)}{match.group(5)}"

    body = _PLACEHOLDER.sub(fill, body)
    direction = render.document_direction(doc.text)
    # dir="auto": a note in the UI's language keeps its own direction inside a page of the other one.
    extra = "".join(f'<p class="note" dir="auto">{escape(n)}</p>' for n in notes)
    return _html(extra + body, direction)
