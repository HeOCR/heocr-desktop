"""Headless conversions for CI: the packaged app's own Python, Tesseract and models, no window."""
from __future__ import annotations

import json
import traceback
from pathlib import Path

from . import core, offline


def main(out: str, files: list[str]) -> int:
    offline.enforce()
    info = core.configure()
    report = {"info": info, "files": []}
    ok = True
    for f in files:
        entry = {"file": Path(f).name}
        try:
            r = core.convert(f)
            entry.update(format=r.format, routes=r.routes, unread=r.unread, text=r.text)
        except Exception:  # noqa: BLE001 - reported, and the run fails
            entry["error"] = traceback.format_exc()
            ok = False
        report["files"].append(entry)
    Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if ok else 1
