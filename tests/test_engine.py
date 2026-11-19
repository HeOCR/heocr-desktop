import os
import socket
from pathlib import Path

import pytest

from heocr_desktop import engine

FIX = Path(__file__).resolve().parent / "fixtures"
HAS_OCR = engine.tesseract_path() is not None and engine.tessdata_path() is not None


def test_offline_guard_refuses_outside_connections():
    engine.install_offline_guard()
    with pytest.raises(OSError):
        socket.create_connection(("192.0.2.1", 80), timeout=1)  # TEST-NET-1, never routed
    with pytest.raises(OSError):
        socket.getaddrinfo("example.org", 443)


def test_offline_guard_keeps_loopback():
    engine.install_offline_guard()
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    client = socket.create_connection(server.getsockname(), timeout=2)
    client.close()
    server.close()


def test_born_digital_pdf_uses_the_text_layer():
    result = engine.convert(FIX / "garden.pdf")
    assert result.kind == "ok"
    assert result.routes == {"text_layer": 1}
    assert "גינה קהילתית ברחוב הדקלים" in result.doc.text
    assert any(b.kind == "table" for b in result.doc.blocks)


def test_docx_keeps_headings_and_table():
    result = engine.convert(FIX / "garden.docx")
    assert result.kind == "ok"
    kinds = [b.kind for b in result.doc.blocks]
    assert kinds.count("heading") == 3 and "table" in kinds
    assert "| שקי אדמה | 20 | 1,400 |" in result.doc.markdown


def test_doc_needs_a_converter_and_says_so():
    result = engine.convert(FIX / "garden.doc")
    assert result.kind == "needs_converter"


def test_progress_reports_pages():
    seen = []
    engine.convert(FIX / "garden.pdf", report=seen.append)
    stages = [p.stage for p in seen]
    assert stages[0] == "reading" and "pages" in stages and stages[-1] == "finishing"
    assert any(p.total == 1 for p in seen if p.stage == "pages")


def test_cancel_stops_before_the_first_page():
    import threading

    stop = threading.Event()
    stop.set()
    with pytest.raises(engine.Cancelled):
        engine.convert(FIX / "garden.pdf", report=lambda p: None, cancel=stop)


def test_progress_hook_does_not_change_the_reading():
    import heocr

    plain = heocr.extract(str(FIX / "garden.pdf"), ocr=False, convert=False).to_dict()
    hooked = engine.convert(FIX / "garden.pdf").doc.to_dict()
    plain["producer"].pop("components"), hooked["producer"].pop("components")
    for d in (plain, hooked):
        d["options"].pop("ocr", None)
    assert plain["blocks"] == hooked["blocks"] and plain["pages"] == hooked["pages"]


@pytest.mark.skipif(not HAS_OCR, reason="no bundled Tesseract (set HEOCR_DESKTOP_DEV_TESSERACT/TESSDATA)")
@pytest.mark.parametrize("name", ["garden-scan.png", "garden-scan.jpg", "garden-scan.tiff", "garden-scan.pdf"])
def test_scans_go_through_ocr(name):
    result = engine.convert(FIX / name)
    assert result.kind == "ok"
    assert result.routes.get("ocr") == 1
    assert "הדקלים" in result.doc.text


def test_errors_are_not_retried(monkeypatch):
    import heocr

    def broken(path, **kwargs):
        raise ValueError("something else")

    monkeypatch.setattr(heocr, "extract", broken)
    with pytest.raises(ValueError):
        engine.convert(FIX / "garden.pdf")


def test_configure_points_the_engine_elsewhere(monkeypatch, tmp_path):
    monkeypatch.setattr(engine, "_CONFIGURED", {})
    exe, data = tmp_path / "libtesseract_exec.so", tmp_path / "tessdata"
    engine.configure(tesseract=exe, tessdata=data)
    assert engine.tesseract_path() == exe
    assert engine.tessdata_path() == data
