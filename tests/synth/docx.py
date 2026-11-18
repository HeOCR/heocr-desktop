"""Synthetic DOCX fixtures, written as raw WordprocessingML.

Everything here is generated text. No real document is copied or embedded.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

NS = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
    'xmlns:v="urn:schemas-microsoft-com:vml"'
)


def lvl(
    ilvl: int,
    fmt: str = "decimal",
    text: str | None = None,
    start: int | None = 1,
    restart: int | None = None,
    lgl: bool = False,
    suff: str | None = None,
    pstyle: str | None = None,
) -> str:
    if text is None:
        text = "".join(f"%{i + 1}." for i in range(ilvl + 1))
    parts = [f'<w:lvl w:ilvl="{ilvl}">']
    if start is not None:
        parts.append(f'<w:start w:val="{start}"/>')
    parts.append(f'<w:numFmt w:val="{fmt}"/>')
    if restart is not None:
        parts.append(f'<w:lvlRestart w:val="{restart}"/>')
    if pstyle:
        parts.append(f'<w:pStyle w:val="{pstyle}"/>')
    if lgl:
        parts.append("<w:isLgl/>")
    if suff:
        parts.append(f'<w:suff w:val="{suff}"/>')
    parts.append(f'<w:lvlText w:val="{escape(text, {chr(34): "&quot;"})}"/><w:lvlJc w:val="right"/></w:lvl>')
    return "".join(parts)


def abstract_num(abstract_id: int, levels: list[str], style_link: str | None = None, num_style_link: str | None = None) -> str:
    links = ""
    if style_link:
        links += f'<w:styleLink w:val="{style_link}"/>'
    if num_style_link:
        links += f'<w:numStyleLink w:val="{num_style_link}"/>'
    return f'<w:abstractNum w:abstractNumId="{abstract_id}"><w:multiLevelType w:val="multilevel"/>{links}{"".join(levels)}</w:abstractNum>'


def num(num_id: int, abstract_id: int, starts: dict[int, int] | None = None, levels: dict[int, str] | None = None) -> str:
    overrides = ""
    for ilvl in sorted(set(starts or {}) | set(levels or {})):
        inner = ""
        if starts and ilvl in starts:
            inner += f'<w:startOverride w:val="{starts[ilvl]}"/>'
        if levels and ilvl in levels:
            inner += levels[ilvl]
        overrides += f'<w:lvlOverride w:ilvl="{ilvl}">{inner}</w:lvlOverride>'
    return f'<w:num w:numId="{num_id}"><w:abstractNumId w:val="{abstract_id}"/>{overrides}</w:num>'


def image_run(n: int) -> str:
    """A run holding the n-th embedded image (Docx.images), as Word writes an inline picture."""
    return (
        '<w:r><w:drawing><wp:inline><a:graphic><a:graphicData>'
        f'<a:blip r:embed="rIdImg{n}"/>'
        "</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"
    )


def numbering_xml(abstracts: list[str], nums: list[str]) -> bytes:
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering {NS}>{"".join(abstracts)}{"".join(nums)}</w:numbering>'.encode()


# -- documents -----------------------------------------------------------------


def run(text: str, *, hidden: bool = False, rstyle: str | None = None, deleted: bool = False) -> str:
    props = ""
    if rstyle:
        props += f'<w:rStyle w:val="{rstyle}"/>'
    if hidden:
        props += "<w:vanish/>"
    rpr = f"<w:rPr>{props}<w:rtl/></w:rPr>"
    pieces = []
    for i, line in enumerate(text.split("\n")):
        if i:
            pieces.append("<w:br/>")
        segments = line.split("\t")
        for j, seg in enumerate(segments):
            if j:
                pieces.append("<w:tab/>")
            if seg:
                tag = "w:delText" if deleted else "w:t"
                pieces.append(f'<{tag} xml:space="preserve">{escape(seg)}</{tag}>')
    body = f"<w:r>{rpr}{''.join(pieces)}</w:r>"
    if deleted:
        return f'<w:del w:id="9" w:author="synth">{body}</w:del>'
    return body


def para(
    *runs: str,
    style: str | None = None,
    num_id: int | None = None,
    ilvl: int | None = None,
    outline: int | None = None,
    bidi: bool = True,
) -> str:
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if num_id is not None:
        ppr += "<w:numPr>"
        if ilvl is not None:
            ppr += f'<w:ilvl w:val="{ilvl}"/>'
        ppr += f'<w:numId w:val="{num_id}"/></w:numPr>'
    if outline is not None:
        ppr += f'<w:outlineLvl w:val="{outline}"/>'
    if bidi:
        ppr += "<w:bidi/>"
    content = "".join(r if r.startswith("<") else run(r) for r in runs)
    return f"<w:p><w:pPr>{ppr}</w:pPr>{content}</w:p>"


def table(rows: list[list[str | tuple[str, dict]]], *, bidi: bool = True, borders: bool = False) -> str:
    """Rows of cells. A cell is text (``\\n`` starts a new paragraph) or (text, {"span": n, "vmerge": "restart"|"continue"})."""
    lines = "".join(f'<w:{side} w:val="single" w:sz="8" w:space="0" w:color="000000"/>' for side in ("top", "left", "bottom", "right", "insideH", "insideV"))
    tblpr = "<w:tblPr>" + ("<w:bidiVisual/>" if bidi else "") + (f"<w:tblBorders>{lines}</w:tblBorders>" if borders else "") + "</w:tblPr>"
    columns = max((sum((min(c[1].get("span", 1), 64) if not isinstance(c, str) else 1) for c in row) for row in rows), default=1)  # a hostile span stays a short grid
    grid = "<w:tblGrid>" + '<w:gridCol w:w="2000"/>' * columns + "</w:tblGrid>"
    out = [f"<w:tbl>{tblpr}{grid}"]
    for row in rows:
        out.append("<w:tr>")
        for cell in row:
            text, opts = (cell, {}) if isinstance(cell, str) else cell
            tcpr = ""
            if opts.get("span"):
                tcpr += f'<w:gridSpan w:val="{opts["span"]}"/>'
            if opts.get("vmerge") == "restart":
                tcpr += '<w:vMerge w:val="restart"/>'
            elif opts.get("vmerge") == "continue":
                tcpr += "<w:vMerge/>"
            paragraphs = "".join(para(p) for p in text.split("\n\n")) if text else para()
            out.append(f"<w:tc><w:tcPr>{tcpr}</w:tcPr>{paragraphs}</w:tc>")
        out.append("</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def style(
    style_id: str,
    name: str,
    *,
    kind: str = "paragraph",
    based_on: str | None = None,
    outline: int | None = None,
    num_id: int | None = None,
    ilvl: int | None = None,
    hidden: bool = False,
) -> str:
    ppr = ""
    if num_id is not None or ilvl is not None:
        ppr += "<w:numPr>" + (f'<w:ilvl w:val="{ilvl}"/>' if ilvl is not None else "")
        ppr += (f'<w:numId w:val="{num_id}"/>' if num_id is not None else "") + "</w:numPr>"
    if outline is not None:
        ppr += f'<w:outlineLvl w:val="{outline}"/>'
    based = f'<w:basedOn w:val="{based_on}"/>' if based_on else ""
    rpr = "<w:rPr><w:vanish/></w:rPr>" if hidden else ""
    return f'<w:style w:type="{kind}" w:styleId="{style_id}"><w:name w:val="{name}"/>{based}<w:pPr>{ppr}</w:pPr>{rpr}</w:style>'


@dataclass
class Docx:
    body: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    abstracts: list[str] = field(default_factory=list)
    nums: list[str] = field(default_factory=list)
    footnotes: dict[int, str] = field(default_factory=dict)
    endnotes: dict[int, str] = field(default_factory=dict)
    comments: dict[int, str] = field(default_factory=dict)
    headers: list[str] = field(default_factory=list)
    footers: list[str] = field(default_factory=list)
    extra_parts: dict[str, bytes] = field(default_factory=dict)
    images: list[bytes] = field(default_factory=list)  # embedded as word/media/image<n>, relationship rIdImg<n>

    def build(self) -> bytes:
        rels = []
        content_types = [
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
            '<Default Extension="xml" ContentType="application/xml"/>',
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        ]
        parts: dict[str, bytes] = {}
        sect = ""

        def add(name: str, rel_type: str, xml: str) -> str:
            rid = f"rId{len(rels) + 1}"
            rels.append(
                f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/{rel_type}" Target="{name}"/>'
            )
            parts[f"word/{name}"] = xml.encode()
            return rid

        for n, data in enumerate(self.images, 1):
            parts[f"word/media/image{n}.png"] = data
            rels.append(
                f'<Relationship Id="rIdImg{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image{n}.png"/>'
            )
        if self.styles:
            add("styles.xml", "styles", f'<?xml version="1.0" encoding="UTF-8"?><w:styles {NS}>{"".join(self.styles)}</w:styles>')
        if self.abstracts or self.nums:
            parts["word/numbering.xml"] = numbering_xml(self.abstracts, self.nums)
            rels.append(
                f'<Relationship Id="rId{len(rels) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
            )
        for tag, notes, name in (("footnote", self.footnotes, "footnotes.xml"), ("endnote", self.endnotes, "endnotes.xml")):
            if notes:
                items = "".join(
                    f'<w:{tag} w:id="{nid}">{para(text)}</w:{tag}>' for nid, text in notes.items()
                )
                sep = f'<w:{tag} w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:{tag}>'
                add(name, tag + "s", f'<?xml version="1.0" encoding="UTF-8"?><w:{tag}s {NS}>{sep}{items}</w:{tag}s>')
        if self.comments:
            items = "".join(
                f'<w:comment w:id="{cid}" w:author="synth">{para(text)}</w:comment>' for cid, text in self.comments.items()
            )
            add("comments.xml", "comments", f'<?xml version="1.0" encoding="UTF-8"?><w:comments {NS}>{items}</w:comments>')
        for kind, texts in (("header", self.headers), ("footer", self.footers)):
            for i, text in enumerate(texts, 1):
                tag = "hdr" if kind == "header" else "ftr"
                rid = add(f"{kind}{i}.xml", kind, f'<?xml version="1.0" encoding="UTF-8"?><w:{tag} {NS}>{para(text)}</w:{tag}>')
                sect += f'<w:{kind}Reference w:type="default" r:id="{rid}"/>'
        document = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>'
            + "".join(self.body)
            # Word always ends the body with a paragraph; a final table without one is invalid,
            # and LibreOffice's text export loops on it.
            + (para() if self.body and self.body[-1].startswith("<w:tbl>") else "")
            + f"<w:sectPr>{sect}</w:sectPr></w:body></w:document>"
        )
        parts["word/document.xml"] = document.encode()
        parts["word/_rels/document.xml.rels"] = (
            '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(rels)
            + "</Relationships>"
        ).encode()
        parts["_rels/.rels"] = (
            b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            b"</Relationships>"
        )
        parts["[Content_Types].xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            + "".join(content_types)
            + "</Types>"
        ).encode()
        parts.update(self.extra_parts)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in ["[Content_Types].xml", *sorted(n for n in parts if n != "[Content_Types].xml")]:
                archive.writestr(name, parts[name])
        return buffer.getvalue()
