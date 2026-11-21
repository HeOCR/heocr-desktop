"""Read the regular files directly inside one folder and save Word copies and a report."""

from __future__ import annotations

import json
import threading
import traceback
from dataclasses import dataclass
from itertools import count
from pathlib import Path
from typing import Callable

from heocr_desktop import engine, exports, i18n

REPORT_NAME = "batch-report.txt"


@dataclass
class BatchResult:
    directory: Path | None
    items: list[dict]
    total: int
    cancelled: bool
    report: Path | None


def _new_directory(folder: Path) -> Path:
    for n in count(1):
        candidate = folder / ("HeOCR" if n == 1 else f"HeOCR ({n})")
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue


def _write_new_file(target: Path, data: bytes) -> None:
    stream = target.open("xb")
    try:
        with stream:
            stream.write(data)
    except OSError:
        target.unlink(missing_ok=True)
        raise


def _write_word(directory: Path, source: Path, data: bytes) -> str:
    for n in count(1):
        stem = source.stem if n == 1 else f"{source.stem} ({n})"
        target = directory / f"{stem}.docx"
        try:
            _write_new_file(target, data)
        except FileExistsError:
            continue
        return target.name


def _report_bytes(items: list[dict], total: int, cancelled: bool) -> bytes:
    strings = i18n.STRINGS["en"]
    read = [item for item in items if item["kind"] in ("ok", "batch_write_error")]
    failures = [item for item in items if item["kind"] != "ok"]
    lines = [
        strings["batch_report_title"],
        strings["m_cancelled_t" if cancelled else "batch_done"],
        "",
        strings["batch_report_read"].format(read=len(read), total=total),
        strings["batch_saved"].format(saved=len(items) - len(failures), total=total),
        strings["batch_report_pages"].format(pages=sum(item["pages"] for item in read)),
    ]
    if cancelled:
        lines.append(strings["batch_report_remaining"].format(n=total - len(items)))
    partial = [item for item in items if item["kind"] == "ok" and item["unread"]]
    if partial:
        lines.append("")
        for item in partial:
            name = json.dumps(item["name"], ensure_ascii=False)
            unread = item["unread"]
            warning = strings["unread_1" if unread == 1 else "unread_n"].format(n=unread)
            lines.append(f"- {name}: {warning}")
    lines.extend(("", strings["batch_report_failures"].format(n=len(failures))))
    for item in failures:
        name = json.dumps(item["name"], ensure_ascii=False)
        lines.append(f"- {name}: {strings.get(item['kind'], strings['error'])}")
    return ("\n".join(lines) + "\n").encode("utf-8-sig", errors="backslashreplace")


def convert_folder(
    folder: Path,
    start_file: Callable[[str, int, int], None],
    report: Callable[[engine.Progress], None],
    cancel: threading.Event,
) -> BatchResult:
    files = sorted(
        (p for p in folder.iterdir() if not p.name.startswith(".") and not p.is_symlink() and p.is_file()),
        key=lambda p: (p.name.casefold(), p.name),
    )
    directory = None
    items = []
    for index, path in enumerate(files, 1):
        if cancel.is_set():
            break
        start_file(path.name, index, len(files))
        try:
            result = engine.convert(path, report=report, cancel=cancel)
        except engine.Cancelled:
            break
        except Exception:
            traceback.print_exc()
            items.append({"name": path.name, "kind": "error"})
            continue
        if cancel.is_set():
            break
        item = {"name": path.name, "kind": result.kind, "unread": result.unread}
        if result.kind == "ok":
            doc = result.doc
            item["pages"] = doc.page_count if doc.page_count is not None else len(doc.pages)
            try:
                data = exports.export(doc, "docx")
                if cancel.is_set():
                    break
                if directory is None:
                    directory = _new_directory(folder)
                item["output"] = _write_word(directory, path, data)
            except Exception:
                traceback.print_exc()
                item["kind"] = "batch_write_error"
        items.append(item)
    cancelled = cancel.is_set() and len(items) < len(files)
    report_path = None
    try:
        if directory is None:
            directory = _new_directory(folder)
        target = directory / REPORT_NAME
        _write_new_file(target, _report_bytes(items, len(files), cancelled))
        report_path = target
    except OSError:
        traceback.print_exc()
    return BatchResult(directory, items, len(files), cancelled, report_path)
