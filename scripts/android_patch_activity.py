#!/usr/bin/env python3
"""After ``briefcase create android``: two overrides in Briefcase's MainActivity.

- **A document shared while HeOCR is open reaches Python.** The activity runs as ``singleTask``
  (pyproject.toml), so Android hands a new share or "Open with" to the running activity through
  ``onNewIntent``. Briefcase's MainActivity does not forward that, and ``getIntent()`` keeps the launch
  intent. The override keeps the newest intent; the app reads it when its window regains focus
  (``heocr_mobile.app.HeOCR.on_focus``).
- **System Back reaches Python** (design/android/SPEC.md, section 3.5). Toga has no Back hook on
  Android; ``onBackPressed`` asks ``heocr_mobile.back.pressed()`` first, and does Android's own Back
  (leave the app) only when the app did not handle it.

    python scripts/android_patch_activity.py

Safe to run twice: it changes nothing once the override is there.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTIVITY = ROOT / "build" / "heocr_mobile" / "android" / "gradle" / "app" / "src" / "main" / "java" / "org" / "beeware" / "android" / "MainActivity.java"
MARK = "// HeOCR: keep the newest intent"
BACK_MARK = "// HeOCR: System Back goes to Python first"
OVERRIDE = f"""
    {MARK} (a share or "Open with" while the app is open), for Python to read.
    @Override
    protected void onNewIntent(Intent intent) {{
        super.onNewIntent(intent);
        setIntent(intent);
    }}

    {BACK_MARK}: close the sheet, or go to the previous screen, before leaving the app.
    @Override
    public void onBackPressed() {{
        boolean handled = false;
        try {{
            handled = com.chaquo.python.Python.getInstance().getModule("heocr_mobile.back").callAttr("pressed").toBoolean();
        }} catch (Exception e) {{
            android.util.Log.w("HeOCR", "Back: " + e);
        }}
        if (!handled) {{
            super.onBackPressed();
        }}
    }}
"""


def main() -> None:
    source = ACTIVITY.read_text("utf-8")
    if MARK in source:
        print("already patched:", ACTIVITY.relative_to(ROOT))
        return
    for method in ("void onNewIntent(", "void onBackPressed("):
        if method in source:
            sys.exit(f"MainActivity already defines {method.split()[1]}; review the template before patching")
    if "import android.content.Intent;" not in source:
        source = source.replace("package org.beeware.android;", "package org.beeware.android;\n\nimport android.content.Intent;", 1)
    end = source.rstrip().rfind("}")
    ACTIVITY.write_text(source[:end] + OVERRIDE + source[end:], "utf-8")
    print("patched:", ACTIVITY.relative_to(ROOT))


if __name__ == "__main__":
    main()
