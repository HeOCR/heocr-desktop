"""The Android app's test mode (``briefcase run android --test``): run the on-device tests.

Briefcase starts this module in place of the app and reads its exit marker from the device log.
"""

import sys
import tempfile
from pathlib import Path

import pytest

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    code = pytest.main(["-vv", "--no-header", "-p", "no:cacheprovider", "-o", f"cache_dir={tempfile.gettempdir()}", str(here)])
    print(f">>>>>>>>>> EXIT {code} <<<<<<<<<<")
    sys.exit(code)
