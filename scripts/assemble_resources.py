#!/usr/bin/env python3
"""Put the built Tesseract and its models into ``src/heocr_desktop/resources`` before Briefcase.

    # macOS: both architectures become one universal binary
    python scripts/assemble_resources.py build/tess/macos-arm64 build/tess/macos-x86_64
    # Windows
    python scripts/assemble_resources.py build/tess/windows-x64

It also fetches the two models (tessdata_fast 4.1.0 ``heb`` and ``eng``) and checks their
sha256 against ``tesseract/pins.json``. The resources folder is generated, never committed.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESOURCES = ROOT / "src" / "heocr_desktop" / "resources"
PINS = json.loads((ROOT / "tesseract" / "pins.json").read_text("utf-8"))
CACHE = ROOT / "build" / "tessdata-cache"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model(name: str, pin: dict) -> Path:
    cached = CACHE / name
    if not cached.is_file() or sha256(cached) != pin["sha256"]:
        CACHE.mkdir(parents=True, exist_ok=True)
        print("fetch", pin["url"], flush=True)
        with urllib.request.urlopen(pin["url"], timeout=120) as response:  # noqa: S310 - pinned https
            cached.write_bytes(response.read())
    if sha256(cached) != pin["sha256"]:
        sys.exit(f"sha256 mismatch for {name}")
    return cached


def main(dirs: list[str]) -> None:
    builds = [Path(d).resolve() for d in dirs]
    if not builds:
        sys.exit(__doc__)
    if RESOURCES.exists():
        shutil.rmtree(RESOURCES)
    (RESOURCES / "tesseract").mkdir(parents=True)
    (RESOURCES / "tessdata").mkdir()
    windows = (builds[0] / "tesseract.exe").is_file()
    exe = "tesseract.exe" if windows else "tesseract"
    target = RESOURCES / "tesseract" / exe
    if len(builds) > 1:
        subprocess.run(["lipo", "-create", *[str(b / exe) for b in builds], "-output", str(target)], check=True)
        subprocess.run(["lipo", "-info", str(target)], check=True)
    else:
        shutil.copy2(builds[0] / exe, target)
    target.chmod(0o755)
    shutil.copytree(builds[0] / "configs", RESOURCES / "tessdata" / "configs")
    for name, pin in PINS["tessdata"]["files"].items():
        shutil.copy2(model(name, pin), RESOURCES / "tessdata" / name)
    shutil.copytree(builds[0] / "licenses", RESOURCES / "licenses")
    info = [json.loads((b / "BUILD_INFO.json").read_text("utf-8")) for b in builds]
    (RESOURCES / "BUILD_INFO.json").write_text(json.dumps({"tesseract_builds": info, "tessdata": PINS["tessdata"]}, indent=2) + "\n", "utf-8")
    shutil.copy2(ROOT / "THIRD_PARTY_LICENSES.md", RESOURCES / "THIRD_PARTY_LICENSES.md")
    print("resources ready:", sorted(str(p.relative_to(RESOURCES)) for p in RESOURCES.rglob("*") if p.is_file() and "configs" not in p.parts and "licenses" not in p.parts))


if __name__ == "__main__":
    main(sys.argv[1:])
