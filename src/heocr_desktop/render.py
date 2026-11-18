"""heocr's Markdown as HTML for the window: headings, paragraphs, tables, section rules and page marks.

Only the constructs heocr writes are handled, and every piece of text is escaped. Each block gets
``dir="auto"``, so a Hebrew paragraph reads right to left and a Latin one left to right, whatever the
interface language.
"""
from __future__ import annotations

import html
import re

_PAGE = re.compile(r"<!-- (page|slide) (\d+) -->")
_NOTE = re.compile(r"<!-- heocr: (.*?) -->", re.S)
_HEADING = re.compile(r"(#{1,6}) (.*)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RULE = re.compile(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?")


def _inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = out.replace("&lt;br&gt;", "<br>")
    return _BOLD.sub(r"<strong>\1</strong>", out)


def _cells(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    cells, cur, i = [], "", 0
    while i < len(row):
        if row[i] == "\\" and i + 1 < len(row) and row[i + 1] == "|":
            cur += "|"
            i += 2
            continue
        if row[i] == "|":
            cells.append(cur.strip())
            cur = ""
        else:
            cur += row[i]
        i += 1
    cells.append(cur.strip())
    return cells


def _table(lines: list[str]) -> str:
    rows = [_cells(l) for l in lines if not _RULE.fullmatch(l.strip())]
    if not rows:
        return ""
    head, body = rows[0], rows[1:]
    out = ['<table dir="auto"><thead><tr>' + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"]
    out += ["<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in body]
    out.append("</tbody></table>")
    return "".join(out)


def to_html(markdown: str, page_label: str = "Page") -> str:
    parts = []
    for chunk in re.split(r"\n\s*\n", markdown.strip()):
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        m = _PAGE.fullmatch(chunk.strip())
        if m:
            parts.append(f'<div class="page-mark">{html.escape(page_label)} {m.group(2)}</div>')
            continue
        m = _NOTE.fullmatch(chunk.strip())
        if m:
            parts.append(f'<div class="note" dir="auto">{html.escape(m.group(1))}</div>')
            continue
        if chunk.strip() == "---":
            parts.append("<hr>")
            continue
        m = _HEADING.fullmatch(chunk.strip())
        if m:
            level = len(m.group(1))
            parts.append(f'<h{level} dir="auto">{_inline(m.group(2))}</h{level}>')
            continue
        lines = chunk.split("\n")
        if all(l.strip().startswith("|") for l in lines):
            parts.append(_table(lines))
            continue
        body = "<br>".join(_inline(l.rstrip()) for l in lines)
        parts.append(f'<p dir="auto">{body}</p>')
    return "\n".join(parts)
