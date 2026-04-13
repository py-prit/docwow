"""Tests for MutableHeaderFooter and DocumentWrapper header/footer API."""
from __future__ import annotations

import pytest

from docwow.api.document import DocumentWrapper
from docwow.api.header_footer import MutableHeaderFooter
from docwow.api.paragraph import ParagraphCollection
from docwow.api.run import MutablePageNumberField, MutableRun
from docwow.models.header_footer import HeaderFooter


# ---------------------------------------------------------------------------
# MutablePageNumberField
# ---------------------------------------------------------------------------

class TestMutablePageNumberFieldConstruction:
    def test_default_field_type(self):
        f = MutablePageNumberField()
        assert f.field_type == "PAGE"

    def test_explicit_page(self):
        f = MutablePageNumberField("PAGE")
        assert f.field_type == "PAGE"

    def test_numpages(self):
        f = MutablePageNumberField("NUMPAGES")
        assert f.field_type == "NUMPAGES"

    def test_sectionpages(self):
        f = MutablePageNumberField("SECTIONPAGES")
        assert f.field_type == "SECTIONPAGES"

    def test_invalid_field_type_raises(self):
        with pytest.raises(ValueError, match="field_type"):
            MutablePageNumberField("PAGECOUNT")

    def test_repr(self):
        assert "PAGE" in repr(MutablePageNumberField("PAGE"))


class TestMutablePageNumberFieldSetters:
    def test_set_field_type(self):
        f = MutablePageNumberField("PAGE")
        result = f.set_field_type("NUMPAGES")
        assert f.field_type == "NUMPAGES"
        assert result is f

    def test_set_invalid_field_type_raises(self):
        f = MutablePageNumberField("PAGE")
        with pytest.raises(ValueError):
            f.set_field_type("BOGUS")


class TestMutablePageNumberFieldToFrozen:
    def test_to_frozen_page(self):
        from docwow.models.paragraph import PageNumberField
        frozen = MutablePageNumberField("PAGE")._to_frozen()
        assert isinstance(frozen, PageNumberField)
        assert frozen.field_type == "PAGE"

    def test_to_frozen_numpages(self):
        from docwow.models.paragraph import PageNumberField
        frozen = MutablePageNumberField("NUMPAGES")._to_frozen()
        assert frozen.field_type == "NUMPAGES"


# ---------------------------------------------------------------------------
# RunCollection.add_page_number
# ---------------------------------------------------------------------------

class TestRunCollectionPageNumber:
    def test_add_page_number_default(self):
        from docwow.api.run import RunCollection
        rc = RunCollection()
        f = rc.add_page_number()
        assert isinstance(f, MutablePageNumberField)
        assert f.field_type == "PAGE"
        assert len(rc) == 1
        assert rc[0] is f

    def test_add_page_number_numpages(self):
        from docwow.api.run import RunCollection
        rc = RunCollection()
        f = rc.add_page_number("NUMPAGES")
        assert f.field_type == "NUMPAGES"

    def test_frozen_page_number_field_rejected(self):
        from docwow.api.run import RunCollection
        from docwow.models.paragraph import PageNumberField
        rc = RunCollection()
        with pytest.raises(TypeError, match="frozen"):
            rc.append(PageNumberField(field_type="PAGE"))

    def test_to_frozen_includes_page_number(self):
        from docwow.api.run import RunCollection
        from docwow.models.paragraph import PageNumberField
        rc = RunCollection()
        rc.add_page_number("NUMPAGES")
        frozen = rc._to_frozen()
        assert len(frozen) == 1
        assert isinstance(frozen[0], PageNumberField)
        assert frozen[0].field_type == "NUMPAGES"


# ---------------------------------------------------------------------------
# MutableHeaderFooter
# ---------------------------------------------------------------------------

class TestMutableHeaderFooterConstruction:
    def test_empty_by_default(self):
        hf = MutableHeaderFooter()
        assert isinstance(hf.paragraphs, ParagraphCollection)
        assert len(hf.paragraphs) == 0

    def test_with_paragraphs(self):
        coll = ParagraphCollection()
        hf = MutableHeaderFooter(paragraphs=coll)
        assert hf.paragraphs is coll

    def test_repr(self):
        hf = MutableHeaderFooter()
        assert "0 paragraph" in repr(hf)


class TestMutableHeaderFooterToFrozen:
    def test_empty_to_frozen(self):
        hf = MutableHeaderFooter()
        frozen = hf._to_frozen()
        assert isinstance(frozen, HeaderFooter)
        assert frozen.paragraphs == ()

    def test_with_paragraph_to_frozen(self):
        from docwow.models.paragraph import Paragraph
        hf = MutableHeaderFooter()
        hf.paragraphs.add_paragraph("Header text")
        frozen = hf._to_frozen()
        assert isinstance(frozen, HeaderFooter)
        assert len(frozen.paragraphs) == 1
        assert isinstance(frozen.paragraphs[0], Paragraph)


# ---------------------------------------------------------------------------
# DocumentWrapper header/footer properties
# ---------------------------------------------------------------------------

