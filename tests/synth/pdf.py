"""Synthetic PDF fixtures with an exact text layer, written byte by byte.

Glyphs come from a Type3 font (filled rectangles) with an explicit ToUnicode map, so no
font file is needed and every text-layer state can be made on purpose:

- logical or visual stream order;
- real or position-only spaces;
- invisible text (render mode 3);
- remapped characters, as in broken ToUnicode maps;
- images and vector paths;
- any page size.

The visual layout follows the Unicode Bidirectional Algorithm (reduced: no embeddings).
It is written for fixtures only and is independent of the reader's inverse pass.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

ADVANCE = {" ": 250}
DEFAULT_ADVANCE = 500  # glyph units of 1/1000 em


def _advance(ch: str) -> int:
    return 0 if unicodedata.combining(ch) else ADVANCE.get(ch, DEFAULT_ADVANCE)


def layout(text: str, rtl: bool = True) -> list[int]:
    """Display order, left to right, of a logical line, as logical indexes.

    A reduced Unicode Bidirectional Algorithm (no embeddings, no Arabic numbers):
    W4 (a single , . : / between digits), W5 (% ₪ next to digits), W7 (a number after
    Latin letters is Latin), N1/N2 (numbers count as R for neutrals; unequal
    neighbours take the line's direction), I1/I2 levels, and L2 reversal.
    """
    n = len(text)
    types = []
    for ch in text:
        bidi = unicodedata.bidirectional(ch)
        types.append("R" if bidi in ("R", "AL") else "L" if bidi == "L" else "EN" if bidi in ("EN", "AN") else "N")
    for i, ch in enumerate(text):  # W4
        if types[i] == "N" and 0 < i < n - 1 and ch in ",.:/" and types[i - 1] == "EN" and types[i + 1] == "EN":
            types[i] = "EN"
    for i, ch in enumerate(text):  # W5
        if types[i] == "N" and unicodedata.bidirectional(ch) == "ET":
            j = i
            while j < n and unicodedata.bidirectional(text[j]) == "ET":
                j += 1
            k = i
            while k > 0 and unicodedata.bidirectional(text[k - 1]) == "ET":
                k -= 1
            if (j < n and types[j] == "EN") or (k > 0 and types[k - 1] == "EN"):
                types[i] = "EN"
    base = "R" if rtl else "L"
    last_strong = base
    for i in range(n):  # W7
        if types[i] in ("R", "L"):
            last_strong = types[i]
        elif types[i] == "EN" and last_strong == "L":
            types[i] = "L"
    resolved = list(types)
    i = 0
    while i < n:  # N1, N2
        if types[i] != "N":
            i += 1
            continue
        j = i
        while j < n and types[j] == "N":
            j += 1
        left = types[i - 1] if i > 0 else base
        right = types[j] if j < n else base
        left, right = ("R" if left == "EN" else left), ("R" if right == "EN" else right)
        for k in range(i, j):
            resolved[k] = left if left == right else base
        i = j
    if rtl:
        levels = [1 if t == "R" else 2 for t in resolved]
    else:
        levels = [1 if t == "R" else 2 if t == "EN" else 0 for t in resolved]
    order = list(range(n))
    for level in range(max(levels, default=0), 0, -1):
        k = 0
        while k < n:
            if levels[k] >= level:
                m = k
                while m < n and levels[m] >= level:
                    m += 1
                order[k:m] = order[k:m][::-1]
                levels[k:m] = levels[k:m][::-1]
                k = m
            else:
                k += 1
    return order


def visual_order(text: str, rtl: bool = True) -> str:
    return "".join(text[i] for i in layout(text, rtl))


@dataclass
class TextLine:
    text: str  # logical order
    x: float  # right edge for RTL lines, left edge for LTR lines
    y: float  # baseline, PDF coordinates (origin bottom-left)
    size: float = 12.0
    rtl: bool = True
    vertical: bool = False  # turned 90 degrees clockwise (text space x runs down the page), glyphs in visual order


@dataclass
class PdfPage:
    lines: list[TextLine] = field(default_factory=list)
    width: float = 595.0
    height: float = 842.0
    stream_order: str = "logical"  # or "visual"
    real_spaces: bool = True
    invisible: bool = False
    remap: dict[str, str] = field(default_factory=dict)  # displayed char -> char in the ToUnicode map
    images: list[tuple[float, float, float, float]] = field(default_factory=list)  # x, y, w, h
    image_gray: int = 0x80  # grey level of every image (0xFF: a blank background)
    rasters: list[tuple] = field(default_factory=list)  # (x, y, w, h, PIL "L" image): real pixels, as a scan
    font_name: str = ""  # the Type3 font's /Name (and BaseFont), for per-font evidence
    rules: list[tuple[float, float, float, float]] = field(default_factory=list)  # ruling segments x0, y0, x1, y1
    rules_as: str = "stroke"  # "stroke": lines; "rects": thin filled rectangles, as Word draws borders; "double": two parallel lines
    rule_width: float = 0.5  # stroke width of "stroke" rulings
    rule_gap: float = 3.0  # distance between the two lines of a "double" ruling
    fills: list[tuple[float, float, float, float]] = field(default_factory=list)  # shading: filled, unstroked x, y, w, h
    paths: int = 0
    rotate: int = 0
    unit_font_size: bool = False  # "Tf 1" with the size in the text matrix, as many producers write
    glyphs: list[tuple[str, float, float]] = field(default_factory=list)  # extra glyphs (char, x, y), drawn as is
    origin: tuple[float, float] = (0.0, 0.0)  # the MediaBox's lower-left corner; all content is moved with it
    # Turn the page's content counter-clockwise by this many degrees in user space and set /Rotate to
    # it, so the page shows exactly as it would unturned: an upright page stored the way rotated
    # pages are. ``glyphs`` are drawn outside the turn (sideways on screen), for mixed pages.
    turn: int = 0
    crop: tuple[float, float, float, float] | None = None  # a CropBox, in the page's own coordinates (before origin)


def lines_block(texts: list[str], *, right: float = 545.0, top: float = 780.0, leading: float = 18.0, size: float = 12.0) -> list[TextLine]:
    return [TextLine(text, right, top - i * leading, size) for i, text in enumerate(texts)]


def make_pdf(pages: list[PdfPage]) -> bytes:
    objects: dict[int, bytes] = {}
    next_id = [3]

    def new(data: bytes) -> int:
        oid = next_id[0]
        next_id[0] += 1
        objects[oid] = data
        return oid

    def stream(data: bytes, extra: str = "") -> bytes:
        return f"<< /Length {len(data)} {extra}>>\nstream\n".encode() + data + b"\nendstream"

    page_ids = []
    for page in pages:
        chars = sorted(
            {ch for line in page.lines for ch in line.text if page.real_spaces or ch != " "} | {g[0] for g in page.glyphs}
        )
        codes = {ch: i + 1 for i, ch in enumerate(chars)}
        if len(codes) > 254:
            raise ValueError("one Type3 font holds at most 254 glyphs")
        content: list[str] = []
        for line in page.lines:
            order = layout(line.text, line.rtl)
            width = sum(_advance(line.text[i]) for i in order) * line.size / 1000
            x = line.x - width if line.rtl else line.x
            placed = []  # (logical index, char, x)
            base_x: dict[int, float] = {}
            for i in order:
                ch = line.text[i]
                if unicodedata.combining(ch):
                    continue
                if ch != " " or page.real_spaces:
                    placed.append((i, ch, x))
                base_x[i] = x + _advance(ch) * line.size / 2000
                x += _advance(ch) * line.size / 1000
            for i, ch in enumerate(line.text):
                if unicodedata.combining(ch):
                    # A mark has no advance and sits over the centre of its base letter.
                    base = max((b for b in base_x if b < i), default=None)
                    if base is not None:
                        placed.append((i, ch, base_x[base]))
            if page.stream_order != "logical":
                placed.sort(key=lambda item: (item[2], item[0]))
            if page.stream_order == "logical":
                placed.sort(key=lambda item: item[0])
            sequence = [(ch, px) for _, ch, px in placed]
            mode = 3 if page.invisible else 0
            for k, (ch, px) in enumerate(sequence):
                if line.vertical:
                    # Text space x runs down the page (matrix 0 -1 1 0): each glyph goes where its visual
                    # position along the upright line puts it, as a real producer draws rotated text.
                    y = line.y - (px - min(q for _, q in sequence))
                    content.append(f"BT {mode} Tr /F1 {line.size:g} Tf 0 -1 1 0 {line.x:.3f} {y:.3f} Tm <{codes[ch]:02X}> Tj ET")
                elif page.unit_font_size:
                    content.append(f"BT {mode} Tr /F1 1 Tf {line.size:g} 0 0 {line.size:g} {px:.3f} {line.y:.3f} Tm <{codes[ch]:02X}> Tj ET")
                else:
                    content.append(f"BT {mode} Tr /F1 {line.size:g} Tf 1 0 0 1 {px:.3f} {line.y:.3f} Tm <{codes[ch]:02X}> Tj ET")
        unturned = [f"BT /F1 12 Tf 1 0 0 1 {gx:.3f} {gy:.3f} Tm <{codes[ch]:02X}> Tj ET" for ch, gx, gy in page.glyphs]
        for x, y, w, h in page.fills:
            content.append(f"0.9 g {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f 0 g")
        for x0, y0, x1, y1 in page.rules:
            if page.rules_as == "double":
                dx, dy = (page.rule_gap / 2, 0) if x0 == x1 else (0, page.rule_gap / 2)
                for sign in (-1, 1):
                    content.append(f"0.5 w {x0 + sign * dx:.2f} {y0 + sign * dy:.2f} m {x1 + sign * dx:.2f} {y1 + sign * dy:.2f} l S")
            elif page.rules_as == "rects":
                w, h = max(abs(x1 - x0), 0.5), max(abs(y1 - y0), 0.5)
                content.append(f"{min(x0, x1):.2f} {min(y0, y1) - (0.25 if h == 0.5 else 0):.2f} {w:.2f} {h:.2f} re f")
            else:
                content.append(f"{page.rule_width:g} w {x0:.2f} {y0:.2f} m {x1:.2f} {y1:.2f} l S")
        for i in range(page.paths):
            content.append(f"{20 + (i % 50) * 5} {20 + (i // 50) * 5} 3 3 re f")
        resources = ""
        xobjects = []
        for n, (x, y, w, h) in enumerate(page.images):
            image = new(stream(bytes([page.image_gray]) * 4, "/Type /XObject /Subtype /Image /Width 2 /Height 2 /ColorSpace /DeviceGray /BitsPerComponent 8 "))
            xobjects.append(f"/Im{n} {image} 0 R")
            content.append(f"q {w:g} 0 0 {h:g} {x:g} {y:g} cm /Im{n} Do Q")
        for n, (x, y, w, h, picture) in enumerate(page.rasters):
            import zlib

            gray = picture.convert("L")
            data = zlib.compress(gray.tobytes())
            extra = f"/Type /XObject /Subtype /Image /Width {gray.size[0]} /Height {gray.size[1]} /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode "
            image = new(stream(data, extra))
            xobjects.append(f"/Ra{n} {image} 0 R")
            content.append(f"q {w:g} 0 0 {h:g} {x:g} {y:g} cm /Ra{n} Do Q")
        font = ""
        if codes:
            procs = []
            for ch, code in codes.items():
                adv = _advance(ch)
                if adv == 0:
                    glyph = "0 0 -60 750 60 850 d1 -60 750 120 100 re f"
                else:
                    glyph = f"{adv} 0 0 0 {adv} 700 d1" + ("" if ch == " " else f" 40 0 {adv - 80} 700 re f")
                procs.append(f"/g{code} {new(stream(glyph.encode()))} 0 R")
            cmap_lines = [
                "/CIDInit /ProcSet findresource begin 12 dict begin begincmap",
                "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def",
                "/CMapName /Synth-UCS def /CMapType 2 def",
                "1 begincodespacerange <00> <FF> endcodespacerange",
                f"{len(codes)} beginbfchar",
            ]
            for ch, code in codes.items():
                mapped = page.remap.get(ch, ch)
                cmap_lines.append(f"<{code:02X}> <{''.join(f'{u:04X}' for u in _utf16(mapped))}>")
            cmap_lines.append("endbfchar endcmap CMapName currentdict /CMap defineresource pop end end")
            tounicode = new(stream("\n".join(cmap_lines).encode()))
            widths = " ".join(str(_advance(ch)) for ch in codes)
            diffs = " ".join(f"/g{code}" for code in codes.values())
            font_id = new(
                (
                    "<< /Type /Font /Subtype /Type3 "
                    + (f"/Name /{page.font_name} /BaseFont /{page.font_name} " if page.font_name else "")
                    + "/FontBBox [0 0 1000 1000] /FontMatrix [0.001 0 0 0.001 0 0] "
                    f"/CharProcs << {' '.join(procs)} >> /Encoding << /Type /Encoding /Differences [1 {diffs}] >> "
                    f"/FirstChar 1 /LastChar {len(codes)} /Widths [{widths}] /ToUnicode {tounicode} 0 R /Resources << >> >>"
                ).encode()
            )
            font = f"/Font << /F1 {font_id} 0 R >>"
        if xobjects:
            resources = f"/XObject << {' '.join(xobjects)} >>"
        ox, oy = page.origin
        box_w, box_h = page.width, page.height
        if page.turn:
            # Counter-clockwise by ``turn`` about the origin, then moved back into the box.
            w, h = page.width, page.height
            matrix = {90: f"0 1 -1 0 {h:g} 0", 180: f"-1 0 0 -1 {w:g} {h:g}", 270: f"0 -1 1 0 0 {w:g}"}[page.turn]
            content = ["q", f"{matrix} cm"] + content + ["Q"]
            if page.turn in (90, 270):
                box_w, box_h = h, w
        content = content + unturned
        if ox or oy:
            content = [f"1 0 0 1 {ox:g} {oy:g} cm"] + content
        contents = new(stream("\n".join(content).encode()))
        rotation = page.turn or page.rotate
        rotate = f" /Rotate {rotation}" if rotation else ""
        crop = ""
        if page.crop is not None:
            cx0, cy0, cx1, cy1 = page.crop
            crop = f" /CropBox [{cx0 + ox:g} {cy0 + oy:g} {cx1 + ox:g} {cy1 + oy:g}]"
        page_ids.append(
            new(
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [{ox:g} {oy:g} {ox + box_w:g} {oy + box_h:g}]{crop}{rotate} "
                    f"/Resources << {font} {resources} >> /Contents {contents} 0 R >>"
                ).encode()
            )
        )
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[2] = f"<< /Type /Pages /Kids [{' '.join(f'{p} 0 R' for p in page_ids)}] /Count {len(page_ids)} >>".encode()
    out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for oid in sorted(objects):
        offsets[oid] = len(out)
        out += f"{oid} 0 obj\n".encode() + objects[oid] + b"\nendobj\n"
    xref = len(out)
    size = max(objects) + 1
    out += f"xref\n0 {size}\n0000000000 65535 f \n".encode()
    for oid in range(1, size):
        out += f"{offsets[oid]:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def _utf16(text: str) -> list[int]:
    data = text.encode("utf-16-be")
    return [int.from_bytes(data[i : i + 2], "big") for i in range(0, len(data), 2)]
