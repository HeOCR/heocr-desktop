import shutil
import threading
from pathlib import Path
from zipfile import ZipFile

import pypdfium2

from heocr_desktop import app, batch

FIX = Path(__file__).parent / "fixtures"


def test_batch_keeps_both_outputs_and_continues_after_unsupported_file(tmp_path):
    with pypdfium2.PdfDocument(FIX / "garden.pdf") as source, pypdfium2.PdfDocument.new() as two_pages:
        two_pages.import_pages(source, [0, 0])
        two_pages.save(tmp_path / "example.pdf")
    shutil.copy(FIX / "garden.docx", tmp_path / "example.docx")
    (tmp_path / "bad.bin").write_bytes(b"invented contents")
    shutil.copy(FIX / "garden.docx", tmp_path / ".hidden.docx")
    (tmp_path / "HeOCR").mkdir()
    shutil.copy(FIX / "garden.docx", tmp_path / "HeOCR" / "existing.docx")
    seen = []

    result = batch.convert_folder(tmp_path, lambda *info: seen.append(info), lambda p: None, threading.Event())

    assert result.directory == tmp_path / "HeOCR (2)"
    assert seen == [("bad.bin", 1, 3), ("example.docx", 2, 3), ("example.pdf", 3, 3)]
    assert [row["kind"] for row in result.items] == ["unsupported", "ok", "ok"]
    assert [row["output"] for row in result.items[1:]] == ["example.docx", "example (2).docx"]
    for row in result.items[1:]:
        with ZipFile(result.directory / row["output"]) as docx:
            assert b"<w:tbl>" in docx.read("word/document.xml")
    assert (tmp_path / "HeOCR" / "existing.docx").read_bytes() == (FIX / "garden.docx").read_bytes()
    assert result.report == result.directory / "batch-report.txt"
    report = result.report.read_text("utf-8-sig")
    assert "Files read: 2 of 3" in report
    assert "Pages in read files (where known): 2" in report
    assert "Failures: 1" in report
    assert '- "bad.bin": HeOCR cannot read this file type.' in report


def test_batch_cancel_keeps_completed_output(tmp_path):
    for name in ("a.docx", "b.docx"):
        shutil.copy(FIX / "garden.docx", tmp_path / name)
    cancel = threading.Event()

    def stop_during_second(name, index, total):
        if index == 2:
            cancel.set()

    result = batch.convert_folder(tmp_path, stop_during_second, lambda p: None, cancel)
    assert result.cancelled and result.total == 2
    assert sorted(p.name for p in result.directory.iterdir()) == ["a.docx", "batch-report.txt"]
    report = result.report.read_text("utf-8-sig")
    assert "Reading stopped" in report
    assert "Files not processed: 1" in report
    assert "Failures: 0" in report
    assert "b.docx" not in report


def test_folder_with_only_failures_saves_and_reveals_its_report(monkeypatch, tmp_path):
    (tmp_path / "bad.bin").write_bytes(b"invented contents")
    api = app.Api()
    revealed = []
    finished = []
    monkeypatch.setattr(app.reveal, "local_file", lambda path: revealed.append(path) or path)
    monkeypatch.setattr(api, "_push", lambda event, payload: finished.append(payload) if event == "heocr.finished" else None)

    assert api._begin()
    api._run_folder(tmp_path)

    report = tmp_path / "HeOCR" / "batch-report.txt"
    assert revealed == [report]
    assert finished[0]["saved"] == 0 and finished[0]["reveal"] and not finished[0]["report_error"]
    assert "Files read: 0 of 1" in report.read_text("utf-8-sig")


def test_report_write_failure_keeps_completed_word_file(monkeypatch, tmp_path):
    shutil.copy(FIX / "garden.docx", tmp_path / "document.docx")
    write_new_file = batch._write_new_file

    def write_file(target, data):
        if target.name == "batch-report.txt":
            raise PermissionError("test failure")
        write_new_file(target, data)

    monkeypatch.setattr(batch, "_write_new_file", write_file)
    result = batch.convert_folder(tmp_path, lambda *info: None, lambda p: None, threading.Event())
    assert result.report is None
    assert result.items[0]["kind"] == "ok"
    assert (result.directory / "document.docx").is_file()


def test_folder_picker_needs_confirmation_before_saving(monkeypatch, tmp_path):
    shutil.copy(FIX / "garden.docx", tmp_path / "document.docx")
    api = app.Api()
    finished = threading.Event()
    messages = []

    class Window:
        def create_file_dialog(self, dialog):
            from webview import FileDialog
            assert dialog == FileDialog.FOLDER
            return (str(tmp_path),)

    def push(function, payload):
        if function == "heocr.finished":
            messages.append(payload)
            finished.set()

    api._window = Window()
    monkeypatch.setattr(api, "_push", push)
    assert api.open_folder() == tmp_path.name
    assert not (tmp_path / "HeOCR").exists()
    assert api.start_folder()
    assert finished.wait(timeout=10)
    assert (messages[0]["kind"], messages[0]["saved"], messages[0]["total"]) == ("batch", 1, 1)
    assert (tmp_path / "HeOCR" / "document.docx").is_file()
    assert (tmp_path / "HeOCR" / "batch-report.txt").is_file()
