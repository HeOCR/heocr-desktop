#!/usr/bin/env python3
"""Run the packaged app in smoke mode on the fixtures and fail unless every one passes.

    python scripts/smoke_app.py macos              # build/…/HeOCR.app
    python scripts/smoke_app.py macos-x86_64       # the same app's Intel slice, under Rosetta
    python scripts/smoke_app.py windows            # build/…/HeOCR.exe
    python scripts/smoke_app.py windows-installed  # the MSI-installed HeOCR.exe
    python scripts/smoke_app.py path/to/executable

The app reads ``tests/fixtures`` (invented text only) with its bundled Tesseract, exactly as
the window does, and writes ``smoke-report.json``. No window opens.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build" / "heocr_desktop"


def executable(where: str) -> Path:
    if where in ("macos", "macos-x86_64"):
        return BUILD / "macos" / "app" / "HeOCR.app" / "Contents" / "MacOS" / "HeOCR"
    if where == "windows":
        return BUILD / "windows" / "app" / "src" / "HeOCR.exe"
    if where == "windows-installed":
        roots = [os.environ.get("ProgramFiles", r"C:\Program Files"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")]
        for root in roots:
            for found in Path(root).glob("**/HeOCR/HeOCR.exe"):
                return found
        sys.exit(f"installed HeOCR.exe not found under {roots}")
    return Path(where)


def main(where: str) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252; the report is Hebrew
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    exe = executable(where)
    if not exe.is_file():
        sys.exit(f"no app at {exe}")
    work = Path(tempfile.mkdtemp(prefix="heocr-smoke-"))
    shutil.copytree(ROOT / "tests" / "fixtures", work / "fixtures")
    env = dict(os.environ, HEOCR_DESKTOP_SMOKE=str(work / "fixtures"))
    print("running", exe, flush=True)
    argv = ["arch", "-x86_64", str(exe)] if where == "macos-x86_64" else [str(exe)]
    proc = subprocess.run(argv, env=env, timeout=900, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(proc.stdout[-4000:], proc.stderr[-4000:], sep="\n")
    report_path = work / "fixtures" / "smoke-report.json"
    if not report_path.is_file():
        print(f"no smoke report; exit code {proc.returncode}")
        return 1
    report = json.loads(report_path.read_text("utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    out = ROOT / "build" / f"smoke-report-{where if os.sep not in where else 'custom'}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    return 0 if report.get("ok") and proc.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "macos"))
