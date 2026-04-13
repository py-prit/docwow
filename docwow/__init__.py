"""
docwow — pixel-perfect Word ↔ HTML conversion.

Public API
----------
Parse::

    doc = docwow.open("report.docx")          # DOCX → DocumentWrapper
    doc = docwow.open(html_string)             # docwow HTML → DocumentWrapper

Edit::

    doc.paragraphs.add_paragraph("Hello", style_id="Heading1")
    doc.paragraphs[0].set_bold(True)
    doc.save("output.docx")

Convert::

    html = docwow.to_html("report.docx")      # DOCX → HTML string
    data = docwow.to_docx(html_string)        # HTML → DOCX bytes
    data = docwow.to_docx(html_string, target="out.docx")

Low-level::

    doc  = docwow.parse_docx(source)           # bytes | str | Path → Document
    doc  = docwow.parse_html(source)           # str | bytes → Document
    html = docwow.render_document(doc)         # Document → HTML string
    data = docwow.write_docx(doc, target=None) # Document → DOCX bytes
"""
from __future__ import annotations

from pathlib import Path

from docwow.html_parser.html_parser import parse_html
from docwow.parser.docx_parser import parse_docx
from docwow.renderer.html_renderer import render_document
from docwow.writer.docx_writer import write_docx

__all__ = [
    "open",
    "to_html",
    "to_docx",
    "parse_docx",
    "parse_html",
    "render_document",
    "write_docx",
]

__version__ = "0.3.0"


# ---------------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------------

def open(source: str | Path | bytes) -> "DocumentWrapper":
    """Parse a DOCX file *or* a docwow HTML string into a :class:`~docwow.api.document.DocumentWrapper`.

    Args:
        source: A file path (``str`` or :class:`~pathlib.Path`) or raw bytes
                pointing to a ``.docx`` file, **or** an HTML string produced
                by :func:`render_document`.

    Returns:
        A :class:`~docwow.api.document.DocumentWrapper` instance.
    """
    from docwow.api._convert import document_from_frozen

    if isinstance(source, (str, Path)):
        path = Path(source)
        try:
            is_docx = path.exists() and path.suffix.lower() in (".docx", ".doc")
        except (OSError, ValueError):
            is_docx = False
        if is_docx:
            return document_from_frozen(parse_docx(source))
        return document_from_frozen(parse_html(str(source)))
    if isinstance(source, bytes):
        if source[:2] == b"PK":
            return document_from_frozen(parse_docx(source))
        return document_from_frozen(parse_html(source))
    raise TypeError(f"Expected str, Path, or bytes; got {type(source).__name__}")


def to_html(source: str | Path | bytes) -> str:
    """Convert a DOCX file to a self-contained HTML string.

    Args:
        source: Path to a ``.docx`` file, or raw DOCX bytes.

    Returns:
        UTF-8 HTML string produced by :func:`render_document`.
    """
    doc = parse_docx(source)
    return render_document(doc)


def to_docx(
    html: str | bytes,
    target: str | Path | None = None,
) -> bytes:
    """Convert a docwow HTML string back to a DOCX file.

    Args:
        html:   HTML string or bytes produced by :func:`render_document` /
                :func:`to_html`.
        target: Optional output path.  When provided the bytes are also
                written to disk.

    Returns:
        Raw DOCX bytes (a valid ZIP archive).
    """
    doc = parse_html(html)
    return write_docx(doc, target=target)
