#!/usr/bin/env python3
"""Build Pillow for Android (arm64-v8a, CPython 3.13), at the version heocr's release gate ran with.

    python scripts/build_pillow_android.py --deps build/tess/android-arm64/deps --out build/android-wheels

Pillow publishes iOS wheels but no Android ones, so the Android app needs its own build. The
sdist comes from PyPI, checked against the sha256 below. cibuildwheel cross-builds it with the
Android NDK and links the static image libraries from ``scripts/build_tesseract.py --target
android-arm64`` (``deps/``), the same libraries Leptonica uses. Runs in CI on Linux, with
``ANDROID_HOME`` set (GitHub's Ubuntu runners have it).

Pillow's optional features: zlib, JPEG, TIFF, WebP and JPEG 2000 on (the formats heocr reads);
FreeType, LittleCMS, libimagequant, XCB, Raqm and AVIF off (heocr does not use them).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PILLOW = {
    "version": "13.0.0",
    "url": "https://files.pythonhosted.org/packages/ce/a4/9cc30690a394a8305e8be4c9036aa16d0dfddadd09079860b582f562496d/pillow-13.0.0.tar.gz",
    "sha256": "cdcd1ba258178f7356d74170c9a81ba4eab6a5d55748bc402a5a2a6fe6be3510",
}
CIBUILDWHEEL = "4.3.5"
BUILD = "cp313-android_arm64_v8a"
ON = ("zlib", "jpeg", "tiff", "webp", "jpeg2000")
OFF = ("freetype", "lcms", "imagequant", "xcb", "raqm", "avif")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Static libraries that need another one Pillow does not name: libtiff (compressed with lzma) and
# libwebp (which calls libsharpyuv). cibuildwheel sets LDFLAGS itself for Android, so extra -l flags
# do not reach the linker; instead each gets a copy with its dependency's objects folded in.
FOLD = {"libtiff.a": ["liblzma.a"], "libwebp.a": ["libsharpyuv.a"]}


def llvm_tool(name: str) -> Path:
    ndk = Path(os.environ.get("ANDROID_NDK_HOME") or os.environ.get("ANDROID_NDK_LATEST_HOME") or "")
    tools = sorted((ndk / "toolchains" / "llvm" / "prebuilt").glob(f"*/bin/{name}"))
    if not tools:
        sys.exit(f"{name} not found: set ANDROID_NDK_HOME")
    return tools[0]


def pillow_deps(deps: Path, work: Path) -> Path:
    """A copy of deps/ in which libtiff.a and libwebp.a carry what they depend on."""
    out = work / "deps"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(deps, out)
    ar = llvm_tool("llvm-ar")
    for lib, extra in FOLD.items():
        script = [f"create {out / 'lib' / lib}.merged", f"addlib {deps / 'lib' / lib}"]
        script += [f"addlib {deps / 'lib' / e}" for e in extra] + ["save", "end"]
        subprocess.run([str(ar), "-M"], input="\n".join(script) + "\n", text=True, check=True)
        (out / "lib" / f"{lib}.merged").replace(out / "lib" / lib)
    return out


def strip_debug_symbols(wheel: Path, work: Path) -> None:
    """Strip detached DWARF sections and repack with a fresh RECORD and the original licences."""
    with tempfile.TemporaryDirectory(dir=work) as tmp:
        stage = Path(tmp)
        subprocess.run([sys.executable, "-m", "wheel", "unpack", "--dest", stage, wheel], check=True)
        unpacked, = stage.iterdir()
        libraries = sorted((unpacked / "PIL").glob("*.so"))
        if not libraries:
            sys.exit(f"no Pillow native libraries in {wheel.name}")
        before = sum(path.stat().st_size for path in libraries)
        subprocess.run([llvm_tool("llvm-strip"), "--strip-debug", *libraries], check=True)
        after = sum(path.stat().st_size for path in libraries)
        subprocess.run([sys.executable, "-m", "wheel", "pack", "--dest-dir", stage, unpacked], check=True)
        (stage / wheel.name).replace(wheel)
        print(f"Pillow native libraries: {before:,} to {after:,} bytes after stripping debug symbols", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deps", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--work", type=Path, default=Path("build") / "pillow-android")
    a = ap.parse_args()
    deps, out, work = a.deps.resolve(), a.out.resolve(), a.work.resolve()
    if not (deps / "lib").is_dir():
        sys.exit(f"no static libraries in {deps}/lib; build Tesseract for android-arm64 first")
    work.mkdir(parents=True, exist_ok=True)
    sdist = work / Path(PILLOW["url"]).name
    if not sdist.is_file() or sha256(sdist) != PILLOW["sha256"]:
        print("fetch", PILLOW["url"], flush=True)
        with urllib.request.urlopen(PILLOW["url"], timeout=120) as response:  # noqa: S310 - pinned https
            sdist.write_bytes(response.read())
    if sha256(sdist) != PILLOW["sha256"]:
        sys.exit("sha256 mismatch for the Pillow sdist")

    subprocess.run([sys.executable, "-m", "pip", "install", "-q", f"cibuildwheel=={CIBUILDWHEEL}", "wheel==0.48.0"], check=True)
    deps = pillow_deps(deps, work)
    roots = " ".join(f"{name}={deps}" for name in ("ZLIB_ROOT", "JPEG_ROOT", "TIFF_ROOT", "WEBP_ROOT", "JPEG2K_ROOT"))
    env = dict(
        os.environ,
        CIBW_BUILD=BUILD,
        CIBW_ARCHS="arm64_v8a",
        CIBW_BUILD_VERBOSITY="1",
        CIBW_CONFIG_SETTINGS=" ".join(["platform-guessing=disable", *(f"{f}=enable" for f in ON), *(f"{f}=disable" for f in OFF)]),
        CIBW_ENVIRONMENT=roots,
        # Pillow's own [tool.cibuildwheel] builds its dependencies with a script that is not in the
        # sdist, and tests with numpy; here the dependencies come from deps/ and tests run on the
        # app (android/tests). Environment variables take precedence over pyproject.toml.
        CIBW_BEFORE_ALL="true",
        CIBW_TEST_COMMAND="",
        CIBW_TEST_REQUIRES="",
        CIBW_TEST_EXTRAS="",
    )
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    subprocess.run([sys.executable, "-m", "cibuildwheel", "--platform", "android", "--output-dir", str(out), str(sdist)], check=True, env=env)
    wheels = sorted(out.glob("pillow-*.whl"))
    if len(wheels) != 1:
        sys.exit(f"expected one wheel, got {[w.name for w in wheels]}")
    strip_debug_symbols(wheels[0], work)
    info = {
        "pillow": PILLOW,
        "cibuildwheel": CIBUILDWHEEL,
        "build": BUILD,
        "features_on": ON,
        "features_off": OFF,
        "wheel": wheels[0].name,
        "wheel_sha256": sha256(wheels[0]),
    }
    (out / "BUILD_INFO-pillow.json").write_text(json.dumps(info, indent=2) + "\n", "utf-8")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
