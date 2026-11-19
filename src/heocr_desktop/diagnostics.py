"""A reading's structure, safe to send: how it was read, never what it says.

``report(result)`` keeps the record's shape: format, pages with their class, route, flags and
measurements, the document's flags, why parts were not read, block counts by kind and source, and
the components' versions. It drops every piece of text (blocks, cells, lines, labels, readings, the
file's name and hash), and keeps a value only if it is a number, a true/false, or a short code
(flags, routes, classes, reasons). Font names are kept, because a font that reads wrongly is the
usual cause of a bad text layer; they name typefaces, not content.
"""

from __future__ import annotations

import json
import platform
import re
import sys

_CODE = re.compile(r"^[A-Za-z0-9_.:+\-/ ]{1,64}$")


def _number(value):
    return isinstance(value, (int, float, bool)) or value is None


def _safe(value, depth: int = 0):
    """Numbers, booleans and short codes, in nested dicts and lists; anything else is dropped."""
    if _number(value):
        return value
    if isinstance(value, str):
        return value if _CODE.match(value) else None
    if depth > 3:
        return None
    if isinstance(value, (list, tuple)):
        kept = [_safe(v, depth + 1) for v in value]
        return [v for v in kept if v is not None]
    if isinstance(value, dict):
        kept = {str(k): _safe(v, depth + 1) for k, v in value.items() if isinstance(k, str) and _CODE.match(k)}
        return {k: v for k, v in kept.items() if v is not None}
    return None


def report(result, *, app: str, app_version: str, input_bytes: int | None = None, declared_bytes: int | None = None) -> dict:
    """The safe structure of one reading (``heocr_desktop.engine.Result``)."""
    import heocr

    doc = result.doc
    out: dict = {
        "app": app,
        "app_version": app_version,
        "heocr": getattr(heocr, "__version__", "unknown"),
        "python": platform.python_version(),
        "platform": sys.platform,
        "kind": result.kind,
        "seconds": round(result.seconds, 2),
        "input_bytes": input_bytes,
        "declared_bytes": declared_bytes,
    }
    if doc is None:
        return out
    record = doc.to_dict()
    document = record.get("document") or {}
    out["format"] = _safe(document.get("format"))
    out["format_evidence"] = _safe(document.get("format_evidence"))
    out["page_count"] = _safe(document.get("page_count"))
    out["read_bytes"] = _safe(document.get("bytes"))  # what heocr read; the file's hash is left out
    out["flags"] = _safe(record.get("flags", []))
    out["options"] = _safe(record.get("options", {}))
    out["components"] = _safe((record.get("producer") or {}).get("components", {}))
    pages = []
    for page in record.get("pages", []):
        fonts = [f for f in (page.get("signals") or {}).get("fonts", []) if isinstance(f, str) and len(f) <= 64]
        signals = _safe({k: v for k, v in (page.get("signals") or {}).items() if k != "fonts"})
        pages.append({**_safe({k: page.get(k) for k in ("index", "width", "height", "class", "route", "flags", "coverage")}), "signals": signals, "fonts": fonts})
    out["pages"] = pages
    out["unread"] = [_safe({k: u.get(k) for k in ("scope", "reason", "page")}) for u in record.get("unread", [])]
    blocks: dict[str, int] = {}
    for block in record.get("blocks", []):
        key = f"{block.get('source')}:{block.get('kind')}"
        blocks[key] = blocks.get(key, 0) + 1
    out["blocks"] = blocks
    return out


def text(report_dict: dict) -> str:
    """The report as the text the "Copy diagnostics" button puts on the clipboard."""
    return "HeOCR diagnostics (structure only, no document text)\n" + json.dumps(report_dict, ensure_ascii=True, indent=1, sort_keys=True)


STRUCTURE_SIGNALS = ("chars", "image_coverage", "invisible_share", "hebrew_share", "images", "paths")


def page_structure(doc) -> list[dict]:
    """Per page: class, route, flags and the measurements the classifier decides on. Two platforms that
    read a document the same way give the same list (the on-device test compares it with the host's)."""
    pages = []
    for page in doc.to_dict().get("pages", []):
        signals = page.get("signals") or {}
        pages.append({
            "index": page.get("index"),
            "class": page.get("class"),
            "route": page.get("route"),
            "flags": page.get("flags", []),
            **{k: signals.get(k) for k in STRUCTURE_SIGNALS},
        })
    return pages


if __name__ == "__main__":  # python -m heocr_desktop.diagnostics doc.pdf > doc.expected.json (no OCR needed)
    import heocr as _heocr

    _doc = _heocr.extract(sys.argv[1], ocr=False, convert=False)
    print(json.dumps({"heocr": _heocr.__version__, "pages": page_structure(_doc)}, indent=1, sort_keys=True))
