"""What "Save" writes, for the desktop and Android apps alike: one function per format, as bytes.

- ``txt``: the plain text, UTF-8 **with a byte-order mark**, so Windows Notepad and older Windows tools
  show the Hebrew instead of mojibake; macOS TextEdit reads it either way.
- ``md``: heocr's Markdown, UTF-8.
- ``json``: heocr's full record, UTF-8.
- ``docx`` (Word) comes from heocr itself once its writer lands, so the CLI and both apps share one.
"""

from __future__ import annotations

import json

FORMATS = ("txt", "md", "json")
MIME = {
    "txt": "text/plain",
    "md": "text/markdown",
    "json": "application/json",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def export(doc, kind: str) -> bytes:
    """The saved file's bytes for a reading, in one of ``FORMATS``."""
    if kind == "txt":
        return doc.text.encode("utf-8-sig")
    if kind == "md":
        return doc.markdown.encode("utf-8")
    if kind == "json":
        return (json.dumps(doc.to_dict(), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    raise ValueError(f"unknown format {kind!r}; known: {', '.join(FORMATS)}")
