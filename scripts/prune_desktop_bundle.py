#!/usr/bin/env python3
"""Remove test fixtures and detached debug symbols before packaging the desktop app."""

import shutil
import sys
from pathlib import Path


def main(packages: Path) -> None:
    if packages.name != "app_packages" or not packages.is_dir():
        raise SystemExit(f"could not find Briefcase's app_packages at {packages}")
    fixtures = packages / "PyObjCTest"
    removed = 0
    if fixtures.is_dir():
        removed += size(fixtures)
        shutil.rmtree(fixtures)
    for bundle in sorted(packages.rglob("*.dSYM")):
        if bundle.is_dir():
            removed += size(bundle)
            shutil.rmtree(bundle)
    for pdb in packages.rglob("*.pdb"):
        if pdb.is_file():
            removed += pdb.stat().st_size
            pdb.unlink()
    print(f"Removed {removed:,} bytes of test fixtures and detached debug symbols")


def size(directory: Path) -> int:
    return sum(path.stat().st_size for path in directory.rglob("*") if path.is_file() and not path.is_symlink())


if __name__ == "__main__":
    main(Path(sys.argv[1]))
