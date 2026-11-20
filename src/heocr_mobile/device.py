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


def _strings(values):
    """A Java String[]: Chaquopy cannot choose an Intent.putExtra overload for a Python list."""
    from java import jarray

    return jarray(_jclass("java.lang.String"))(list(values))


def open_document_intent():
    """The system picker (Storage Access Framework), for PDF, DOCX and images."""
    Intent = _jclass("android.content.Intent")
    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("*/*")
    intent.putExtra(Intent.EXTRA_MIME_TYPES, _strings(MIME_TYPES))
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


def _column(uri, column: str):
    """One column of a content URI's metadata row (name, size), or None when the provider has none."""
    cursor = _android_context().getContentResolver().query(uri, _strings([column]), None, None, None)
    if cursor is None:
        return None
    try:
        if not cursor.moveToFirst() or cursor.isNull(0):
            return None
        return cursor.getString(0) if column == "_display_name" else cursor.getLong(0)
    finally:
        cursor.close()


def display_name(uri) -> str:
    """The document's name as its app shows it, for the status line; never used as a path."""
    name = _column(uri, str(_jclass("android.provider.OpenableColumns").DISPLAY_NAME))
    return str(name) if name else "document"


def declared_size(uri) -> int | None:
    """The size the providing app declares for a document, to check the copy against; None if unknown."""
    size = _column(uri, str(_jclass("android.provider.OpenableColumns").SIZE))
    return int(size) if size is not None else None


def copy_to(uri, folder: Path) -> tuple[Path, int]:
    """Copy a content URI into the app's own cache, so heocr reads a plain file; (path, bytes copied)."""
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
    return target, size


def create_document_intent(name: str, mime: str):
    """The system "save as" screen (Storage Access Framework), suggesting a file name."""
    Intent = _jclass("android.content.Intent")
    intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType(mime)
    # A typed Java String: Chaquopy cannot always choose an Intent.putExtra overload for a Python value.
    intent.putExtra(Intent.EXTRA_TITLE, _jclass("java.lang.String")(name))
    # Start in Downloads (SPEC 3.9). The picker treats it as a hint and falls back to its own choice.
    downloads = _jclass("android.provider.DocumentsContract").buildDocumentUri(
        "com.android.externalstorage.documents", "primary:Download")
    intent.putExtra(_jclass("android.provider.DocumentsContract").EXTRA_INITIAL_URI, downloads)
    return intent


def in_downloads(uri) -> bool:
    """True when a saved document's address is in the Downloads folder (for "Saved to Downloads")."""
    authority = str(uri.getAuthority() or "")
    if authority == "com.android.providers.downloads.documents":
        return True
    try:
        doc_id = str(_jclass("android.provider.DocumentsContract").getDocumentId(uri))
    except Exception:  # noqa: BLE001 - not a documents-provider address
        return False
    return authority == "com.android.externalstorage.documents" and doc_id.startswith("primary:Download/")


def write_to(uri, data: bytes) -> None:
    """Write a saved file's bytes to the place the user chose."""
    from java import jarray, jbyte

    stream = _android_context().getContentResolver().openOutputStream(uri, "wt")
    if stream is None:
        raise OSError("the file could not be written")
    try:
        stream.write(jarray(jbyte)(data))
    finally:
        stream.close()


# -- the screen: system bars, text size, the browser (design/android/SPEC.md, sections 3.4 to 3.8) -----

BAR_LIGHT, BAR_NIGHT = "#ffffff", "#141414"  # the page background (--bg) in each theme


def night(activity) -> bool:
    """True when the phone is in its dark theme (the app's DayNight theme follows it)."""
    Configuration = _jclass("android.content.res.Configuration")
    mode = activity.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK
    return mode == Configuration.UI_MODE_NIGHT_YES


def style_system_bars(activity) -> None:
    """Status and navigation bars in the page's background, with icons that read on it."""
    dark = night(activity)
    window = activity.getWindow()
    colour = _jclass("android.graphics.Color").parseColor(BAR_NIGHT if dark else BAR_LIGHT)
    window.setStatusBarColor(colour)
    window.setNavigationBarColor(colour)
    controller = _jclass("androidx.core.view.WindowCompat").getInsetsController(window, window.getDecorView())
    controller.setAppearanceLightStatusBars(not dark)
    controller.setAppearanceLightNavigationBars(not dark)


