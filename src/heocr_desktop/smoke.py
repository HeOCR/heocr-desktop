"""Headless smoke conversion, run inside the packaged app (CI and local release checks).

``HEOCR_DESKTOP_SMOKE=<fixtures folder>`` makes the app read every fixture with exactly the
code path the window uses (bundled Tesseract, no conversion), write ``smoke-report.json`` next
to them, and exit 0 only if each fixture meets its expectation. No window opens.

Expectations come from ``expect.json`` in the folder: ``{"file": {"kind": "ok", "route": "ocr",
"contains": ["..."]}}``. The fixtures hold invented text only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from heocr_desktop import engine


def run(folder: str) -> int:
    base = Path(folder)
    expect = json.loads((base / "expect.json").read_text("utf-8"))
    report: dict = {
        "tesseract": str(engine.tesseract_path()),
        "tessdata": str(engine.tessdata_path()),
        "files": {},
    }
    failures = 0
    for name, want in sorted(expect.items()):
        entry: dict = {"want": want}
        try:
            result = engine.convert(base / name)
            text = result.doc.text if result.doc is not None else ""
            entry.update(kind=result.kind, routes=result.routes, sources=result.sources, unread=result.unread, chars=len(text), seconds=round(result.seconds, 2))
            problems = []
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
        print(name, "OK" if not entry["problems"] else entry["problems"], flush=True)
    report["ok"] = failures == 0
    out = base / "smoke-report.json"
    try:
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    except OSError:
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
    return 0 if failures == 0 else 1
