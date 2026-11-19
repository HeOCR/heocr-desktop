"""What "Save" writes, for the desktop and Android apps alike: one function per format, as bytes.

- ``txt``: the plain text, UTF-8 **with a byte-order mark**, so Windows Notepad and older Windows tools
  show the Hebrew instead of mojibake; macOS TextEdit reads it either way.
- ``md``: heocr's Markdown, UTF-8.
- ``json``: heocr's full record, UTF-8.
- ``docx``: Word, from heocr's own writer (``Document.to_docx()``, HeOCR/heocr#124), so the CLI and both
  apps write the same file. It is offered only when the installed heocr has it, and then first.
"""

from __future__ import annotations

import json

import heocr

FORMATS = ("txt", "md", "json")  # always available
MIME = {
    "txt": "text/plain",
    "md": "text/markdown",
    "json": "application/json",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def has_docx() -> bool:
    """Whether the installed heocr writes Word files (``Document.to_docx``)."""
    return callable(getattr(heocr.Document, "to_docx", None))


def formats() -> tuple[str, ...]:
    """What Save offers, in order: Word first when heocr can write it, then text, Markdown, JSON."""
    return (("docx",) if has_docx() else ()) + FORMATS


def export(doc, kind: str) -> bytes:
    """The saved file's bytes for a reading, in one of ``formats()``."""
    if kind == "docx" and has_docx():
        return doc.to_docx()
    if kind == "txt":
        return doc.text.encode("utf-8-sig")
    if kind == "md":
        return doc.markdown.encode("utf-8")
    if kind == "json":
        return (json.dumps(doc.to_dict(), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    raise ValueError(f"unknown format {kind!r}; known: {', '.join(formats())}")
