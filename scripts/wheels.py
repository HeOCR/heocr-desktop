"""Build the wheels Briefcase cannot download: heocr at its pinned commit, and proxy_tools (a pywebview
dependency published only as source). Briefcase installs binary wheels only; it finds these in wheels/.

    python scripts/wheels.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINNED = [
    "heocr @ git+https://github.com/HeOCR/heocr@57e58deb3a230a86b07e9fdf110223cac9fbf471",  # 0.1.0rc1
    "proxy_tools==0.1.0",
]


def main():
    out = ROOT / "wheels"
    shutil.rmtree(out, ignore_errors=True)
    subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(out), *PINNED], check=True)
    for w in sorted(out.glob("*.whl")):
        print(w.name)


if __name__ == "__main__":
    main()
