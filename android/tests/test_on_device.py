"""On the phone (the Android emulator in CI): the bundled Tesseract runs, the network is refused by
Android itself, and every fixture reads as on the desktop (``heocr_desktop.smoke``).

The fixtures (invented text only) are copied here from ``tests/fixtures`` by the CI job.
"""

import json
import socket
import subprocess
from pathlib import Path

import pytest

from heocr_desktop import engine, smoke
from heocr_mobile import device

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
    code = smoke.run(str(FIXTURES))
    report = json.loads((FIXTURES / "smoke-report.json").read_text("utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert code == 0 and report["ok"], report
