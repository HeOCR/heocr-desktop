"""The reading as one self-contained HTML page for the app's WebView: no script, no network."""

from __future__ import annotations

import re
from pathlib import Path
from html import escape

from heocr_desktop import render

# The design's result stylesheet (design/android/css/result-standalone.css): brand tokens for light and
# night, the two typefaces embedded as data URIs, and the rules for heocr's result markup under ``.doc``.
CSS = (Path(__file__).resolve().parent / "result.css").read_text("utf-8")
# Nothing loads: the fonts are inside the stylesheet (font-src data:), and there is no script.
CSP = "default-src 'none'; style-src 'unsafe-inline'; font-src data:"

_MODEL = re.compile(r"^tesseract:(.+)\.traineddata$")


def ocr_models(doc) -> set[str]:
    """The Tesseract models a reading used (``heb``, ``eng``, ``heocr_modern_v1``), from its record."""
    return {m.group(1) for key in getattr(doc, "components", {}) if (m := _MODEL.match(key))}


def _html(body: str, direction: str) -> str:
    return (
        f'<!doctype html><html dir="{direction}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'
        f'<style>{CSS}</style></head><body class="doc">{body}</body></html>'
    )


def welcome(strings: dict[str, str], lang: str) -> str:
    """The page before any reading: what to do, and the offline promise (it wraps, unlike a label)."""
    direction = "rtl" if lang == "he" else "ltr"
    return _html(f'<p>{escape(strings["welcome"])}</p><p class="note">{escape(strings["offline"])}</p>', direction)


def message(strings: dict[str, str], lang: str, text: str) -> str:
    """A message in place of a reading (the file could not be read, needs a converter, had no text)."""
    direction = "rtl" if lang == "he" else "ltr"
    return _html(f'<p>{escape(text)}</p><p class="note">{escape(strings["welcome"])}</p>', direction)


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