class TestDocumentWrapperHeaderFooter:
    def test_header_creates_on_access(self):
        doc = DocumentWrapper()
        assert doc._header_default is None
        hdr = doc.header
        assert isinstance(hdr, MutableHeaderFooter)
        assert doc._header_default is hdr

    def test_footer_creates_on_access(self):
        doc = DocumentWrapper()
        assert doc._footer_default is None
        ftr = doc.footer
        assert isinstance(ftr, MutableHeaderFooter)
        assert doc._footer_default is ftr

    def test_header_first_default_none(self):
        doc = DocumentWrapper()
        assert doc.header_first is None

    def test_header_even_default_none(self):
        doc = DocumentWrapper()
        assert doc.header_even is None

    def test_footer_first_default_none(self):
        doc = DocumentWrapper()
        assert doc.footer_first is None

    def test_footer_even_default_none(self):
        doc = DocumentWrapper()
        assert doc.footer_even is None

    def test_title_pg_default_false(self):
        doc = DocumentWrapper()
        assert doc.title_pg is False

    def test_header_setter(self):
        doc = DocumentWrapper()
        hf = MutableHeaderFooter()
        doc.header = hf
        assert doc.header is hf

    def test_footer_setter(self):
        doc = DocumentWrapper()
        hf = MutableHeaderFooter()
        doc.footer = hf
        assert doc.footer is hf

    def test_header_first_setter(self):
        doc = DocumentWrapper()
        hf = MutableHeaderFooter()
        doc.header_first = hf
        assert doc.header_first is hf

    def test_header_even_setter(self):
        doc = DocumentWrapper()
        hf = MutableHeaderFooter()
        doc.header_even = hf
        assert doc.header_even is hf

    def test_footer_first_setter(self):
        doc = DocumentWrapper()
        hf = MutableHeaderFooter()
        doc.footer_first = hf
        assert doc.footer_first is hf

    def test_footer_even_setter(self):
        doc = DocumentWrapper()
        hf = MutableHeaderFooter()
        doc.footer_even = hf
        assert doc.footer_even is hf

    def test_title_pg_setter(self):
        doc = DocumentWrapper()
        doc.title_pg = True
        assert doc.title_pg is True

    def test_clear_header(self):
        doc = DocumentWrapper()
        _ = doc.header  # create
        doc.header = None
        assert doc._header_default is None

    def test_constructor_with_header(self):
        hf = MutableHeaderFooter()
        doc = DocumentWrapper(header_default=hf)
        assert doc.header is hf

    def test_constructor_with_title_pg(self):
        doc = DocumentWrapper(title_pg=True)
        assert doc.title_pg is True


# ---------------------------------------------------------------------------
# Convert: frozen ↔ wrapper round-trip
# ---------------------------------------------------------------------------

class TestConvertHeaderFooter:
    def test_document_from_frozen_no_hf(self):
        from docwow.api._convert import document_from_frozen
        from docwow.models.document import Document
        frozen = Document(body=(), styles=(), numbering=())
        wrapper = document_from_frozen(frozen)
        assert wrapper._header_default is None
        assert wrapper._footer_default is None
        assert wrapper.title_pg is False

    def test_document_from_frozen_with_header(self):
        from docwow.api._convert import document_from_frozen
        from docwow.models.document import Document
        from docwow.models.paragraph import Paragraph, TextRun
        from docwow.models.styles import ParagraphFormatting
        para = Paragraph(
            runs=(TextRun(text="Page header"),),
            formatting=ParagraphFormatting(),
        )
        hf = HeaderFooter(paragraphs=(para,))
        frozen = Document(body=(), styles=(), numbering=(), header_default=hf, title_pg=True)
        wrapper = document_from_frozen(frozen)
        assert isinstance(wrapper._header_default, MutableHeaderFooter)
        assert len(wrapper.header.paragraphs) == 1
        assert wrapper.title_pg is True

    def test_document_to_frozen_with_header(self):
        from docwow.api._convert import document_to_frozen
        doc = DocumentWrapper()
        doc.header.paragraphs.add_paragraph("Header line")
        doc.title_pg = True
        frozen = document_to_frozen(doc)
        assert frozen.header_default is not None
        assert len(frozen.header_default.paragraphs) == 1
        assert frozen.title_pg is True

    def test_document_to_frozen_no_hf(self):
        from docwow.api._convert import document_to_frozen
        doc = DocumentWrapper()
        frozen = document_to_frozen(doc)
        assert frozen.header_default is None
        assert frozen.footer_default is None

    def test_header_footer_round_trip(self):
        from docwow.api._convert import document_from_frozen, document_to_frozen
        # Build via API
        doc = DocumentWrapper()
        doc.header.paragraphs.add_paragraph("My Header")
        doc.footer.paragraphs.add_paragraph()
        doc.footer.paragraphs[-1].runs.add_page_number()
        doc.title_pg = True

        # Freeze and thaw
        frozen = document_to_frozen(doc)
        doc2 = document_from_frozen(frozen)

        assert doc2.title_pg is True
        assert len(doc2.header.paragraphs) == 1
        assert len(doc2.footer.paragraphs) == 1

    def test_run_from_frozen_page_number(self):
        from docwow.api._convert import run_from_frozen
        from docwow.models.paragraph import PageNumberField
        frozen = PageNumberField(field_type="NUMPAGES")
        mutable = run_from_frozen(frozen)
        assert isinstance(mutable, MutablePageNumberField)
        assert mutable.field_type == "NUMPAGES"
