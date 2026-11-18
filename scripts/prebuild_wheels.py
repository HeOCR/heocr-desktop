#!/usr/bin/env python3
"""Build wheels for the few pure-Python dependencies that publish only an sdist.

Briefcase installs binary wheels only. pywebview needs proxy_tools (MIT), which has no wheel on
PyPI, so it is built here into build/wheels, which pyproject.toml lists with --find-links.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SDIST_ONLY = ["proxy_tools==0.1.0"]

if __name__ == "__main__":
    out = ROOT / "build" / "wheels"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(out), *SDIST_ONLY], check=True)
