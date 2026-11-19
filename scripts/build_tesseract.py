#!/usr/bin/env python3
"""Build the Tesseract that HeOCR desktop ships: one static executable, no network code.

    python scripts/build_tesseract.py --target macos-arm64 --out build/tess/macos-arm64
    python scripts/build_tesseract.py --target macos-x86_64 --out build/tess/macos-x86_64
    python scripts/build_tesseract.py --target windows-x64 --out build/tess/windows-x64
    python scripts/build_tesseract.py --target android-arm64 --out build/tess/android-arm64   # on Linux, with $ANDROID_NDK_HOME

What it does, all from pinned sources (tesseract/pins.json, tesseract/vcpkg.json):

1. vcpkg (pinned tag) builds Leptonica 1.87.0 and its image libraries (zlib, libpng,
   libjpeg-turbo, libtiff, giflib, libwebp, OpenJPEG), static, release only.
2. Tesseract 5.5.3, from its release tarball (sha256 checked), is built with CMake against them:
   static, no training tools, no ScrollView, **no libcurl and no libarchive** (so the binary
   cannot fetch URLs), no OpenMP.
3. The output folder gets ``tesseract`` (``tesseract.exe``), Tesseract's ``configs`` (heocr
   needs ``configs/tsv``), and every component's licence text under ``licenses/``.
4. It checks the executable links only to the operating system's own libraries.

For Android the executable is cross-built with the NDK (API 24, arm64-v8a, static C++ runtime). The
output also gets ``deps/`` (the static image libraries and their headers), which the Android build
of Pillow links against (``scripts/build_pillow_android.py``), so both read images with the same
libraries.

This runs in CI (``.github/workflows/tesseract.yml``); a local run needs CMake, Ninja, git
and a compiler. It takes a few minutes of full CPU: on the maintainer's Mac it goes through the
power scheduler.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESS = ROOT / "tesseract"
PINS = json.loads((TESS / "pins.json").read_text("utf-8"))

TARGETS = {
    "macos-arm64": {"triplet": "arm64-osx-heocr", "arch": "arm64"},
    "macos-x86_64": {"triplet": "x64-osx-heocr", "arch": "x86_64"},
    "windows-x64": {"triplet": "x64-windows-heocr", "arch": "x64"},
    "android-arm64": {"triplet": "arm64-android-heocr", "arch": "arm64-v8a", "api": 24},
}

# Shared libraries the executable may load: the OS's own, nothing bundled.
MAC_ALLOWED = re.compile(r"^(/usr/lib/|/System/Library/)")
ANDROID_ALLOWED = {"libc.so", "libm.so", "libdl.so", "liblog.so"}
WIN_ALLOWED = {
    "kernel32.dll", "user32.dll", "advapi32.dll", "ws2_32.dll", "shell32.dll", "ole32.dll",
    "oleaut32.dll", "gdi32.dll", "comdlg32.dll", "shlwapi.dll", "bcrypt.dll", "crypt32.dll",
}


def run(cmd: list[str], **kwargs) -> None:
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kwargs)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, digest: str) -> Path:
    if not dest.is_file() or sha256(dest) != digest:
        dest.parent.mkdir(parents=True, exist_ok=True)
        print("fetch", url, flush=True)
        with urllib.request.urlopen(url, timeout=120) as response, dest.open("wb") as out:  # noqa: S310 - pinned https
            shutil.copyfileobj(response, out)
    got = sha256(dest)
    if got != digest:
        sys.exit(f"sha256 mismatch for {url}: {got} != {digest}")
    return dest


def ndk_revision(ndk: Path) -> str:
    """The NDK's Pkg.Revision, recorded so an Android build says which NDK made it."""
    props = (ndk / "source.properties").read_text("utf-8")
    match = re.search(r"Pkg\.Revision\s*=\s*(\S+)", props)
    return match.group(1) if match else "unknown"


