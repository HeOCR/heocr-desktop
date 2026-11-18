import re
from pathlib import Path

from heocr_desktop import i18n

UI = Path(__file__).resolve().parent.parent / "src" / "heocr_desktop" / "ui"


def test_csp_blocks_everything():
    html = (UI / "index.html").read_text("utf-8")
    assert "default-src 'none'" in html and "connect-src 'none'" in html


def test_ui_loads_nothing_from_the_network():
    for path in UI.iterdir():
        text = path.read_text("utf-8")
        assert not re.search(r"(src|href)\s*=\s*[\"']?(https?:)?//", text), path.name
        assert "fetch(" not in text and "XMLHttpRequest" not in text and "WebSocket" not in text, path.name


def test_every_ui_key_has_a_string():
    keys = set()
    for path in UI.iterdir():
        keys |= set(re.findall(r'data-i18n="([a-z_]+)"', path.read_text("utf-8")))
        keys |= set(re.findall(r'\bt\("([a-z_]+)"', path.read_text("utf-8")))
    src = (UI.parent / "render.py").read_text("utf-8")
    keys |= {k for k in re.findall(r'data-i18n="([a-z_]+)"', src)}
    keys |= {f"section_{role}" for role in ("footnote", "endnote", "comment", "header", "footer", "notes", "navigation")}
    keys = {k for k in keys if "{" not in k and not k.endswith("_")}  # t("note_" + n) is dynamic
    missing = sorted(k for k in keys if k not in i18n.STRINGS["en"])
    assert not missing, missing
