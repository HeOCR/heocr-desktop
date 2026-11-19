"""Where the Android app keeps Tesseract and its models, and the phone's own services.

- **Tesseract** ships as ``libtesseract_exec.so`` in the APK's native-library folder: since
  Android 10 an app may run executables only from there (docs/mobile-design.md, section 3).
- **Models** (``heb``, ``eng`` and Tesseract's ``configs``) ship in this package's
  ``resources/tessdata``, which the Gradle build extracts to real files.
- **No network:** the app's manifest has no INTERNET permission, so Android refuses every
  socket. The desktop's in-process guard stays on as a second layer.
"""

from __future__ import annotations

from pathlib import Path

from heocr_desktop import engine

RESOURCES = Path(__file__).resolve().parent / "resources"
EXECUTABLE = "libtesseract_exec.so"


def _android_context():
    from com.chaquo.python import Python  # Chaquopy's Java bridge, present only on Android

    return Python.getPlatform().getApplication()


def native_library_dir() -> Path:
    return Path(str(_android_context().getApplicationInfo().nativeLibraryDir))


def prepare() -> None:
    """Point the shared engine at the bundled Tesseract and models, and block the network."""
    engine.install_offline_guard()
    engine.configure(tesseract=native_library_dir() / EXECUTABLE, tessdata=RESOURCES / "tessdata")


def language() -> str:
    """``he`` when the phone's language is Hebrew (Java still reports it as ``iw``), else ``en``."""
    try:
        from java import jclass

        code = str(jclass("java.util.Locale").getDefault().getLanguage()).lower()
    except Exception:  # noqa: BLE001 - off Android, or no locale: English
        return "en"
    return "he" if code in ("he", "iw") else "en"


def copy_text(text: str) -> None:
    from java import jclass

    context = _android_context()
    clipboard = context.getSystemService(jclass("android.content.Context").CLIPBOARD_SERVICE)
    clipboard.setPrimaryClip(jclass("android.content.ClipData").newPlainText("HeOCR", text))
