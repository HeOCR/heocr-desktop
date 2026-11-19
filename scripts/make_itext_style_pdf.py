#!/usr/bin/env python3
"""Write an invented two-page Hebrew "invoice" PDF built the way many generated bills are.

    python scripts/make_itext_style_pdf.py --font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf out.pdf

It reproduces the structure of a real bill that read badly on a phone, with invented text only:
- A4 pages; Type0 fonts with Identity-H encoding and a ToUnicode map;
- page 1: an embedded TrueType CID font (``--font``, with Hebrew) and a 624 x 654 JPEG logo;
- page 2: a CID font named Arial that is **not embedded**, so a renderer must substitute one;
- Hebrew runs drawn right to left glyph by glyph, numbers left to right;
- an incremental update at the end (a new Info dictionary and a second xref with /Prev), as tools
  that "modify" a PDF append.
The real bill's embedded fonts are CFF (CIDFontType0C); this one is TrueType (CIDFontType2), which
fontTools can embed as is. Needs fontTools and Pillow.
"""

from __future__ import annotations

import argparse
import io
import re
import zlib
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

PAGE = (595.28, 841.89)
PAGE1 = [
    ("חשבון תקופתי לדוגמה", 18),
    ("לכבוד: משפחת הגננים", 12),
    ("רחוב הדקלים 12, עיר לדוגמה", 12),
    ("מספר לקוח: 40712  ·  תקופה: 01/10/2026 עד 31/10/2026", 11),
    ("פירוט החיובים", 14),
    ("צריכה בתקופה: 312 יחידות", 11),
    ("מחיר ליחידה: 0.64 ₪", 11),
    ("סך הכול לתשלום: 199.68 ₪", 13),
]
PAGE2 = [
    ("הסברים לחשבון", 14),
    ("החשבון מחושב לפי הצריכה שנמדדה בתקופה.", 11),
    ("אפשר לשלם עד 15/11/2026 בכל אחד מאמצעי התשלום.", 11),
    ("לשאלות: מוקד שירות לדוגמה, 03-0000000.", 11),
    ("תודה שבחרתם בשירות לדוגמה.", 11),
]
LTR = re.compile(r"[0-9.,/₪\-]+(?: [0-9.,/₪\-]+)*")


class Font:
    def __init__(self, path: Path):
        self.path = path
        self.tt = TTFont(path)
        self.cmap = self.tt.getBestCmap()
        self.upem = self.tt["head"].unitsPerEm
        self.hmtx = self.tt["hmtx"]
        self.order = self.tt.getGlyphOrder()
        self.used: dict[int, str] = {}

    def gid(self, ch: str) -> int:
        name = self.cmap.get(ord(ch))
        if name is None:
            raise SystemExit(f"{self.path.name} has no glyph for {ch!r}")
        g = self.order.index(name)
        self.used[g] = ch
        return g

    def advance(self, g: int, size: float) -> float:
        return self.hmtx[self.order[g]][0] * size / self.upem


def runs(line: str):
    """(text, ltr) runs in logical order: numbers and their punctuation left to right, the rest RTL."""
    pos = 0
    for m in LTR.finditer(line):
        if m.start() > pos:
            yield line[pos:m.start()], False
        yield m.group(0), True
        pos = m.end()
    if pos < len(line):
        yield line[pos:], False


def draw(lines, font: Font, name: str, top: float) -> bytes:
    """A content stream: each glyph placed by its own matrix, Hebrew from the right margin leftwards."""
    out = ["BT"]
    y = top
    for text, size in lines:
        x = PAGE[0] - 48
        out.append(f"/{name} {size} Tf")
        for run, ltr in runs(text):
            glyphs = [font.gid(ch) for ch in run]
            width = sum(font.advance(g, size) for g in glyphs)
            if ltr:
                gx = x - width
                for g in glyphs:
                    out.append(f"1 0 0 1 {gx:.2f} {y:.2f} Tm <{g:04X}> Tj")
                    gx += font.advance(g, size)
            else:
                gx = x
                for g in glyphs:
                    gx -= font.advance(g, size)
                    out.append(f"1 0 0 1 {gx:.2f} {y:.2f} Tm <{g:04X}> Tj")
            x -= width
        y -= size * 2.0
    out.append("ET")
    return "\n".join(out).encode("ascii")


def to_unicode(used: dict[int, str]) -> bytes:
    items = sorted(used.items())
    body = [
        "/CIDInit /ProcSet findresource begin", "12 dict begin", "begincmap",
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def",
        "/CMapName /Adobe-Identity-UCS def", "/CMapType 2 def",
        "1 begincodespacerange", "<0000> <FFFF>", "endcodespacerange",
    ]
    for i in range(0, len(items), 100):
        chunk = items[i:i + 100]
        body.append(f"{len(chunk)} beginbfchar")
        body += [f"<{g:04X}> <{ord(ch):04X}>" for g, ch in chunk]
        body.append("endbfchar")
    body += ["endcmap", "CMapName currentdict /CMap defineresource pop", "end", "end"]
    return "\n".join(body).encode("ascii")


def widths(font: Font) -> str:
    return "[" + " ".join(f"{g} [{round(font.advance(g, 1000))}]" for g in sorted(font.used)) + "]"


def logo() -> bytes:
    im = Image.new("RGB", (624, 654), (250, 250, 250))
    d = ImageDraw.Draw(im)
    d.ellipse((60, 60, 564, 594), fill=(30, 96, 192))
    d.rectangle((210, 230, 414, 424), fill=(255, 255, 255))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return buf.getvalue()