def configure_webview(webview, activity) -> int:
    """A phone page, not a zoomable web page: the viewport tag holds (``width=device-width``, scale 1),
    no pinch zoom (Toga turns it on) and no text boosting, and the text follows the phone's font size
    setting (the layout holds at 200%). Returns the text zoom in percent."""
    settings = webview.getSettings()
    settings.setUseWideViewPort(True)
    settings.setLoadWithOverviewMode(False)
    allow_zoom(webview, False)
    settings.setLayoutAlgorithm(_jclass("android.webkit.WebSettings$LayoutAlgorithm").NORMAL)
    # One CSS pixel per dp, pinned. Left to the WebView (setInitialScale(0)), the first page on some
    # starts drew about 1.5 times too large, whatever its viewport tag said.
    density = activity.getResources().getDisplayMetrics().density
    webview.setInitialScale(round(density * 100))
    scale = activity.getResources().getConfiguration().fontScale
    wanted = max(50, min(300, round(scale * 100)))
    default = settings.getTextZoom()
    # Always set it: left at its default, a recent System WebView also zooms the whole page by the font
    # scale (Android 14 emulator, 200%: icons and layout doubled, text larger still). Set explicitly, the
    # text alone scales. Android 15 at 200% still draws the text too large: issue #23.
    settings.setTextZoom(wanted)
    print(f"HeOCR text zoom: font_scale={scale:.2f} webview_default={default} now={settings.getTextZoom()}", flush=True)
    return int(settings.getTextZoom())


def allow_zoom(webview, allowed: bool) -> None:
    """Pinch zoom on the reading itself (a document to read closely), not on the app's screens.
    The phone's font size setting scales the text everywhere either way."""
    settings = webview.getSettings()
    settings.setSupportZoom(allowed)
    settings.setBuiltInZoomControls(allowed)
    settings.setDisplayZoomControls(False)


def open_in_browser(activity, url: str) -> bool:
    """Open a website link in the phone's browser, never inside the app; False when there is none."""
    Intent = _jclass("android.content.Intent")
    intent = Intent(Intent.ACTION_VIEW, _jclass("android.net.Uri").parse(url))
    try:
        activity.startActivity(intent)
    except Exception:  # noqa: BLE001 - no browser on the phone
        return False
    return True


def phone() -> dict:
    """The Android version and phone model, for "Copy technical details" (never anything personal)."""
    Build = _jclass("android.os.Build")
    return {"android": str(Build.VERSION.RELEASE), "sdk": int(Build.VERSION.SDK_INT), "model": str(Build.MODEL)}


# -- share and open (design/android/SPEC.md, section 9: heocr:share, heocr:open-saved) ----------

SHARE_TEXT_LIMIT = 100_000  # characters; longer text goes as a .txt file (an intent extra has a size limit)


def share_intent(text: str, name: str, cache: Path):
    """The system share sheet with the reading's text: as text, or as a .txt file when it is long."""
    Intent = _jclass("android.content.Intent")
    String = _jclass("java.lang.String")
    send = Intent(Intent.ACTION_SEND)
    send.setType("text/plain")
    if len(text) <= SHARE_TEXT_LIMIT:
        send.putExtra(Intent.EXTRA_TEXT, String(text))
    else:
        # The "shared" folder in the app's cache is the one Briefcase's FileProvider serves (as for photos).
        folder = cache / "shared"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}.txt"
        path.write_text(text, encoding="utf-8")
        context = _android_context()
        uri = _jclass("androidx.core.content.FileProvider").getUriForFile(
            context, f"{context.getPackageName()}.fileprovider", _jclass("java.io.File")(str(path)))
        send.putExtra(Intent.EXTRA_STREAM, uri)
        send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    return Intent.createChooser(send, None)


def view_intent(uri, mime: str):
    """Open a saved document in the phone's app for its type; None when no app can open it."""
    Intent = _jclass("android.content.Intent")
    view = Intent(Intent.ACTION_VIEW)
    view.setDataAndType(uri, mime)
    view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    # The manifest's <queries> lets the app see the viewers for its two types (Android 11 and later).
    if _android_context().getPackageManager().queryIntentActivities(view, 0).isEmpty():
        return None
    return view
