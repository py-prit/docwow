"""Mutable header/footer wrapper for the programmatic API."""
from __future__ import annotations

from docwow.api.paragraph import ParagraphCollection
from docwow.models.header_footer import HeaderFooter


class MutableHeaderFooter:
    """
    A mutable header or footer — an editable collection of paragraphs.

    Obtain instances via :attr:`DocumentWrapper.header` and
    :attr:`DocumentWrapper.footer` (or the first/even variants).

    Example::

        doc = docwow.open("report.docx")

        # Edit the default header
        hdr = doc.header
        hdr.paragraphs.clear()
        hdr.paragraphs.add_paragraph("My Company — Confidential")

        # Add a footer with page numbers
        ftr = doc.footer
        ftr.paragraphs.clear()
        p = ftr.paragraphs.add_paragraph()
        p.runs.add_text("Page ")
        p.runs.add_page_number()
        p.runs.add_text(" of ")
        p.runs.add_page_number("NUMPAGES")

        doc.save("output.docx")
    """

    def __init__(self, paragraphs: ParagraphCollection | None = None) -> None:
        self._paragraphs = paragraphs if paragraphs is not None else ParagraphCollection()

    @property
    def paragraphs(self) -> ParagraphCollection:
        """The paragraph collection for this header or footer."""
        return self._paragraphs

    def _to_frozen(self) -> HeaderFooter:
        return HeaderFooter(paragraphs=self._paragraphs._to_frozen_body())

    def __repr__(self) -> str:
        return f"MutableHeaderFooter({len(self._paragraphs)} paragraph(s))"
