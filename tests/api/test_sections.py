"""Tests for multiple sections support via the mutable API."""

from __future__ import annotations

from pathlib import Path

import docwow
from docwow.api.paragraph import MutableParagraph, MutableSectionBreak, ParagraphCollection
from docwow.models.section import SectionBreak, SectionProperties

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestSectionProperties:
    def test_defaults(self):
        props = SectionProperties()
        assert props.page_width_pt == 595.28
        assert props.page_height_pt == 841.89
        assert props.margin_top_pt == 72.0
        assert props.break_type == "nextPage"

    def test_landscape(self):
        props = SectionProperties(page_width_pt=841.89, page_height_pt=595.28)
        assert props.page_width_pt > props.page_height_pt


class TestMutableSectionBreak:
    def test_defaults(self):
        sb = MutableSectionBreak()
        assert sb.page_width_pt == 595.28
        assert sb.break_type == "nextPage"

    def test_set_page_size(self):
        sb = MutableSectionBreak()
        result = sb.set_page_size(841.89, 595.28)
        assert sb.page_width_pt == 841.89
        assert sb.page_height_pt == 595.28
        assert result is sb

    def test_set_margins(self):
        sb = MutableSectionBreak()
        result = sb.set_margins(top_pt=36.0, bottom_pt=36.0, left_pt=54.0, right_pt=54.0)
        assert sb.margin_top_pt == 36.0
        assert sb.margin_left_pt == 54.0
        assert result is sb

    def test_set_break_type(self):
        sb = MutableSectionBreak()
        result = sb.set_break_type("continuous")
        assert sb.break_type == "continuous"
        assert result is sb

    def test_invalid_break_type(self):
        import pytest
        with pytest.raises(ValueError):
            MutableSectionBreak().set_break_type("invalid")

    def test_to_frozen(self):
        sb = MutableSectionBreak(
            page_width_pt=612.0, page_height_pt=792.0,
            margin_top_pt=36.0, break_type="continuous"
        )
        frozen = sb._to_frozen()
        assert isinstance(frozen, SectionBreak)
        assert frozen.properties.page_width_pt == 612.0
        assert frozen.properties.break_type == "continuous"


class TestParagraphCollectionAddSectionBreak:
    def test_add_section_break(self):
        pc = ParagraphCollection()
        sb = pc.add_section_break(break_type="nextPage", page_width_pt=612.0)
        assert isinstance(sb, MutableSectionBreak)
        assert len(pc) == 1
        assert sb.break_type == "nextPage"
        assert sb.page_width_pt == 612.0

    def test_add_section_break_defaults(self):
        pc = ParagraphCollection()
        sb = pc.add_section_break()
        assert sb.page_width_pt == 595.28
        assert sb.break_type == "nextPage"


class TestSectionsRoundTrip:
    def test_section_break_survives_docx_round_trip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        doc.paragraphs.add_paragraph("Section 1 content")
        doc.paragraphs.add_section_break(
            break_type="nextPage",
            page_width_pt=612.0,
            page_height_pt=792.0,
            margin_top_pt=54.0,
        )
        doc.paragraphs.add_paragraph("Section 2 content")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        section_breaks = [
            p for p in doc2.paragraphs if isinstance(p, MutableSectionBreak)
        ]
        assert len(section_breaks) >= 1
        sb = section_breaks[0]
        assert sb.page_width_pt == pytest.approx(612.0, abs=1.0)
        assert sb.break_type == "nextPage"

    def test_multiple_sections(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        doc.paragraphs.add_paragraph("S1")
        doc.paragraphs.add_section_break(break_type="nextPage", page_width_pt=612.0)
        doc.paragraphs.add_paragraph("S2")
        doc.paragraphs.add_section_break(break_type="continuous", page_width_pt=841.89)
        doc.paragraphs.add_paragraph("S3")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        breaks = [p for p in doc2.paragraphs if isinstance(p, MutableSectionBreak)]
        assert len(breaks) >= 2
        assert breaks[1].break_type == "continuous"


import pytest
