"""Read the regular files directly inside one folder and save Word copies."""

from __future__ import annotations

import threading
import traceback
from dataclasses import dataclass
from itertools import count
from pathlib import Path
from typing import Callable

from heocr_desktop import engine, exports


@dataclass
class BatchResult:
    directory: Path | None
    items: list[dict]
    total: int
    cancelled: bool


def _new_directory(folder: Path) -> Path:
    for n in count(1):
        candidate = folder / ("HeOCR" if n == 1 else f"HeOCR ({n})")
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue


def _write_word(directory: Path, source: Path, data: bytes) -> str:
    for n in count(1):
        stem = source.stem if n == 1 else f"{source.stem} ({n})"
        target = directory / f"{stem}.docx"
        try:
            stream = target.open("xb")
        except FileExistsError:
            continue
        try:
            with stream:
                stream.write(data)
        except OSError:
            target.unlink(missing_ok=True)
            raise
        return target.name


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
            try:
                data = exports.export(result.doc, "docx")
                if cancel.is_set():
                    break
                if directory is None:
                    directory = _new_directory(folder)
                item["output"] = _write_word(directory, path, data)
            except Exception:
                traceback.print_exc()
                item["kind"] = "batch_write_error"
        items.append(item)
    return BatchResult(directory, items, len(files), cancel.is_set() and len(items) < len(files))
