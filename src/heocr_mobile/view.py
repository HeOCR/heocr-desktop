"""What a reading used, for the device log and the on-device test. The pages are in ``screens``."""

from __future__ import annotations

import re

_MODEL = re.compile(r"^tesseract:(.+)\.traineddata$")


def ocr_models(doc) -> set[str]:
    """The Tesseract models a reading used (``heb``, ``eng``, ``heocr_modern_v1``), from its record."""
    return {m.group(1) for key in getattr(doc, "components", {}) if (m := _MODEL.match(key))}
