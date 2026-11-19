"""Where the Android app keeps Tesseract and its models, and the phone's own services.

- **Tesseract** ships as ``libtesseract_exec.so`` in the APK's native-library folder: since
  Android 10 an app may run executables only from there (docs/mobile-design.md, section 3).
- **Models:** HeOCR's own (``heocr_modern_v1``, heocr's default) ship inside the heocr package;
  stock ``heb``, ``eng`` (heocr's second reading of numbers) and Tesseract's ``configs`` ship in this
  package's ``resources/tessdata``. The Gradle build extracts both to real files.
- **No network:** the app's manifest has no INTERNET permission, so Android refuses every
  socket. The desktop's in-process guard stays on as a second layer.
"""

from __future__ import annotations

import os
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
    """Point the shared engine at the bundled Tesseract and models, and block the network.

    ``HEOCR_MODELS`` names a folder that holds no models, so heocr always uses the models in its own
    package (``heocr_modern_v1``, its default) and never one downloaded elsewhere: every phone reads
    the same way.
    """
    engine.install_offline_guard()
    engine.configure(tesseract=native_library_dir() / EXECUTABLE, tessdata=RESOURCES / "tessdata")
    os.environ["HEOCR_MODELS"] = str(RESOURCES / "no-downloaded-models")


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


# -- documents from other apps: the system picker and the share sheet ---------------------

# What the picker offers and the share sheet accepts. heocr decides the format from the content.
MIME_TYPES = (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/*",
)
MAX_BYTES = 200 * 1024 * 1024  # heocr's own limit is checked again when it reads


def _jclass(name: str):
    from java import jclass

    return jclass(name)


def open_document_intent():
    """The system picker (Storage Access Framework), for PDF, DOCX and images."""
    Intent = _jclass("android.content.Intent")
    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("*/*")
    intent.putExtra(Intent.EXTRA_MIME_TYPES, list(MIME_TYPES))
    return intent


def incoming_uri(intent):
    """The document a SEND (share sheet) or VIEW (open with) intent carries, or None."""
    if intent is None:
        return None
    Intent = _jclass("android.content.Intent")
    action = intent.getAction()
    if action == Intent.ACTION_SEND:
        return intent.getParcelableExtra(Intent.EXTRA_STREAM)
    if action == Intent.ACTION_VIEW:
        return intent.getData()
    return None


def display_name(uri) -> str:
    """The document's name as its app shows it, for the status line; never used as a path."""
    OpenableColumns = _jclass("android.provider.OpenableColumns")
    cursor = _android_context().getContentResolver().query(uri, [OpenableColumns.DISPLAY_NAME], None, None, None)
    try:
        if cursor is not None and cursor.moveToFirst():
            return str(cursor.getString(0))
    finally:
        if cursor is not None:
            cursor.close()
    return "document"


def copy_to(uri, folder: Path) -> Path:
    """Copy a content URI into the app's own cache, so heocr reads a plain file."""
    from java import jarray, jbyte

    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "incoming"
    stream = _android_context().getContentResolver().openInputStream(uri)
    if stream is None:
        raise OSError("the document could not be opened")
    buffer = jarray(jbyte)(1 << 16)
    size = 0
    try:
        with target.open("wb") as out:
            while True:
                n = stream.read(buffer)
                if n < 0:
                    break
                size += n
                if size > MAX_BYTES:
                    raise OSError("the document is too large")
                out.write(bytes(buffer)[:n])
    finally:
        stream.close()
    return target
