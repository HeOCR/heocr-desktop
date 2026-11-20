"""On the phone (the Android emulator in CI): the bundled Tesseract runs, the network is refused by
Android itself, and every fixture reads as on the desktop (``heocr_desktop.smoke``).

The fixtures (invented text only) are copied here from ``tests/fixtures`` by the CI job.
"""

import json
import socket
import subprocess
from pathlib import Path

import pytest

from heocr_desktop import diagnostics, engine, smoke
from heocr_mobile import device, view

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="module", autouse=True)
def prepared():
    device.prepare()


def test_bundled_tesseract_runs():
    exe = engine.tesseract_path()
    assert exe is not None and exe.is_file(), exe
    out = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=60)
    print(out.stdout or out.stderr)
    assert "tesseract 5.5.3" in (out.stdout + out.stderr)
    assert "libcurl" not in out.stdout + out.stderr


def test_models_are_the_pinned_files():
    folder = engine.tessdata_path()
    info = json.loads((device.RESOURCES / "BUILD_INFO.json").read_text("utf-8"))
    import hashlib

    for name, pin in info["tessdata"]["files"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == pin["sha256"], name


def test_android_refuses_the_network():
    # No INTERNET permission in the manifest: the kernel refuses to create an internet socket.
    with pytest.raises(PermissionError):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def test_fixtures_read_as_on_the_desktop():
    code = smoke.run(str(FIXTURES), resources=device.RESOURCES)
    report = json.loads((FIXTURES / "smoke-report.json").read_text("utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert code == 0 and report["ok"], report


def test_reads_with_heocrs_bundled_modern_model():
    # heocr 0.2's default: HeOCR's own modern-print model, from inside the heocr package, not stock heb.
    result = engine.convert(FIXTURES / "garden-scan.png")
    assert result.kind == "ok"
    assert "heocr_modern_v1" in view.ocr_models(result.doc), sorted(result.doc.components)
    assert "bundled_model_unavailable" not in result.doc.flags


ITEXT = FIXTURES / "itext-style.pdf"  # invented, generated in CI by scripts/make_itext_style_pdf.py


def test_picker_intent_carries_a_java_string_array():
    # Built for real, as "Open a file" builds it: a Python list there made the button fail silently.
    intent = device.open_document_intent()
    types = intent.getStringArrayExtra(device._jclass("android.content.Intent").EXTRA_MIME_TYPES)
    assert types is not None and [str(t) for t in types] == list(device.MIME_TYPES)


def _provider_uri(path):
    context = device._android_context()
    pm = context.getPackageManager()
    info = pm.getPackageInfo(context.getPackageName(), device._jclass("android.content.pm.PackageManager").GET_PROVIDERS)
    authority = str(info.providers[0].authority)
    FileProvider = device._jclass("androidx.core.content.FileProvider")
    return FileProvider.getUriForFile(context, authority, device._jclass("java.io.File")(str(path)))


def test_a_shared_document_is_copied_byte_for_byte(tmp_path):
    # The share path: a content URI from a provider (the app's own FileProvider here), copied in.
    context = device._android_context()
    shared = Path(str(context.getCacheDir().getAbsolutePath())) / "shared"
    shared.mkdir(parents=True, exist_ok=True)
    source = shared / "copy-test.pdf"
    source.write_bytes(ITEXT.read_bytes())
    uri = _provider_uri(source)
    assert device.declared_size(uri) == source.stat().st_size
    copied, size = device.copy_to(uri, tmp_path)
    assert size == source.stat().st_size and copied.read_bytes() == source.read_bytes()


def test_an_itext_style_bill_reads_from_its_text_layer_as_on_the_host():
    # Two pages of CID fonts with Identity-H and ToUnicode, one font not embedded, a JPEG logo, an
    # incremental update: heocr must read both pages from the text layer, exactly as on the CI host.
    expected = json.loads((FIXTURES / "itext-style.expected.json").read_text("utf-8"))
    result = engine.convert(ITEXT)
    got = diagnostics.page_structure(result.doc)
    print(json.dumps(got, indent=1))
    assert [p["route"] for p in got] == ["text_layer", "text_layer"], got
    assert got == expected["pages"], (got, expected["pages"])


def test_save_intent_carries_its_file_name():
    Intent = device._jclass("android.content.Intent")
    intent = device.create_document_intent("garden.txt", "text/plain")
    assert str(intent.getAction()) == str(Intent.ACTION_CREATE_DOCUMENT)
    assert str(intent.getStringExtra(Intent.EXTRA_TITLE)) == "garden.txt" and str(intent.getType()) == "text/plain"
