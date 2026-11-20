"""Headless smoke conversion, run inside the packaged app (CI and local release checks).

``HEOCR_DESKTOP_SMOKE=<fixtures folder>`` makes the app read every fixture with exactly the
code path the window uses (bundled Tesseract, no conversion), write ``smoke-report.json`` next
to them, and exit 0 only if each fixture meets its expectation. No window opens.

Expectations come from ``expect.json`` in the folder: ``{"file": {"kind": "ok", "route": "ocr",
"contains": ["..."]}}``. The fixtures hold invented text only.

Every reading also records the Tesseract models it used and the document's flags. A document flagged
``bundled_model_unavailable`` (heocr's own model missing, stock Tesseract read instead) always fails.
OCR must use the shipped stock ``heb`` model. ``eng`` may also be used for number checks.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from heocr_desktop import engine, licences

_MODEL = re.compile(r"^tesseract:(.+)\.traineddata$")


def models(doc) -> list[str]:
    """The Tesseract models a reading used, from its record (``heb``, ``eng``)."""
    return sorted({m.group(1) for key in getattr(doc, "components", {}) or {} if (m := _MODEL.match(key))})


def run(folder: str, *, resources: Path | None = None) -> int:
    """Run fixture and font licence checks using the packaged app's resources."""
    if resources is None:
        resources = engine.RESOURCES
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    base = Path(folder)
    expect = json.loads((base / "expect.json").read_text("utf-8"))
    report: dict = {
        "tesseract": str(engine.tesseract_path()),
        "tessdata": str(engine.tessdata_path()),
        "files": {},
    }
    want_model = os.environ.get("HEOCR_SMOKE_MODEL", "heb")
    report["want_model"] = want_model
    missing = [
        name for name, filename in licences.FONT_NOTICES.items()
        if not (resources / "licenses" / filename).is_file()
    ]
    report["missing_font_licences"] = missing
    failures = len(missing)
    for name, want in sorted(expect.items()):
        entry: dict = {"want": want}
        try:
            result = engine.convert(base / name)
            text = result.doc.text if result.doc is not None else ""
            used = models(result.doc) if result.doc is not None else []
            flags = list(getattr(result.doc, "flags", []) or []) if result.doc is not None else []
            entry.update(kind=result.kind, routes=result.routes, sources=result.sources, unread=result.unread, chars=len(text), seconds=round(result.seconds, 2), models=used, flags=flags)
            problems = []
            if "bundled_model_unavailable" in flags:
                problems.append("bundled_model_unavailable")
            if unexpected := set(used) - {"heb", "eng"}:
                problems.append(f"unexpected OCR model: {sorted(unexpected)}")
            if "ocr" in result.routes and want_model not in used:
                problems.append(f"read without {want_model}: {used}")
            if result.kind != want.get("kind", "ok"):
                problems.append(f"kind {result.kind}")
            route = want.get("route")
            if route and route not in result.routes and route not in result.sources:
                problems.append(f"no {route} route")
            for needle in want.get("contains", []):
                if needle not in text:
                    problems.append(f"missing {needle!r}")
            entry["problems"] = problems
        except Exception as exc:  # noqa: BLE001
            entry["problems"] = [f"{type(exc).__name__}: {exc}"]
        failures += bool(entry["problems"])
        report["files"][name] = entry
        if sys.stdout is not None:  # a Windows GUI app may have no console at all
            print(name, "OK" if not entry["problems"] else entry["problems"], flush=True)
    report["ok"] = failures == 0
    out = base / "smoke-report.json"
    try:
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    except OSError:
        if sys.stderr is not None:
            print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
    return 0 if failures == 0 else 1
