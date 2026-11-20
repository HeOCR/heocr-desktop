"""Licence inventory displayed in the desktop app."""

from pathlib import Path

FONT_NOTICES = {
    "Noto Sans Hebrew": "fonts-OFL-NotoSansHebrew.txt",
    "JetBrains Mono": "fonts-OFL-JetBrainsMono.txt",
}


def about_text(resources: Path) -> str:
    paths = {"": resources / "THIRD_PARTY_LICENSES.md"}
    paths.update({name: resources / "licenses" / file for name, file in FONT_NOTICES.items()})
    parts = []
    for name, path in paths.items():
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        parts.append(f"{name}\n\n{text}" if name else text)
    return "\n\n".join(parts)
