"""
Generate showcase.docx — a single DOCX produced by the docwow writer that
demonstrates every supported feature end-to-end.

This file is the source of truth for manual testing.  Open showcase.docx in
Word / LibreOffice and showcase.html in a browser after any feature change to
verify both outputs look correct.

Run from the project root::

    python tests/fixtures/generate_showcase.py

The test suite also regenerates showcase.docx / showcase.html automatically
on every run (see tests/test_integration.py::TestShowcase).
"""
from __future__ import annotations

import struct as _struct
import sys
import zlib as _zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from docwow.models.comment import Comment
from docwow.models.document import Document
from docwow.models.footnote import Footnote
from docwow.models.header_footer import HeaderFooter
from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.paragraph import (
    BookmarkStart, CommentRef, FootnoteRef, Hyperlink, ImageRun,
    PageBreak, PageNumberField, Paragraph, TextRun, TrackedChange,
)
from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.models.table import Table, TableCell, TableRow
from docwow.models.toc import TableOfContents, TocEntry
from docwow.writer.docx_writer import write_docx


# ---------------------------------------------------------------------------
# Minimal 16×16 4-quadrant PNG (red/yellow/green/blue)
# ---------------------------------------------------------------------------

def _make_color_png() -> bytes:
    def _chunk(tag: bytes, data: bytes) -> bytes:
        s = _struct.pack(">I", len(data)) + tag + data
        return s + _struct.pack(">I", _zlib.crc32(s[4:]) & 0xFFFFFFFF)
    w, h = 16, 16
    row_top = bytes([255, 0, 0] * 8 + [255, 255, 0] * 8)
    row_bot = bytes([0, 160, 0] * 8 + [0, 80, 200] * 8)
    raw = b"".join(b"\x00" + (row_top if y < h // 2 else row_bot) for y in range(h))
    ihdr = _struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", _zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )


PNG_DATA = _make_color_png()


# ---------------------------------------------------------------------------
# Paragraph helpers
# ---------------------------------------------------------------------------

def _p(text: str, **fmt_kw) -> Paragraph:
    """Plain paragraph with a single text run."""
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(**fmt_kw),
    )


def _ph(text: str, bookmark: str, **fmt_kw) -> Paragraph:
    """Heading paragraph with a BookmarkStart anchor so TOC links resolve."""
    return Paragraph(
        runs=(BookmarkStart(name=bookmark), TextRun(text=text)),
        formatting=ParagraphFormatting(**fmt_kw),
    )


def _rp(*runs, **fmt_kw) -> Paragraph:
    """Paragraph with arbitrary run objects."""
    return Paragraph(runs=tuple(runs), formatting=ParagraphFormatting(**fmt_kw))


def _run(text: str, **kw) -> TextRun:
    return TextRun(text=text, formatting=RunFormatting(**kw))


def _list_para(text: str, num_id: str, level: int = 0) -> Paragraph:
    return Paragraph(
        runs=(TextRun(text=text),),
        formatting=ParagraphFormatting(),
        list_info=ListInfo(num_id=num_id, level=level),
    )


def _cell(*texts, col_span=1, row_span=1, v_merge_start=False,
          v_merge_continue=False, width_pt=None) -> TableCell:
    return TableCell(
        paragraphs=tuple(_p(t) for t in texts),
        col_span=col_span,
        row_span=row_span,
        v_merge_start=v_merge_start,
        v_merge_continue=v_merge_continue,
        width_pt=width_pt,
    )


# ---------------------------------------------------------------------------
# Bookmark names (TOC targets — all must match TocEntry urls below)
# ---------------------------------------------------------------------------

BM = {
    "title":       "showcase-title",
    "para_fmt":    "showcase-para-fmt",
    "run_fmt":     "showcase-run-fmt",
    "images":      "showcase-images",
    "lists":       "showcase-lists",
    "tables":      "showcase-tables",
    "hyperlinks":  "showcase-hyperlinks",
    "bookmarks":   "showcase-bookmarks",
    "footnotes":   "showcase-footnotes",
    "comments":    "showcase-comments",
    "track":       "showcase-track-changes",
    "pagebreaks":  "showcase-pagebreaks",
    "pagefields":  "showcase-pagefields",
    "hf":          "showcase-hf",
    "toc":         "showcase-toc",
}


# ---------------------------------------------------------------------------
# build_showcase
# ---------------------------------------------------------------------------

def build_showcase() -> Document:
    body = []

    # -----------------------------------------------------------------------
    # Title
    # -----------------------------------------------------------------------
    body.append(_ph("docwow Showcase Document", BM["title"], style_id="Heading1"))
    body.append(_p(
        "This document is generated entirely by the docwow writer layer. "
        "It demonstrates every supported feature. "
        "Open showcase.html in a browser and showcase.docx in Word to verify "
        "that all features render correctly."
    ))

    # -----------------------------------------------------------------------
    # Table of Contents  — functional, clickable, at the top
    # -----------------------------------------------------------------------
    body.append(_ph("Table of Contents", BM["toc"], style_id="Heading2"))
    body.append(TableOfContents(
        title="Contents",
        entries=(
            TocEntry("docwow Showcase Document",    f"#{BM['title']}",      1),
            TocEntry("Table of Contents",           f"#{BM['toc']}",        1),
            TocEntry("Paragraph Formatting",        f"#{BM['para_fmt']}",   1),
            TocEntry("Run (Character) Formatting",  f"#{BM['run_fmt']}",    1),
            TocEntry("Inline Images",               f"#{BM['images']}",     1),
            TocEntry("Lists",                       f"#{BM['lists']}",      1),
            TocEntry("Tables",                      f"#{BM['tables']}",     1),
            TocEntry("Hyperlinks",                  f"#{BM['hyperlinks']}",  1),
            TocEntry("Bookmarks",                   f"#{BM['bookmarks']}",  1),
            TocEntry("Footnotes and Endnotes",      f"#{BM['footnotes']}",  1),
            TocEntry("Comments",                    f"#{BM['comments']}",   1),
            TocEntry("Track Changes",               f"#{BM['track']}",      1),
            TocEntry("Page Breaks",                 f"#{BM['pagebreaks']}", 1),
            TocEntry("Page Number Fields",          f"#{BM['pagefields']}", 1),
            TocEntry("Headers and Footers",         f"#{BM['hf']}",         1),
        ),
    ))

    # -----------------------------------------------------------------------
    # 1. Paragraph Formatting
    # -----------------------------------------------------------------------
    body.append(_ph("Paragraph Formatting", BM["para_fmt"], style_id="Heading1"))

    body.append(_p("Alignment", style_id="Heading2"))
    body.append(_p("Left-aligned paragraph (default).", alignment="left"))
    body.append(_p("Centre-aligned paragraph.", alignment="center"))
    body.append(_p("Right-aligned paragraph.", alignment="right"))
    body.append(_p(
        "Justified paragraph. Lorem ipsum dolor sit amet, consectetur "
        "adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        alignment="justify",
    ))

    body.append(_p("Indentation", style_id="Heading2"))
    body.append(_p("No indent (normal)."))
    body.append(_p("Left indent 36pt.", indent_left_pt=36.0))
    body.append(_p("Left indent 72pt.", indent_left_pt=72.0))
    body.append(_p("Right indent 36pt.", indent_right_pt=36.0))
    body.append(_p("First-line indent 36pt.", indent_first_line_pt=36.0))
    body.append(_p(
        "Hanging indent: first line protrudes left by 36pt.",
        indent_left_pt=72.0, indent_first_line_pt=-36.0,
    ))

    body.append(_p("Spacing", style_id="Heading2"))
    body.append(_p("Space-before 24pt.", space_before_pt=24.0))
    body.append(_p("Space-after 24pt.", space_after_pt=24.0))
    body.append(_p("Line-spacing 20pt.", line_spacing_pt=20.0))

    body.append(_p("Pagination flags", style_id="Heading2"))
    body.append(_p(
        "keep_together=True: Word keeps all lines of this paragraph on the same page.",
        keep_together=True,
    ))
    body.append(_p(
        "keep_with_next=True: Word keeps this paragraph on the same page as the one after it.",
        keep_with_next=True,
    ))
    body.append(_p("This paragraph follows the keep_with_next paragraph."))
    body.append(_p(
        "page_break_before=True: Word starts this paragraph on a new page.",
        page_break_before=True,
    ))

    # -----------------------------------------------------------------------
    # 2. Run (Character) Formatting
    # -----------------------------------------------------------------------
    body.append(_ph("Run (Character) Formatting", BM["run_fmt"], style_id="Heading1"))

    body.append(_rp(
        _run("Bold  ", bold=True),
        _run("Italic  ", italic=True),
        _run("Underline  ", underline=True),
        _run("Strikethrough  ", strike=True),
        _run("Bold + Italic", bold=True, italic=True),
    ))
    body.append(_rp(
        _run("Arial 10pt  ", font_name="Arial", font_size_pt=10.0),
        _run("Courier New 12pt  ", font_name="Courier New", font_size_pt=12.0),
        _run("Times New Roman 14pt", font_name="Times New Roman", font_size_pt=14.0),
    ))
    body.append(_rp(
        _run("Red  ", color="FF0000"),
        _run("Green  ", color="00AA00"),
        _run("Blue", color="0000FF"),
    ))
    body.append(_rp(
        _run("Yellow highlight  ", highlight="yellow"),
        _run("Cyan highlight  ", highlight="cyan"),
        _run("Red highlight", highlight="red"),
    ))
    body.append(_rp(
        _run("Normal "),
        _run("Superscript", vertical_align="superscript"),
        _run("  Normal  "),
        _run("Subscript", vertical_align="subscript"),
        _run("  Normal"),
    ))
    body.append(_rp(_run("Line 1\nLine 2 (newline inside one run)\nLine 3")))

    # -----------------------------------------------------------------------
    # 3. Inline Images
    # -----------------------------------------------------------------------
    body.append(_ph("Inline Images", BM["images"], style_id="Heading1"))
    body.append(_p("A 16×16 4-quadrant PNG embedded as an inline image run:"))
    img = InlineImage(
        relationship_id="imgRId1",
        content_type="image/png",
        data=PNG_DATA,
        width_pt=72.0,
        height_pt=72.0,
        alt_text="16×16 4-quadrant colour PNG",
    )
    body.append(Paragraph(
        runs=(
            TextRun(text="Before image — "),
            ImageRun(image=img),
            TextRun(text=" — after image."),
        ),
        formatting=ParagraphFormatting(),
    ))

    # -----------------------------------------------------------------------
    # 4. Lists
    # -----------------------------------------------------------------------
    body.append(_ph("Lists", BM["lists"], style_id="Heading1"))

    nd_bullet = NumberingDefinition(
        abstract_num_id="1",
        levels=(
            ListLevel(level=0, num_fmt="bullet"),
            ListLevel(level=1, num_fmt="bullet"),
            ListLevel(level=2, num_fmt="bullet"),
        ),
    )
    nd_decimal = NumberingDefinition(
        abstract_num_id="2",
        levels=(ListLevel(level=0, num_fmt="decimal"),),
    )
    nd_misc = NumberingDefinition(
        abstract_num_id="3",
        levels=(ListLevel(level=0, num_fmt="bullet"),),
    )

    body.append(_p("Bullet list (3 levels):", style_id="Heading2"))
    for t in ("First bullet", "Second bullet", "Third bullet"):
        body.append(_list_para(t, num_id="1", level=0))
    body.append(_list_para("Nested level 1 — first", num_id="1", level=1))
    body.append(_list_para("Nested level 1 — second", num_id="1", level=1))
    body.append(_list_para("Nested level 2", num_id="1", level=2))
    body.append(_list_para("Back to level 0", num_id="1", level=0))

    body.append(_p("Numbered list:", style_id="Heading2"))
    for t in ("First item", "Second item", "Third item"):
        body.append(_list_para(t, num_id="2", level=0))

    # -----------------------------------------------------------------------
    # 5. Tables
    # -----------------------------------------------------------------------
    body.append(_ph("Tables", BM["tables"], style_id="Heading1"))
    body.append(_p("3-column table with colspan and rowspan:"))
    body.append(Table(
        rows=(
            TableRow(cells=(
                _cell("Header 1", width_pt=120.0),
                _cell("Header 2", width_pt=120.0),
                _cell("Header 3", width_pt=120.0),
            )),
            TableRow(cells=(
                _cell("Row 1 Col 1"),
                _cell("Row 1 Col 2"),
                _cell("Row 1 Col 3"),
            )),
            TableRow(cells=(
                _cell("colspan=2", col_span=2),
                _cell("Normal"),
            )),
            TableRow(cells=(
                _cell("rowspan start", row_span=2, v_merge_start=True),
                _cell("Row 3 Col 2"),
                _cell("Row 3 Col 3"),
            )),
            TableRow(cells=(
                _cell("", v_merge_continue=True),
                _cell("Row 4 Col 2"),
                _cell("Row 4 Col 3"),
            )),
            TableRow(cells=(
                _cell("Row span start", width_pt=120.0),
                _cell("Row 5 Col 2"),
                _cell("Row 5 Col 3"),
            )),
        ),
        width_pt=360.0,
        col_widths_pt=(120.0, 120.0, 120.0),
    ))

    # -----------------------------------------------------------------------
    # 6. Hyperlinks
    # -----------------------------------------------------------------------
    body.append(_ph("Hyperlinks", BM["hyperlinks"], style_id="Heading1"))
    body.append(Paragraph(
        runs=(
            TextRun(text="External URL: "),
            Hyperlink(url="https://docwow.readthedocs.io",
                      runs=(TextRun(text="docwow documentation"),)),
            TextRun(text="."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="Bug reports: "),
            Hyperlink(url="https://github.com/py-prit/docwow/issues",
                      runs=(TextRun(text="GitHub Issues"),)),
            TextRun(text="."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="Mailto: "),
            Hyperlink(url="mailto:hello@example.com",
                      runs=(TextRun(text="hello@example.com"),)),
            TextRun(text="."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="Internal anchor: "),
            Hyperlink(url=f"#{BM['bookmarks']}",
                      runs=(TextRun(text="jump to Bookmarks section"),)),
            TextRun(text=" (should scroll to the Bookmarks heading above)."),
        ),
        formatting=ParagraphFormatting(),
    ))

    # -----------------------------------------------------------------------
    # 7. Bookmarks
    # -----------------------------------------------------------------------
    body.append(_ph("Bookmarks", BM["bookmarks"], style_id="Heading1"))
    body.append(Paragraph(
        runs=(
            BookmarkStart(name="bookmark-demo"),
            TextRun(
                text="This paragraph carries the named bookmark anchor 'bookmark-demo'. "
                     "The anchor is a zero-width invisible marker."
            ),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="This hyperlink jumps to the anchor above: "),
            Hyperlink(url="#bookmark-demo",
                      runs=(TextRun(text="go to bookmark-demo"),)),
            TextRun(text="."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(_p(
        "The TOC at the top of this document also uses bookmarks — each section heading "
        "carries a BookmarkStart run that the TOC hyperlinks resolve to."
    ))

    # -----------------------------------------------------------------------
    # 8. Footnotes and Endnotes
    # -----------------------------------------------------------------------
    body.append(_ph("Footnotes and Endnotes", BM["footnotes"], style_id="Heading1"))

    fn1 = Footnote(
        note_id=1,
        paragraphs=(Paragraph(
            runs=(TextRun(text="First footnote body — rendered at the bottom of the page in Word."),),
            formatting=ParagraphFormatting(),
        ),),
        note_type="footnote",
    )
    fn2 = Footnote(
        note_id=2,
        paragraphs=(Paragraph(
            runs=(TextRun(text="Second footnote body — attached to the second sentence."),),
            formatting=ParagraphFormatting(),
        ),),
        note_type="footnote",
    )
    en1 = Footnote(
        note_id=1,
        paragraphs=(Paragraph(
            runs=(TextRun(text="Endnote body — rendered at the very end of the document in Word."),),
            formatting=ParagraphFormatting(),
        ),),
        note_type="endnote",
    )

    body.append(Paragraph(
        runs=(
            TextRun(text="This sentence has a footnote reference"),
            FootnoteRef(note_id=1, note_type="footnote"),
            TextRun(text=" at the end."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="A second sentence with another footnote"),
            FootnoteRef(note_id=2, note_type="footnote"),
            TextRun(text=" and an endnote reference"),
            FootnoteRef(note_id=1, note_type="endnote"),
            TextRun(text="."),
        ),
        formatting=ParagraphFormatting(),
    ))

    # -----------------------------------------------------------------------
    # 9. Comments
    # -----------------------------------------------------------------------
    body.append(_ph("Comments", BM["comments"], style_id="Heading1"))
    body.append(_p(
        "Comments are annotations attached to specific points in the document text. "
        "In HTML they render as superscript reference markers (orange brackets) and "
        "a comment section at the bottom of the page. In DOCX they appear in the "
        "Word review pane."
    ))

    c1 = Comment(
        comment_id=1,
        author="Alice",
        date="2026-04-17T09:00:00Z",
        initials="A",
        paragraphs=(Paragraph(
            runs=(TextRun(text="This is a great example!"),),
            formatting=ParagraphFormatting(),
        ),),
    )
    c2 = Comment(
        comment_id=2,
        author="Bob",
        date="2026-04-17T10:00:00Z",
        initials="B",
        paragraphs=(Paragraph(
            runs=(TextRun(text="Consider adding more detail here."),),
            formatting=ParagraphFormatting(),
        ),),
    )
    body.append(Paragraph(
        runs=(
            TextRun(text="This sentence has a comment from Alice"),
            CommentRef(comment_id=1),
            TextRun(text=" attached at the end."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="This sentence has a comment from Bob"),
            CommentRef(comment_id=2),
            TextRun(text=" for review."),
        ),
        formatting=ParagraphFormatting(),
    ))

    # -----------------------------------------------------------------------
    # 10. Track Changes
    # -----------------------------------------------------------------------
    body.append(_ph("Track Changes", BM["track"], style_id="Heading1"))
    body.append(_p(
        "Track changes records insertions and deletions made by reviewers. "
        "In HTML, insertions render as green underlined text and deletions as "
        "red strikethrough text. In DOCX they appear in Word's review pane."
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="The original revenue figure was "),
            TrackedChange(
                change_type="delete",
                runs=(TextRun(text="$3.8 M"),),
                author="Alice",
                date="2026-04-17T09:00:00Z",
                change_id=10,
            ),
            TrackedChange(
                change_type="insert",
                runs=(TextRun(text="$4.2 M"),),
                author="Alice",
                date="2026-04-17T09:00:00Z",
                change_id=11,
            ),
            TextRun(text=" for the quarter."),
        ),
        formatting=ParagraphFormatting(),
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="Please "),
            TrackedChange(
                change_type="delete",
                runs=(TextRun(text="review"),),
                author="Bob",
                date="2026-04-17T10:00:00Z",
                change_id=12,
            ),
            TrackedChange(
                change_type="insert",
                runs=(TextRun(text="approve"),),
                author="Bob",
                date="2026-04-17T10:00:00Z",
                change_id=13,
            ),
            TextRun(text=" this change before the deadline."),
        ),
        formatting=ParagraphFormatting(),
    ))

    # -----------------------------------------------------------------------
    # 11. Page Breaks
    # -----------------------------------------------------------------------
    body.append(_ph("Page Breaks", BM["pagebreaks"], style_id="Heading1"))
    body.append(_p(
        "An explicit page break element follows. In HTML it renders as "
        "<div class=\"dw-page-break\"> (invisible, preserved for round-trip). "
        "In Word / LibreOffice it forces a new page."
    ))
    body.append(PageBreak())
    body.append(_p(
        "This paragraph is immediately after the explicit page break. "
        "In Word it should appear at the top of a new page."
    ))

    # -----------------------------------------------------------------------
    # 10. Page Number Fields
    # -----------------------------------------------------------------------
    body.append(_ph("Page Number Fields", BM["pagefields"], style_id="Heading1"))
    body.append(_p(
        "Page number fields can appear anywhere in the body, not just headers/footers. "
        "The paragraph below uses PAGE and NUMPAGES fields:"
    ))
    body.append(Paragraph(
        runs=(
            TextRun(text="You are on page "),
            PageNumberField(field_type="PAGE"),
            TextRun(text=" of "),
            PageNumberField(field_type="NUMPAGES"),
            TextRun(text=" total pages."),
        ),
        formatting=ParagraphFormatting(alignment="center"),
    ))
    body.append(_p(
        "In HTML these render as <span class=\"dw-field\" data-dw-field=\"PAGE\">1</span> "
        "placeholders (static). In Word they update to the actual page number."
    ))

    # -----------------------------------------------------------------------
    # 11. Headers and Footers
    # -----------------------------------------------------------------------
    body.append(_ph("Headers and Footers", BM["hf"], style_id="Heading1"))
    body.append(_p(
        "This document has a default header and footer defined at the Document level. "
        "The header (top of each page in Word) shows the document title in italics. "
        "The footer (bottom of each page) shows 'Page N of M'."
    ))
    body.append(_p(
        "In HTML, headers and footers are rendered as <header> and <footer> elements. "
        "Page-number-only footer paragraphs are hidden (display:none) in the browser "
        "but survive the HTML → DOCX round-trip so Word can display the correct values."
    ))

    # -----------------------------------------------------------------------
    # Numbering, styles, headers/footers, footnotes/endnotes
    # -----------------------------------------------------------------------
    styles = (
        Style(style_id="Heading1", name="heading 1", style_type="paragraph",
              run_fmt=RunFormatting(bold=True, font_size_pt=18.0)),
        Style(style_id="Heading2", name="heading 2", style_type="paragraph",
              run_fmt=RunFormatting(bold=True, font_size_pt=14.0)),
    )
    numbering = (nd_bullet, nd_decimal, nd_misc)

    header_default = HeaderFooter(paragraphs=(
        Paragraph(
            runs=(TextRun(
                text="docwow Showcase Document",
                formatting=RunFormatting(italic=True),
            ),),
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
            formatting=ParagraphFormatting(alignment="center"),
        ),
    ))

    return Document(
        body=tuple(body),
        styles=styles,
        numbering=numbering,
        page_width_pt=595.28,    # A4
        page_height_pt=841.89,
        margin_top_pt=72.0,      # 1 inch
        margin_bottom_pt=72.0,
        margin_left_pt=72.0,
        margin_right_pt=72.0,
        header_default=header_default,
        footer_default=footer_default,
        footnotes=(fn1, fn2),
        endnotes=(en1,),
        comments=(c1, c2),
    )


if __name__ == "__main__":
    out = Path(__file__).parent / "showcase.docx"
    doc = build_showcase()
    write_docx(doc, target=str(out))
    print(f"Written: {out}  ({out.stat().st_size:,} bytes)")
