"""Put Tesseract, its configs and licences, and the models into the app's resources.

    python scripts/vendor.py --tesseract vendor/     # the output of build_tesseract.py
    python scripts/vendor.py --tesseract vendor/ --models-cache build/models

Fills ``src/heocr_desktop/resources/``, which is never committed:

- ``tesseract/tesseract[.exe]``: on macOS, every ``tesseract-<arch>`` in the folder joined into one
  program with ``lipo`` (arm64, or universal with x86_64 too);
- ``tessdata/heb.traineddata`` and ``tessdata/eng.traineddata``, checked against their sha256;
- ``tessdata/configs/``, Tesseract's output configs (heocr uses ``tsv``);
- ``licenses/``, the licence texts of Tesseract's components and the models.

Downloads happen here, at build time, never in the app.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "src" / "heocr_desktop" / "resources"
MODELS = {
    "heb": ("https://github.com/tesseract-ocr/tessdata_best/raw/4.1.0/heb.traineddata",
            "dbaa827aea6bc21215638447f17783a1004987c2d0bf5573d111fee397abdae5"),
    "eng": ("https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/eng.traineddata",
            "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2"),
}
MODEL_LICENSE = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/4.1.0/LICENSE"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fetch(url: str, dest: Path, digest: str | None = None) -> Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"fetch {url}", flush=True)
        with urllib.request.urlopen(url, timeout=120) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
    if digest and sha256(dest) != digest:
        dest.unlink()
        raise SystemExit(f"{dest.name}: sha256 is not the pinned {digest}")
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tesseract", required=True, type=Path, help="build_tesseract.py's --out folder")
    ap.add_argument("--models-cache", type=Path, default=ROOT / "build" / "models")
    a = ap.parse_args()
    src = a.tesseract.resolve()

    shutil.rmtree(RES, ignore_errors=True)
    (RES / "tesseract").mkdir(parents=True)
    (RES / "tessdata").mkdir()
    (RES / "licenses").mkdir()

    if sys.platform == "win32":
        shutil.copy2(src / "tesseract.exe", RES / "tesseract" / "tesseract.exe")
    else:
        arches = sorted(src.glob("tesseract-*"))
        if not arches:
            raise SystemExit(f"no tesseract-<arch> in {src}")
        exe = RES / "tesseract" / "tesseract"
        if len(arches) == 1:
            shutil.copy2(arches[0], exe)
        else:
            subprocess.run(["lipo", "-create", *map(str, arches), "-output", str(exe)], check=True)
        exe.chmod(0o755)

    shutil.copytree(src / "configs", RES / "tessdata" / "configs")
    for lic in (src / "licenses").glob("*.txt"):
        shutil.copy2(lic, RES / "licenses" / lic.name)
    for name, (url, digest) in MODELS.items():
        cached = fetch(url, a.models_cache / f"{name}-{digest[:12]}.traineddata", digest)
        shutil.copy2(cached, RES / "tessdata" / f"{name}.traineddata")
    shutil.copy2(fetch(MODEL_LICENSE, a.models_cache / "tessdata-LICENSE"), RES / "licenses" / "tessdata-4.1.0.txt")
    for p in sorted(RES.rglob("*")):
        if p.is_file() and p.parent.name != "configs":
            print(f"{p.relative_to(RES)}  {p.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