class Writer:
    def __init__(self):
        self.buf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        self.offsets: dict[int, int] = {}

    def obj(self, num: int, body: bytes | str, stream: bytes | None = None):
        self.offsets[num] = len(self.buf)
        body = body.encode("latin-1") if isinstance(body, str) else body
        self.buf += f"{num} 0 obj\n".encode() + body
        if stream is not None:
            self.buf += b"\nstream\n" + stream + b"\nendstream"
        self.buf += b"\nendobj\n"

    def xref(self, nums, size: int, root: int, info: int, prev: int | None = None) -> int:
        start = len(self.buf)
        self.buf += b"xref\n"
        if prev is None:
            self.buf += f"0 {size}\n".encode() + b"0000000000 65535 f \n"
            for n in range(1, size):
                self.buf += f"{self.offsets[n]:010d} 00000 n \n".encode()
        else:
            for n in nums:
                self.buf += f"{n} 1\n{self.offsets[n]:010d} 00000 n \n".encode()
        trailer = f"<< /Size {size} /Root {root} 0 R /Info {info} 0 R" + (f" /Prev {prev}" if prev is not None else "") + " >>"
        self.buf += f"trailer\n{trailer}\nstartxref\n{start}\n%%EOF\n".encode()
        return start


def build(font_path: Path) -> bytes:
    embedded = Font(font_path)
    arial = Font(font_path)  # glyph ids for the non-embedded "Arial", as a generator would emit them
    c1 = b"q 100 0 0 105 48 690 cm /Im1 Do Q\n" + draw(PAGE1, embedded, "F1", 640)
    c2 = draw(PAGE2, arial, "F2", 760)
    ttf = font_path.read_bytes()
    w = Writer()
    w.obj(1, "<< /Type /Catalog /Pages 2 0 R >>")
    w.obj(2, "<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>")
    w.obj(3, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE[0]} {PAGE[1]}] /Contents 5 0 R "
             "/Resources << /Font << /F1 7 0 R >> /XObject << /Im1 16 0 R >> >> >>")
    w.obj(4, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE[0]} {PAGE[1]}] /Contents 6 0 R "
             "/Resources << /Font << /F2 12 0 R >> >> >>")
    for num, data in ((5, c1), (6, c2)):
        packed = zlib.compress(data)
        w.obj(num, f"<< /Length {len(packed)} /Filter /FlateDecode >>", packed)
    w.obj(7, "<< /Type /Font /Subtype /Type0 /BaseFont /HEOCRX+DejaVuSans /Encoding /Identity-H "
             "/DescendantFonts [8 0 R] /ToUnicode 9 0 R >>")
    w.obj(8, "<< /Type /Font /Subtype /CIDFontType2 /BaseFont /HEOCRX+DejaVuSans "
             "/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
             f"/FontDescriptor 10 0 R /CIDToGIDMap /Identity /DW 1000 /W {widths(embedded)} >>")
    cmap1 = zlib.compress(to_unicode(embedded.used))
    w.obj(9, f"<< /Length {len(cmap1)} /Filter /FlateDecode >>", cmap1)
    w.obj(10, "<< /Type /FontDescriptor /FontName /HEOCRX+DejaVuSans /Flags 32 /FontBBox [-1021 -463 1793 1232] "
              "/ItalicAngle 0 /Ascent 928 /Descent -236 /CapHeight 729 /StemV 80 /FontFile2 11 0 R >>")
    packed_ttf = zlib.compress(ttf)
    w.obj(11, f"<< /Length {len(packed_ttf)} /Length1 {len(ttf)} /Filter /FlateDecode >>", packed_ttf)
    w.obj(12, "<< /Type /Font /Subtype /Type0 /BaseFont /Arial /Encoding /Identity-H "
              "/DescendantFonts [13 0 R] /ToUnicode 14 0 R >>")
    w.obj(13, "<< /Type /Font /Subtype /CIDFontType2 /BaseFont /Arial "
              "/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> "
              f"/FontDescriptor 15 0 R /CIDToGIDMap /Identity /DW 1000 /W {widths(arial)} >>")
    cmap2 = zlib.compress(to_unicode(arial.used))
    w.obj(14, f"<< /Length {len(cmap2)} /Filter /FlateDecode >>", cmap2)
    w.obj(15, "<< /Type /FontDescriptor /FontName /Arial /Flags 32 /FontBBox [-665 -325 2000 1006] "
              "/ItalicAngle 0 /Ascent 905 /Descent -212 /CapHeight 716 /StemV 80 >>")
    jpeg = logo()
    w.obj(16, f"<< /Type /XObject /Subtype /Image /Width 624 /Height 654 /ColorSpace /DeviceRGB "
              f"/BitsPerComponent 8 /Filter /DCTDecode /Length {len(jpeg)} >>", jpeg)
    w.obj(17, "<< /Producer (HeOCR test fixture, generated) /Title (Invented bill) >>")
    first = w.xref(None, 18, root=1, info=17)
    # The incremental update a "modifying" tool appends: a new Info dictionary, a second xref.
    w.obj(17, "<< /Producer (HeOCR test fixture, generated; modified by an iText-style update) /Title (Invented bill) >>")
    w.xref([17], 18, root=1, info=17, prev=first)
    return bytes(w.buf)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True, type=Path, help="a TrueType font with Hebrew glyphs, embedded on page 1")
    ap.add_argument("out", type=Path)
    a = ap.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(build(a.font))
    print("wrote", a.out, a.out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
