"""Headless smoke conversion, run inside the packaged app (CI and local release checks).

``HEOCR_DESKTOP_SMOKE=<fixtures folder>`` makes the app read every fixture with exactly the
code path the window uses (bundled Tesseract, no conversion), write ``smoke-report.json`` next
to them, and exit 0 only if each fixture meets its expectation. No window opens.

Expectations come from ``expect.json`` in the folder: ``{"file": {"kind": "ok", "route": "ocr",
"contains": ["..."]}}``. The fixtures hold invented text only.

Every reading also records the Tesseract models it used and the document's flags. A document flagged
``bundled_model_unavailable`` (heocr's own model missing, stock Tesseract read instead) always fails.
The structured PDF and Word fixtures also round-trip through the app's Word exporter.
Fixtures with a ``batch_name`` also run together in a folder to check Word copies and the batch report.
OCR must use the shipped stock ``heb`` model. ``eng`` may also be used for number checks.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import threading
from collections import Counter
from pathlib import Path

import heocr

from heocr_desktop import batch, engine, exports, i18n, licences

_MODEL = re.compile(r"^tesseract:(.+)\.traineddata$")


def models(doc) -> list[str]:
    """The Tesseract models a reading used, from its record (``heb``, ``eng``)."""
    return sorted({m.group(1) for key in getattr(doc, "components", {}) or {} if (m := _MODEL.match(key))})


def _word_structure(doc) -> list[tuple]:
    """Compare ordered headings and tables, including direction and merged cells."""
    blocks = []
    for block in doc.blocks:
        if block.role not in ("body", "textbox"):
            continue
        if block.kind == "heading":
            blocks.append(("heading", block.level, block.text, block.direction))
        elif block.kind == "table":
            rows = [
                [(cell.text, cell.rowspan, cell.colspan) for cell in row]
                for row in block.cells or []
            ]
            blocks.append(("table", block.direction, rows))
    return blocks


def word_roundtrip_problems(doc, expected: dict[str, int], contains: list[str]) -> list[str]:
    """Check the Save as Word bytes against the reading and the fixture's expected structure."""
    if doc is None:
        return ["no document for Word export"]
    if exports.formats()[0] != "docx":
        return ["Word is unavailable as the first save format"]
    before = _word_structure(doc)
    counts = Counter(block[0] for block in before)
    problems = [
        f"expected {count} {kind} blocks before Word export, found {counts[kind]}"
        for kind, count in expected.items()
        if counts[kind] != count
    ]
    saved = heocr.extract(exports.export(doc, "docx"), ocr=False, convert=False, ocr_model=None)
    if saved.format != "docx":
        problems.append("Word export did not read back as DOCX")
    if _word_structure(saved) != before:
        problems.append("Word export changed headings or table structure")
    for needle in contains:
        if needle not in saved.text:
            problems.append(f"Word export missing {needle!r}")
    return problems


def _batch_problems(base: Path, fixtures: dict) -> list[str]:
    problems = []
    with tempfile.TemporaryDirectory(prefix="תיקייה ", dir=base) as directory:
        folder = Path(directory)
        expected = {}
        for fixture, want in fixtures.items():
            name = want["batch_name"]
            shutil.copyfile(base / fixture, folder / name)
            expected[name] = want.get("kind", "ok")

        result = batch.convert_folder(folder, lambda *_: None, lambda _: None, threading.Event())
        if {item["name"]: item["kind"] for item in result.items} != expected:
            problems.append("folder results differ from the expected file and error types")
        outputs = {item["output"] for item in result.items if "output" in item}
        saved = sum(kind == "ok" for kind in expected.values())
        if len(outputs) != saved or any(not (result.directory / name).is_file() for name in outputs):
            problems.append("folder run is missing Word copies")
        if result.report is None:
            return [*problems, "folder run did not save its batch report"]
        report = result.report.read_text("utf-8-sig")
        strings = i18n.STRINGS["en"]
        summary = strings["batch_saved"].format(saved=saved, total=len(expected))
        if summary not in report:
            problems.append("batch report has the wrong saved/total count")
        for name, kind in expected.items():
            if kind != "ok" and f"{json.dumps(name, ensure_ascii=False)}: {strings[kind]}" not in report:
                problems.append(f"batch report is missing the failure reason for {name!r}")
    return problems


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
            if "docx_structure" in want:
                word_problems = word_roundtrip_problems(result.doc, want["docx_structure"], want["contains"])
                entry["word_roundtrip"] = not word_problems
                problems.extend(word_problems)
            entry["problems"] = problems
        except Exception as exc:  # noqa: BLE001
            entry["problems"] = [f"{type(exc).__name__}: {exc}"]
        failures += bool(entry["problems"])
        report["files"][name] = entry
        if sys.stdout is not None:  # a Windows GUI app may have no console at all
            print(name, "OK" if not entry["problems"] else entry["problems"], flush=True)
    if batch_fixtures := {name: want for name, want in expect.items() if "batch_name" in want}:
        try:
            problems = _batch_problems(base, batch_fixtures)
        except Exception as exc:  # Include diagnostics even if the folder setup or report read fails.
            problems = [f"{type(exc).__name__}: {exc}"]
        report["batch"] = {"ok": not problems, "problems": problems}
        failures += bool(problems)
    report["ok"] = failures == 0
    out = base / "smoke-report.json"
    try:
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    except OSError:
        if sys.stderr is not None:
            print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
    return 0 if failures == 0 else 1