def vcpkg_root(work: Path) -> Path:
    pin = PINS["vcpkg"]
    root = work / "vcpkg"
    if not (root / ".git").is_dir():
        run(["git", "clone", "--filter=blob:none", "https://github.com/microsoft/vcpkg", root])
    run(["git", "-C", root, "fetch", "--depth=1", "origin", pin["commit"]])
    run(["git", "-C", root, "checkout", "--quiet", pin["commit"]])
    exe = root / ("vcpkg.exe" if os.name == "nt" else "vcpkg")
    if not exe.is_file():
        boot = root / ("bootstrap-vcpkg.bat" if os.name == "nt" else "bootstrap-vcpkg.sh")
        run([boot, "-disableMetrics"], shell=os.name == "nt")
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--target", required=True, choices=sorted(TARGETS))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--work", type=Path, default=ROOT / "build" / "tess-work")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    args = parser.parse_args()
    target = TARGETS[args.target]
    work = args.work.resolve()
    out = args.out.resolve()
    work.mkdir(parents=True, exist_ok=True)
    windows = args.target.startswith("windows")
    android = args.target.startswith("android")
    ndk = Path(os.environ.get("ANDROID_NDK_HOME", "")) if android else None
    if android and not (ndk / "build" / "cmake" / "android.toolchain.cmake").is_file():
        sys.exit("android targets need ANDROID_NDK_HOME pointing at an Android NDK")

    # 1. Leptonica and image libraries.
    root = vcpkg_root(work)
    installed = work / "vcpkg_installed"
    env = dict(os.environ, VCPKG_DISABLE_METRICS="1")
    run(
        [
            root / ("vcpkg.exe" if windows else "vcpkg"),
            "install",
            f"--triplet={target['triplet']}",
            f"--overlay-triplets={TESS / 'triplets'}",
            f"--x-manifest-root={TESS}",
            f"--x-install-root={installed}",
            "--clean-after-build",
        ],
        env=env,
    )
    prefix = installed / target["triplet"]

    # 2. Tesseract.
    pin = PINS["tesseract"]
    tarball = fetch(pin["url"], work / f"tesseract-{pin['version']}.tar.gz", pin["sha256"])
    src = work / f"tesseract-{pin['version']}"
    if not src.is_dir():
        with tarfile.open(tarball) as tar:
            tar.extractall(work, filter="data")
    build = work / f"build-{args.target}"
    configure = [
        "cmake", "-S", src, "-B", build, "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_TOOLCHAIN_FILE={root / 'scripts' / 'buildsystems' / 'vcpkg.cmake'}",
        f"-DVCPKG_TARGET_TRIPLET={target['triplet']}",
        f"-DVCPKG_OVERLAY_TRIPLETS={TESS / 'triplets'}",
        f"-DVCPKG_INSTALLED_DIR={installed}",
        "-DVCPKG_MANIFEST_MODE=OFF",
        f"-DCMAKE_PREFIX_PATH={prefix}",
        f"-DCMAKE_INSTALL_PREFIX={build / 'install'}",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_TRAINING_TOOLS=OFF",
        "-DBUILD_TESTS=OFF",
        "-DGRAPHICS_DISABLED=ON",
        "-DDISABLE_CURL=ON",
        "-DDISABLE_ARCHIVE=ON",
        "-DOPENMP_BUILD=OFF",
        "-DENABLE_NATIVE=OFF",
        "-DENABLE_CCACHE=OFF",
        "-DSW_BUILD=OFF",
        "-DINSTALL_CONFIGS=ON",
    ]
    if windows:
        configure += ["-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded", "-DCMAKE_POLICY_DEFAULT_CMP0091=NEW"]
    elif android:
        configure += [
            f"-DVCPKG_CHAINLOAD_TOOLCHAIN_FILE={ndk / 'build' / 'cmake' / 'android.toolchain.cmake'}",
            f"-DANDROID_ABI={target['arch']}",
            f"-DANDROID_PLATFORM=android-{target['api']}",
            "-DANDROID_STL=c++_static",
        ]
    else:
        configure += [f"-DCMAKE_OSX_ARCHITECTURES={target['arch']}", "-DCMAKE_OSX_DEPLOYMENT_TARGET=13.0"]
        if target["arch"] == "x86_64" and platform.machine() == "arm64":
            # x86_64 on Apple silicon: Tesseract picks its SIMD code (NEON or AVX/SSE) from
            # CMAKE_SYSTEM_PROCESSOR, which CMake sets from the host. Treat the host as x86_64
            # (its configure checks then run under Rosetta) rather than cross-compiling, which
            # would refuse Leptonica's try_run.
            configure += ["-DCMAKE_APPLE_SILICON_PROCESSOR=x86_64"]
    run(configure)
    run(["cmake", "--build", build, "--parallel", str(args.jobs), "--target", "tesseract"])

    # 3. Collect.
    if out.exists():
        shutil.rmtree(out)
    (out / "licenses").mkdir(parents=True)
    exe_name = "tesseract.exe" if windows else "tesseract"
    exe = next(p for p in build.rglob(exe_name) if p.is_file() and p.parent.name != "CMakeFiles")
    shutil.copy2(exe, out / exe_name)
    if android:
        strip = next((ndk / "toolchains" / "llvm" / "prebuilt").glob("*/bin/llvm-strip"))
        run([strip, "--strip-unneeded", out / exe_name])
    elif not windows:
        run(["strip", "-x", out / exe_name])
    shutil.copytree(src / "tessdata" / "configs", out / "configs")
    shutil.copy2(src / "LICENSE", out / "licenses" / "tesseract-LICENSE.txt")
    for copyright_file in sorted((prefix / "share").glob("*/copyright")):
        port = copyright_file.parent.name
        if port.startswith("vcpkg-"):
            continue  # build helpers, not in the binary
        shutil.copy2(copyright_file, out / "licenses" / f"{port}-LICENSE.txt")
    ports = sorted(p.name for p in (prefix / "share").iterdir() if p.is_dir() and not p.name.startswith("vcpkg-"))
    if android:
        # The same static image libraries, for the Android build of Pillow.
        for part in ("include", "lib"):
            shutil.copytree(prefix / part, out / "deps" / part, ignore=shutil.ignore_patterns("cmake", "pkgconfig"))

    # 4. Check what it links to, and that it runs.
    if android:
        readelf = next((ndk / "toolchains" / "llvm" / "prebuilt").glob("*/bin/llvm-readelf"))
        listing = subprocess.run([readelf, "--dynamic", out / exe_name], capture_output=True, text=True, check=True).stdout
        deps = sorted(set(re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", listing)))
        extra = [d for d in deps if d not in ANDROID_ALLOWED]
        if extra:
            sys.exit(f"tesseract links to non-system libraries: {extra}")
        print("links to:", deps)
    elif windows:
        dumpbin = shutil.which("dumpbin")
        if dumpbin:
            listing = subprocess.run([dumpbin, "/dependents", out / exe_name], capture_output=True, text=True, check=True).stdout
            deps = {line.strip().lower() for line in listing.splitlines() if line.strip().lower().endswith(".dll")}
            extra = sorted(d for d in deps if d not in WIN_ALLOWED and not d.startswith("api-ms-win-"))
            if extra:
                sys.exit(f"tesseract.exe links to non-system DLLs: {extra}")
            print("links to:", sorted(deps))
    else:
        listing = subprocess.run(["otool", "-L", out / exe_name], capture_output=True, text=True, check=True).stdout
        deps = [line.strip().split(" (")[0] for line in listing.splitlines()[1:] if line.strip()]
        extra = [d for d in deps if not MAC_ALLOWED.match(d)]
        if extra:
            sys.exit(f"tesseract links to non-system libraries: {extra}")
        print("links to:", deps)
    can_run = not android and windows == (os.name == "nt") and (windows or target["arch"] == platform.machine() or platform.machine() == "arm64")
    version = ""
    if can_run:
        result = subprocess.run([out / exe_name, "--version"], capture_output=True, text=True, check=True)
        version = (result.stdout or result.stderr).strip()
        print(version)
        for banned in ("libcurl", "libarchive"):
            if banned in version:
                sys.exit(f"{banned} is linked in: {version}")
    (out / "BUILD_INFO.json").write_text(
        json.dumps(
            {
                "target": args.target,
                "tesseract": pin["version"],
                "tesseract_sha256": pin["sha256"],
                "vcpkg": PINS["vcpkg"],
                "vcpkg_ports": ports,
                "version_output": version,
                "executable_sha256": sha256(out / exe_name),
                **({"android_ndk": ndk_revision(ndk), "android_api": target["api"]} if android else {}),
            },
            indent=2,
        )
        + "\n",
        "utf-8",
    )
    print("built", out)


if __name__ == "__main__":
    main()
