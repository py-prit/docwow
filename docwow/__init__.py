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

    html = docwow.to_html("report.docx")                   # DOCX → HTML string
    html = docwow.to_html("report.docx", page_view=True)   # with page styling + @page print rules
    data = docwow.to_docx(html_string)                     # HTML → DOCX bytes
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
from docwow.warnings import DocwowConversionWarning, DocwowParseError, suppress_warnings, strict_warnings
from docwow.writer.docx_writer import write_docx

__all__ = [
    "open",
    "to_html",
    "to_docx",
    "parse_docx",
    "parse_html",
    "render_document",
    "write_docx",
    "DocwowConversionWarning",
    "DocwowParseError",
    "suppress_warnings",
    "strict_warnings",
]

__version__ = "0.9.0"


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


def to_html(source: str | Path | bytes, page_view: bool = False) -> str:
    """Convert a DOCX file to a self-contained HTML string.

    Args:
        source:    Path to a ``.docx`` file, or raw DOCX bytes.
        page_view: When True, styles the output as a physical page and adds
                   ``@media print`` / ``@page`` rules for correct browser
                   printing and PDF export.

    Returns:
        UTF-8 HTML string produced by :func:`render_document`.
    """
    doc = parse_docx(source)
    return render_document(doc, page_view=page_view)


def to_docx(
    html: str | bytes,
    target: str | Path | None = None,
    *,
    is_foreign_html: bool = False,
    fetch_images: bool = False,
    fetch_external_css: bool = False,
) -> bytes:
    """Convert an HTML string to a DOCX file.

    Args:
        html:               HTML string or bytes.
        target:             Optional output path.  When provided the bytes are
                            also written to disk.
        is_foreign_html:    Set to ``True`` to convert arbitrary HTML from any
                            source (CMS, rich text editor, web page, etc.).
                            When ``False`` (default), the HTML must have been
                            produced by docwow — passing foreign HTML without
                            this flag raises :exc:`ValueError`.
        fetch_images:       When ``True``, remote ``<img src="https://...">``
                            URLs are downloaded and embedded.  Default
                            ``False`` — remote images are skipped with a
                            :class:`~docwow.DocwowConversionWarning`.
                            Only used when ``is_foreign_html=True``.
        fetch_external_css: When ``True``, ``<link rel="stylesheet">`` URLs
                            are downloaded and applied.  Default ``False`` —
                            external stylesheets are ignored with a warning.
                            Only used when ``is_foreign_html=True``.

    Returns:
        Raw DOCX bytes (a valid ZIP archive).

    Raises:
        ValueError: If ``is_foreign_html=False`` and the HTML does not appear
                    to be docwow output (no ``dw-document`` element found).
    """
    if is_foreign_html:
        from docwow.html_parser.generic.html_parser import parse_foreign_html
        doc = parse_foreign_html(
            html,
            fetch_images=fetch_images,
            fetch_external_css=fetch_external_css,
        )
    else:
        _html = html if isinstance(html, str) else html.decode("utf-8")
        if "dw-document" not in _html:
            raise ValueError(
                "This HTML does not appear to be docwow output (no dw-document element found).\n"
                "To convert arbitrary HTML, pass is_foreign_html=True:\n"
                "    docwow.to_docx(html, is_foreign_html=True)"
            )
        doc = parse_html(html)
    return write_docx(doc, target=target)
