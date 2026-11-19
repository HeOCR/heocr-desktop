#!/usr/bin/env python3
"""Put the built Tesseract and its models into ``src/heocr_desktop/resources`` before Briefcase.

    # macOS: both architectures become one universal binary
    python scripts/assemble_resources.py build/tess/macos-arm64 build/tess/macos-x86_64
    # Windows
    python scripts/assemble_resources.py build/tess/windows-x64
    # Android: models into src/heocr_mobile/resources, Tesseract into build/android/jniLibs
    python scripts/assemble_resources.py --android build/tess/android-arm64

It also fetches the two models (``heb`` from tessdata_best 4.1.0, ``eng`` from tessdata_fast
4.1.0) and checks their sha256 against ``tesseract/pins.json``. The resources folder is generated,
never committed.

On Android an app may run executables only from its native-library folder, so ``--android``
puts Tesseract at ``build/android/jniLibs/arm64-v8a/libtesseract_exec.so``; the Android build
copies that folder into the Gradle project.
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
MOBILE_RESOURCES = ROOT / "src" / "heocr_mobile" / "resources"
JNILIBS = ROOT / "build" / "android" / "jniLibs"
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
    android = "--android" in dirs
    builds = [Path(d).resolve() for d in dirs if d != "--android"]
    if not builds:
        sys.exit(__doc__)
    resources = MOBILE_RESOURCES if android else RESOURCES
    if resources.exists():
        shutil.rmtree(resources)
    resources.mkdir(parents=True)
    (resources / "tessdata").mkdir()
    windows = (builds[0] / "tesseract.exe").is_file()
    exe = "tesseract.exe" if windows else "tesseract"
    if android:
        abi = JNILIBS / "arm64-v8a"
        if JNILIBS.exists():
            shutil.rmtree(JNILIBS)
        abi.mkdir(parents=True)
        target = abi / "libtesseract_exec.so"
    else:
        (resources / "tesseract").mkdir()
        target = resources / "tesseract" / exe
    if len(builds) > 1:
        subprocess.run(["lipo", "-create", *[str(b / exe) for b in builds], "-output", str(target)], check=True)
        subprocess.run(["lipo", "-info", str(target)], check=True)
    else:
        shutil.copy2(builds[0] / exe, target)
    target.chmod(0o755)
    shutil.copytree(builds[0] / "configs", resources / "tessdata" / "configs")
    for name, pin in PINS["tessdata"]["files"].items():
        shutil.copy2(model(name, pin), resources / "tessdata" / name)
    shutil.copytree(builds[0] / "licenses", resources / "licenses")
    # Licence texts the bundled wheels do not carry themselves (third_party/<name>/). WebView2 is
    # Windows-only, so the Android app leaves it out.
    for folder in sorted((ROOT / "third_party").iterdir()):
        if android and folder.name == "webview2":
            continue
        if not android and folder.name == "fonts":  # the design's typefaces ship in the Android app only
            continue
        for text in sorted(folder.glob("*.txt")):
            shutil.copy2(text, resources / "licenses" / f"{folder.name}-{text.name}")
    info = [json.loads((b / "BUILD_INFO.json").read_text("utf-8")) for b in builds]
    (resources / "BUILD_INFO.json").write_text(json.dumps({"tesseract_builds": info, "tessdata": PINS["tessdata"]}, indent=2) + "\n", "utf-8")
    shutil.copy2(ROOT / "THIRD_PARTY_LICENSES.md", resources / "THIRD_PARTY_LICENSES.md")
    if android:
        # An invented sample page for the app's "Try a sample" button (the CI fixture, invented text).
        (resources / "sample").mkdir()
        shutil.copy2(ROOT / "tests" / "fixtures" / "garden-scan.png", resources / "sample" / "sample.png")
    print("resources ready:", sorted(str(p.relative_to(resources)) for p in resources.rglob("*") if p.is_file() and "configs" not in p.parts and "licenses" not in p.parts), "executable:", target)


if __name__ == "__main__":
    main(sys.argv[1:])
