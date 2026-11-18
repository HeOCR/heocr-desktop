"""The heocr record as HTML for the app's reading pane.

It follows heocr's own Markdown view (``heocr.render.to_markdown``): the body in reading
order with page breaks, then footnotes, endnotes, comments, headers, footers, speaker notes and
navigation, each under its own heading. Every block gets ``dir="auto"`` unless heocr recorded
its direction, so Hebrew reads right to left and English left to right in the same document.
"""

from __future__ import annotations

from html import escape

MAX_SPAN = 1000
_INLINE_ROLES = ("body", "textbox")
SECTIONS = ("footnote", "endnote", "comment", "header", "footer", "notes", "navigation")


def _dir(block) -> str:
    direction = getattr(block, "direction", None)
    return direction if direction in ("rtl", "ltr") else "auto"


def _lines(text: str) -> str:
    return "<br>".join(escape(part) for part in text.split("\n"))


def _labelled(block) -> str:
    text = _lines(block.text or "")
    if not block.label:
        return text
    joiner = "" if "label_suffix_nothing" in (block.flags or []) else " "
    return f'<span class="label">{escape(block.label)}</span>{joiner}{text}'


def _table(block) -> str:
    rows = []
    for row in block.cells or []:
        cells = []
        for cell in row:
            attrs = ""
            colspan = min(max(getattr(cell, "colspan", 1) or 1, 1), MAX_SPAN)
            rowspan = min(max(getattr(cell, "rowspan", 1) or 1, 1), MAX_SPAN)
            if colspan > 1:
                attrs += f' colspan="{colspan}"'
            if rowspan > 1:
                attrs += f' rowspan="{rowspan}"'
            flagged = " flagged" if getattr(cell, "flags", None) else ""
            cells.append(f'<td dir="auto" class="cell{flagged}"{attrs}>{_lines(cell.text or "")}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    if not rows:
        return ""
    return f'<div class="table-wrap"><table dir="{_dir(block)}">' + "".join(rows) + "</table></div>"


def block_html(block) -> str:
    ocr = " ocr" if block.source == "ocr" else ""
    if block.kind == "table":
        return _table(block)
    if block.kind == "figure":
        return '<p class="figure" data-i18n="figure_not_read"></p>'
    if block.kind == "heading":
        level = min(max(block.level or 1, 1), 6)
        return f'<h{level} dir="{_dir(block)}" class="block{ocr}">{_labelled(block)}</h{level}>'
    css = "block list-item" if block.kind == "list_item" else "block"
    note = f'<sup class="note-id">{escape(block.note_id)}</sup> ' if block.note_id else ""
    return f'<p dir="{_dir(block)}" class="{css}{ocr}">{note}{_labelled(block)}</p>'


def document_html(doc) -> str:
    """The reading pane's content: body, then the other parts under their own titles."""
    parts: list[str] = []
    previous = None
    for block in doc.blocks:
        if block.role not in _INLINE_ROLES:
            continue
        where = block.page if block.page is not None else block.slide
        if where is not None and where != previous:
            key = "page_n" if block.page is not None else "slide_n"
            number = block.page + 1 if block.page is not None else block.slide
            parts.append(f'<div class="page-break" data-i18n="{key}" data-n="{number}"></div>')
            previous = where
        parts.append(block_html(block))
    for role in SECTIONS:
        items = [b for b in doc.blocks if b.role == role]
        if not items:
            continue
        parts.append(f'<h2 class="section" data-i18n="section_{role}"></h2>')
        parts.extend(block_html(b) for b in items)
    return "\n".join(parts)


def document_direction(text: str) -> str:
    """``rtl`` when Hebrew (or Arabic) letters outnumber Latin ones, so tables and page marks sit
    on the side the document reads from."""
    rtl = sum(1 for ch in text if "\u0590" <= ch <= "\u08ff" or "\ufb1d" <= ch <= "\ufdff")
    ltr = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    return "rtl" if rtl >= ltr and rtl else "ltr"
