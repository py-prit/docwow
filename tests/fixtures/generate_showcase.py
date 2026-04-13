"""
Generate showcase.docx — a single DOCX produced by our writer that exercises
every feature implemented so far.

Run from the project root::

    python tests/fixtures/generate_showcase.py

Open showcase.docx in Word / LibreOffice to verify visual output.
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

# Make sure we can import docwow from the project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docwow.models.document import Document
from docwow.models.header_footer import HeaderFooter
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import Hyperlink, ImageRun, PageBreak, PageNumberField, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.models.table import Table, TableCell, TableRow
from docwow.writer.docx_writer import write_docx

# ---------------------------------------------------------------------------
# Colored PNG for image demo (visible on white background)
# ---------------------------------------------------------------------------
# 16x16 red/green/blue/yellow 4-quadrant PNG generated with:
#   python -c "
#     import struct, zlib
#     def png(w,h,rows):
#         def chunk(t,d): s=struct.pack('>I',len(d))+t+d; return s+struct.pack('>I',zlib.crc32(s[4:])&0xffffffff)
#         raw=b''.join(b'\x00'+r for r in rows)
#         return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
#     row_r=bytes([255,0,0]*8+[255,255,0]*8)
#     row_g=bytes([0,128,0]*8+[0,0,255]*8)
#     import base64; print(base64.b64encode(png(16,16,[row_r]*8+[row_g]*8)).decode())
#   "
_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAKklEQVQoz2P8z8Cwno"
    "GBgYmBCkCsgYmBiYEKQKyBiYGJgQpArIGJgQkAr+QCi5aGjNUAAAAASUVORK5CYII="
)
PNG_DATA = base64.b64decode(_PNG_B64)
# Fallback: generate a simple colored PNG programmatically if the above doesn't decode well
import struct as _struct, zlib as _zlib

def _make_color_png() -> bytes:
    """Generate a 16x16 4-quadrant colored PNG (red/yellow/green/blue)."""
    def _chunk(tag: bytes, data: bytes) -> bytes:
        s = _struct.pack(">I", len(data)) + tag + data
        return s + _struct.pack(">I", _zlib.crc32(s[4:]) & 0xFFFFFFFF)

    w, h = 16, 16
    row_top = bytes([255, 0, 0] * 8 + [255, 255, 0] * 8)    # red | yellow
    row_bot = bytes([0, 160, 0] * 8 + [0, 80, 200] * 8)     # green | blue
    raw = b"".join(b"\x00" + (row_top if y < h // 2 else row_bot) for y in range(h))
    ihdr = _struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", _zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )

PNG_DATA = _make_color_png()


def _p(text: str, **fmt_kw) -> Paragraph:
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(**fmt_kw),
    )


def _rp(*runs, **fmt_kw) -> Paragraph:
    return Paragraph(runs=tuple(runs), formatting=ParagraphFormatting(**fmt_kw))


def _run(text: str, **kw) -> TextRun:
    return TextRun(text=text, formatting=RunFormatting(**kw))


def _list_para(text: str, num_id: str, level: int = 0) -> Paragraph:
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(),
        list_info=ListInfo(num_id=num_id, level=level),
    )


def build_showcase() -> Document:
    body = []

    # -----------------------------------------------------------------------
    # Section 1: Plain paragraphs
    # -----------------------------------------------------------------------
    body.append(_p("docwow Showcase Document", style_id="Heading1"))
    body.append(_p("This document is generated entirely by the docwow writer layer. "
                   "It exercises every feature implemented in the library."))

    # -----------------------------------------------------------------------
    # Section 2: Paragraph alignment
    # -----------------------------------------------------------------------
    body.append(_p("Paragraph Formatting", style_id="Heading2"))
    body.append(_p("Left-aligned paragraph (default)", alignment="left"))
    body.append(_p("Centre-aligned paragraph", alignment="center"))
    body.append(_p("Right-aligned paragraph", alignment="right"))
    body.append(_p(
        "Justified paragraph. Lorem ipsum dolor sit amet, consectetur "
        "adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore.",
        alignment="justify",
    ))

    # -----------------------------------------------------------------------
    # Section 3: Indentation
    # -----------------------------------------------------------------------
    body.append(_p("Indentation", style_id="Heading2"))
    body.append(_p("Normal paragraph — no indent"))
    body.append(_p("Left indent 36pt", indent_left_pt=36.0))
    body.append(_p("Left indent 72pt", indent_left_pt=72.0))
    body.append(_p("Right indent 36pt", indent_right_pt=36.0))
    body.append(_p("First-line indent 36pt", indent_first_line_pt=36.0))
    body.append(_p("Hanging indent 36pt (first line protrudes left)",
                   indent_left_pt=72.0, indent_first_line_pt=-36.0))

    # -----------------------------------------------------------------------
    # Section 4: Spacing
    # -----------------------------------------------------------------------
    body.append(_p("Spacing", style_id="Heading2"))
    body.append(_p("Space before 24pt", space_before_pt=24.0))
    body.append(_p("Space after 24pt", space_after_pt=24.0))
    body.append(_p("Line spacing 20pt", line_spacing_pt=20.0))
    body.append(_p("Page break before this paragraph", page_break_before=True))

    # -----------------------------------------------------------------------
    # Section 5: Run formatting
    # -----------------------------------------------------------------------
    body.append(_p("Run (Character) Formatting", style_id="Heading2"))

    body.append(_rp(
        _run("Bold ", bold=True),
        _run("Italic ", italic=True),
        _run("Underline ", underline=True),
        _run("Strikethrough ", strike=True),
        _run("Bold+Italic", bold=True, italic=True),
    ))
    body.append(_rp(
        _run("Arial 10pt ", font_name="Arial", font_size_pt=10.0),
        _run("Courier New 12pt ", font_name="Courier New", font_size_pt=12.0),
        _run("Times New Roman 14pt", font_name="Times New Roman", font_size_pt=14.0),
    ))
    body.append(_rp(
        _run("Red text ", color="FF0000"),
        _run("Green text ", color="00AA00"),
        _run("Blue text", color="0000FF"),
    ))
    body.append(_rp(
        _run("Yellow highlight ", highlight="yellow"),
        _run("Cyan highlight ", highlight="cyan"),
        _run("Red highlight", highlight="red"),
    ))
    body.append(_rp(
        _run("Normal "),
        _run("Superscript", vertical_align="superscript"),
        _run(" Normal "),
        _run("Subscript", vertical_align="subscript"),
        _run(" Normal"),
    ))
    body.append(_rp(_run("Line 1\nLine 2 (newline in same run)\nLine 3")))

    # -----------------------------------------------------------------------
    # Section 6: Inline image
    # -----------------------------------------------------------------------
    body.append(_p("Inline Image", style_id="Heading2"))
    body.append(_p("The paragraph below contains an inline image (8×8 white PNG):"))
    img = InlineImage(
        relationship_id="imgRId1",
        content_type="image/png",
        data=PNG_DATA,
        width_pt=72.0,
        height_pt=72.0,
        alt_text="Sample 8x8 PNG",
    )
    body.append(Paragraph(
        runs=(
            TextRun(text="Before image — "),
            ImageRun(image=img),
            TextRun(text=" — After image"),
        ),
        formatting=ParagraphFormatting(),
    ))

    # -----------------------------------------------------------------------
    # Section 7: Bullet list
    # -----------------------------------------------------------------------
    body.append(_p("Bullet List", style_id="Heading2"))
    nd_bullet = NumberingDefinition(
        abstract_num_id="1",
        levels=(
            ListLevel(level=0, num_fmt="bullet"),
            ListLevel(level=1, num_fmt="bullet"),
            ListLevel(level=2, num_fmt="bullet"),
        ),
    )
    for text in ("First bullet item", "Second bullet item", "Third bullet item"):
        body.append(_list_para(text, num_id="1", level=0))
    body.append(_list_para("Nested level 1", num_id="1", level=1))
    body.append(_list_para("Nested level 1 second item", num_id="1", level=1))
    body.append(_list_para("Nested level 2", num_id="1", level=2))
    body.append(_list_para("Back to level 0", num_id="1", level=0))

    # -----------------------------------------------------------------------
    # Section 8: Numbered list
    # -----------------------------------------------------------------------
    body.append(_p("Numbered List", style_id="Heading2"))
    nd_decimal = NumberingDefinition(
        abstract_num_id="2",
        levels=(ListLevel(level=0, num_fmt="decimal"),),
    )
    for text in ("First numbered item", "Second numbered item", "Third numbered item"):
        body.append(_list_para(text, num_id="2", level=0))

    # -----------------------------------------------------------------------
    # Section 9: Table
    # -----------------------------------------------------------------------
    body.append(_p("Table", style_id="Heading2"))

    def _cell(*texts, col_span=1, row_span=1, v_merge_start=False,
              v_merge_continue=False, width_pt=None):
        paras = tuple(_p(t) for t in texts)
        return TableCell(
            paragraphs=paras,
            col_span=col_span,
            row_span=row_span,
            v_merge_start=v_merge_start,
            v_merge_continue=v_merge_continue,
            width_pt=width_pt,
        )

    body.append(Table(
        rows=(
            TableRow(cells=(
                _cell("Header 1", width_pt=120.0),
                _cell("Header 2", width_pt=120.0),
                _cell("Header 3", width_pt=120.0),
            )),
            TableRow(cells=(
                _cell("Row 1, Col 1"),
                _cell("Row 1, Col 2"),
                _cell("Row 1, Col 3"),
            )),
            TableRow(cells=(
                _cell("Colspan 2", col_span=2),
                _cell("Normal"),
            )),
            TableRow(cells=(
                _cell("Row span start", row_span=2, v_merge_start=True),
                _cell("Row 3 Col 2"),
                _cell("Row 3 Col 3"),
            )),
            TableRow(cells=(
                _cell("", v_merge_continue=True),
                _cell("Row 4 Col 2"),
                _cell("Row 4 Col 3"),
            )),
        ),
        width_pt=360.0,
        col_widths_pt=(120.0, 120.0, 120.0),
    ))

    # -----------------------------------------------------------------------
    # Section 10: Hyperlinks
    # -----------------------------------------------------------------------
    body.append(_p("Hyperlinks", style_id="Heading2"))
    body.append(Paragraph(
        runs=(
            TextRun(text="Visit the "),
            Hyperlink(url="https://docwow.readthedocs.io", runs=(TextRun(text="docwow documentation"),)),
            TextRun(text=" for full details."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="Report bugs on "),
            Hyperlink(url="https://github.com/py-prit/docwow/issues", runs=(TextRun(text="GitHub Issues"),)),
            TextRun(text="."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="Contact us at "),
            Hyperlink(url="mailto:hello@example.com", runs=(TextRun(text="hello@example.com"),)),
            TextRun(text="."),
        ),
        formatting=ParagraphFormatting(),
    ))

    # Explicit page break before the headers/footers section
    body.append(PageBreak())

    # -----------------------------------------------------------------------
    # Section 11: Headers and footers
    # -----------------------------------------------------------------------
    body.append(_p("Headers and Footers", style_id="Heading2"))
    body.append(_p("This document has a default header and footer with page numbers."))
    body.append(_p("The header shows the document title; the footer shows 'Page N of M'."))

    # -----------------------------------------------------------------------
    # Section 12: Mixed content
    # -----------------------------------------------------------------------
    body.append(_p("Mixed Content", style_id="Heading2"))
    body.append(_p("A paragraph before a table."))
    body.append(Table(
        rows=(TableRow(cells=(
            TableCell(paragraphs=(_p("Inside table"),), width_pt=200.0),
        )),),
        width_pt=200.0,
        col_widths_pt=(200.0,),
    ))
    body.append(_p("A paragraph after the table."))
    for text in ("List after table item 1", "List after table item 2"):
        body.append(_list_para(text, num_id="3", level=0))
    body.append(_p("Normal paragraph after list."))

    # -----------------------------------------------------------------------
    # Styles and numbering
    # -----------------------------------------------------------------------
    styles = (
        Style(style_id="Heading1", name="heading 1", style_type="paragraph",
              run_fmt=RunFormatting(bold=True, font_size_pt=18.0)),
        Style(style_id="Heading2", name="heading 2", style_type="paragraph",
              run_fmt=RunFormatting(bold=True, font_size_pt=14.0)),
    )
    numbering = (
        nd_bullet,
        nd_decimal,
        NumberingDefinition(
            abstract_num_id="3",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        ),
    )

    # -----------------------------------------------------------------------
    # Headers / footers
    # -----------------------------------------------------------------------
    header_default = HeaderFooter(paragraphs=(
        Paragraph(
            runs=(TextRun(text="docwow showcase document", formatting=RunFormatting(italic=True)),),
            formatting=ParagraphFormatting(),
        ),
    ))

    footer_default = HeaderFooter(paragraphs=(
        Paragraph(
            runs=(
                TextRun(text="Page "),
                PageNumberField(field_type="PAGE"),
                TextRun(text=" of "),
                PageNumberField(field_type="NUMPAGES"),
            ),
            formatting=ParagraphFormatting(),
        ),
    ))

    return Document(
        body=tuple(body),
        styles=styles,
        numbering=numbering,
        page_width_pt=595.28,
        page_height_pt=841.89,
        margin_top_pt=72.0,
        margin_bottom_pt=72.0,
        margin_left_pt=72.0,
        margin_right_pt=72.0,
        header_default=header_default,
        footer_default=footer_default,
    )


if __name__ == "__main__":
    out = Path(__file__).parent / "showcase.docx"
    doc = build_showcase()
    write_docx(doc, target=str(out))
    print(f"Written: {out}  ({out.stat().st_size:,} bytes)")
