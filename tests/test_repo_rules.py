"""The public repository holds no machine paths and no build state."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Built from parts, so this file does not match itself.
_MARKERS = ["/" + "Users/", "/home/" + "runner/", "C:\\" + "Users\\", "/" + "private/tmp/", "/" + "private/var/"]
MACHINE_PATH = re.compile(b"|".join(re.escape(m.encode()) for m in _MARKERS))


class RepoRulesTest(unittest.TestCase):
    def files(self):
        try:
            out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("not a git checkout")
        return [ROOT / f for f in out.decode().split("\0") if f]

    def test_no_build_state_tracked(self):
        for f in self.files():
            rel = f.relative_to(ROOT).as_posix()
            self.assertFalse(rel.startswith((".briefcase/", "build/", "dist/", "wheels/", "vendor", "logs/",
                                             "src/heocr_desktop/resources/")), rel)

    def test_no_machine_paths(self):
        for f in self.files():
            if f.suffix in (".png", ".icns", ".ico") or not f.is_file():
                continue
            self.assertIsNone(MACHINE_PATH.search(f.read_bytes()), f.relative_to(ROOT))


if __name__ == "__main__":
    unittest.main()
