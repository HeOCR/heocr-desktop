"""Native menu labels and actions for the macOS and Windows shells."""

from __future__ import annotations

from functools import partial


def build(language, dispatch, quit_app, platform):
    from webview.menu import Menu, MenuAction

    def label(en, he):
        return he if language == "he" else en

    def item(en, he, action):
        return MenuAction(label(en, he), partial(dispatch, action))

    file_items = [
        item("Open…", "פתיחה…", "open"),
        item("Save", "שמירה", "save"),
        item("Save As…", "שמירה בשם…", "saveAs"),
        item("Close File", "סגירת הקובץ", "close"),
    ]
    about = item("About HeOCR", "אודות HeOCR", "about")
    menus = []
    if platform == "darwin":
        menus.append(Menu("__app__", [about]))
    elif platform == "win32":
        file_items.append(MenuAction(label("Exit", "יציאה"), quit_app))
    else:
        return []
    menus.extend([
        Menu(label("File", "קובץ"), file_items),
        Menu(label("Edit", "עריכה"), [
            item("Copy", "העתקה", "copy"),
            item("Copy All Text", "העתקת כל הטקסט", "copyAll"),
            item("Select All", "בחירת הכול", "selectAll"),
        ]),
        Menu(label("View", "תצוגה"), [
            item("Formatted", "מעוצב", "formatted"),
            item("Text", "טקסט", "text"),
            item("Markdown", "Markdown", "markdown"),
            item("Larger Text", "הגדלת הטקסט", "larger"),
            item("Smaller Text", "הקטנת הטקסט", "smaller"),
            item("Actual Size", "גודל רגיל", "actual"),
            item("עברית", "English", "language"),
        ]),
        Menu(label("Help", "עזרה"), [about]),
    ])
    return menus
