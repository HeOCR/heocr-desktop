"""System Back, from the activity to the app (scripts/android_patch_activity.py adds the Java side).

MainActivity's ``onBackPressed`` calls ``pressed()``. When the app handles Back (closing the sheet,
leaving a screen for Home) it returns True; False lets Android do its own Back, which leaves the app.
"""

from __future__ import annotations

handler = None  # set by heocr_mobile.app.HeOCR: a function that returns True when it handled Back


def pressed() -> bool:
    if handler is None:
        return False
    try:
        return bool(handler())
    except Exception as exc:  # noqa: BLE001 - Back must never crash the app
        print(f"HeOCR back: error {type(exc).__name__}", flush=True)
        return False
