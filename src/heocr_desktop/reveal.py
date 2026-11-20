"""Reveal an app-saved file using the local file manager."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path


def local_file(path: Path) -> Path | None:
    """Use only regular files on a confirmed local volume."""
    if not path.is_absolute():
        return None
    try:
        if sys.platform == "darwin":
            from Foundation import NSURL, NSURLVolumeIsLocalKey

            path = path.resolve(strict=True)
            url = NSURL.fileURLWithPath_(str(path))
            ok, local, _ = url.getResourceValue_forKey_error_(None, NSURLVolumeIsLocalKey, None)
            if ok and local and path.is_file():
                return path
        elif sys.platform == "win32":
            import ctypes

            # Reject UNC/device paths and mapped shares before looking up any file metadata.
            if len(path.drive) != 2 or path.drive[1] != ":":
                return None
            if ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(path.anchor)) not in (2, 3, 6):
                return None
            # Inspect each component without traversing reparse points, which can redirect off disk.
            for part in (*reversed(path.parents), path):
                info = part.lstat()
                if info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    return None
            if stat.S_ISREG(info.st_mode):
                return path
    except (OSError, ImportError, RuntimeError, ValueError):
        return None
    return None


def show(path: Path) -> bool:
    target = local_file(path)
    if target is None:
        return False
    try:
        if sys.platform == "darwin":
            return subprocess.run(["/usr/bin/open", "-R", str(target)], check=False, timeout=5).returncode == 0
        if sys.platform == "win32":
            os.startfile(target.parent, "explore")
            return True
    except (OSError, subprocess.SubprocessError):
        pass
    return False
