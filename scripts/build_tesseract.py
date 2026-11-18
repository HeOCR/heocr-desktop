"""Build the Tesseract the app bundles, from pinned sources, with permissive parts only.

heocr hands Tesseract PNG images only, so Tesseract needs Leptonica with PNG and zlib, and nothing else:
no libarchive, no curl, no training tools, no other image formats. Everything is linked statically, so
the result is one program that depends only on the operating system.

    python scripts/build_tesseract.py --out vendor              # this machine's architecture
    python scripts/build_tesseract.py --out vendor --arch x86_64 # macOS: cross-build for Intel

Writes ``vendor/tesseract[.exe]``, ``vendor/configs/`` (Tesseract's output configs; heocr uses ``tsv``)
and ``vendor/licenses/`` (each component's licence text). Every download is checked against its
sha256 below. Run in CI (GitHub Actions); it takes a few minutes and a C++ compiler and CMake.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

SOURCES = {
    "zlib": ("1.3.1", "https://github.com/madler/zlib/releases/download/v1.3.1/zlib-1.3.1.tar.gz",
             "9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23"),
    "libpng": ("1.6.58", "https://github.com/pnggroup/libpng/archive/refs/tags/v1.6.58.tar.gz",
               "a9d4df463d36a6e5f9c29bd6f4967312d17e996c1854f3511f833924eb1993cf"),
    "leptonica": ("1.87.0", "https://github.com/DanBloomberg/leptonica/releases/download/1.87.0/leptonica-1.87.0.tar.gz",
                  "c73363397f96eb1295602bf44d708a994ad42046c791bf03ea0505d829bdb6a7"),
    "tesseract": ("5.5.3", "https://github.com/tesseract-ocr/tesseract/archive/refs/tags/5.5.3.tar.gz",
                  "9218e62793116d42a9f6d14cd9348518b27f382096eea3d0f2d1a24616bb5884"),
}
# Licence files inside each source tree.
LICENSE_FILES = {"zlib": "LICENSE", "libpng": "LICENSE", "leptonica": "leptonica-license.txt", "tesseract": "LICENSE"}
WINDOWS = sys.platform == "win32"
MACOS = sys.platform == "darwin"
MACOS_MIN = "11.0"


def sh(cmd, cwd=None, env=None):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], cwd=cwd, env=env, check=True)


def fetch(name: str, cache: Path) -> Path:
    version, url, sha = SOURCES[name]
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{name}-{version}.tar.gz"
    if not path.exists():
        print(f"fetch {url}", flush=True)
        with urllib.request.urlopen(url, timeout=120) as r, open(path, "wb") as f:
            shutil.copyfileobj(r, f)
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != sha:
        path.unlink()
        raise SystemExit(f"{name}: sha256 {got} is not the pinned {sha}")
    return path


def unpack(archive: Path, into: Path) -> Path:
    with tarfile.open(archive) as tf:
        top = tf.getnames()[0].split("/")[0]
        tf.extractall(into, filter="data")
    return into / top


def cmake(src: Path, build: Path, prefix: Path, arch: str | None, *flags: str):
    args = ["cmake", "-S", src, "-B", build, f"-DCMAKE_INSTALL_PREFIX={prefix}", f"-DCMAKE_PREFIX_PATH={prefix}",
            "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"]
    if MACOS:
        args += [f"-DCMAKE_OSX_DEPLOYMENT_TARGET={MACOS_MIN}", f"-DCMAKE_OSX_ARCHITECTURES={arch}"]
    if WINDOWS:
        # Static C runtime everywhere (no VC++ redistributable). The policy makes older CMakeLists honour it.
        args += ["-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded", "-DCMAKE_POLICY_DEFAULT_CMP0091=NEW"]
    sh(args + list(flags))
    sh(["cmake", "--build", build, "--config", "Release", "--parallel", str(os.cpu_count() or 2)])
    sh(["cmake", "--install", build, "--config", "Release"])


def _static_only(prefix: Path, name: str, static: str) -> None:
    """Windows: make ``name.lib`` the static library, and drop the DLL, so nothing links it dynamically."""
    lib = prefix / "lib"
    shutil.copy2(lib / f"{static}.lib", lib / f"{name}.lib")
    for dll in (prefix / "bin").glob(f"{name.replace('lib', '', 1) if name.startswith('lib') else name}*.dll"):
        dll.unlink()
    for dll in (prefix / "bin").glob(f"{name}*.dll"):
        dll.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--work", type=Path, default=Path("build/tesseract-src"))
    ap.add_argument("--arch", default=platform.machine() if MACOS else None)
    a = ap.parse_args()
    work, out = a.work.resolve(), a.out.resolve()
    prefix = work / f"prefix-{a.arch or 'native'}"
    shutil.rmtree(prefix, ignore_errors=True)
    srcs = {}
    for name in SOURCES:
        srcs[name] = unpack(fetch(name, work / "cache"), work / "src")

    # zlib: macOS has it in the system; Windows gets a static one.
    if WINDOWS:
        cmake(srcs["zlib"], work / "b-zlib", prefix, a.arch, "-DZLIB_BUILD_EXAMPLES=OFF")
        _static_only(prefix, "zlib", "zlibstatic")
    cmake(srcs["libpng"], work / f"b-png-{a.arch}", prefix, a.arch,
          "-DPNG_SHARED=OFF", "-DPNG_STATIC=ON", "-DPNG_TESTS=OFF", "-DPNG_TOOLS=OFF", "-DPNG_FRAMEWORK=OFF",
          *(["-DPNG_ARM_NEON=off"] if MACOS and a.arch == "x86_64" else []))
    if WINDOWS:
        _static_only(prefix, "libpng16", "libpng16_static")
    cmake(srcs["leptonica"], work / f"b-lept-{a.arch}", prefix, a.arch,
          "-DSW_BUILD=OFF", "-DBUILD_PROG=OFF", "-DENABLE_ZLIB=ON", "-DENABLE_PNG=ON", "-DENABLE_GIF=OFF",
          "-DENABLE_JPEG=OFF", "-DENABLE_TIFF=OFF", "-DENABLE_WEBP=OFF", "-DENABLE_OPENJPEG=OFF")
    cmake(srcs["tesseract"], work / f"b-tess-{a.arch}", prefix, a.arch,
          "-DENABLE_NATIVE=OFF", "-DBUILD_TRAINING_TOOLS=OFF", "-DBUILD_TESTS=OFF", "-DDISABLE_ARCHIVE=ON",
          "-DDISABLE_CURL=ON", "-DGRAPHICS_DISABLED=ON", "-DOPENMP_BUILD=OFF", "-DENABLE_LTO=OFF",
          "-DDISABLE_TIFF=ON", "-DINSTALL_CONFIGS=ON", f"-DLeptonica_DIR={prefix / 'lib' / 'cmake' / 'leptonica'}")

    out.mkdir(parents=True, exist_ok=True)
    exe = "tesseract.exe" if WINDOWS else "tesseract"
    built = prefix / "bin" / exe
    target = out / (exe if not MACOS else f"tesseract-{a.arch}")
    shutil.copy2(built, target)
    configs = srcs["tesseract"] / "tessdata" / "configs"
    shutil.copytree(configs, out / "configs", dirs_exist_ok=True)
    lic = out / "licenses"
    lic.mkdir(exist_ok=True)
    for name, rel in LICENSE_FILES.items():
        if name == "zlib" and not WINDOWS:
            continue
        src = srcs[name] / rel
        if not src.exists():  # licence file names move between releases
            src = next(p for p in srcs[name].iterdir() if p.name.lower().startswith(("license", "copying", "leptonica-license")))
        shutil.copy2(src, lic / f"{name}-{SOURCES[name][0]}.txt")
    print(f"built {target}")
    sh([target, "--version"])


if __name__ == "__main__":
    main()
