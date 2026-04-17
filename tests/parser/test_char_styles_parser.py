"""Tests for character style parsing from DOCX."""

from __future__ import annotations

from pathlib import Path
import pytest

from docwow.parser.docx_parser import parse_docx
from docwow.models.paragraph import Paragraph, TextRun

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture(scope="module")
def char_styles_doc():
    data = (FIXTURES / "char_styles.docx").read_bytes()
    return parse_docx(data)


class TestCharStylesParser:
    def test_plain_run_has_no_char_style(self, char_styles_doc):
        para = char_styles_doc.body[0]
        assert isinstance(para, Paragraph)
        plain_run = para.runs[0]
        assert isinstance(plain_run, TextRun)
        assert plain_run.formatting.char_style_id is None

    def test_strong_run_has_char_style(self, char_styles_doc):
        para = char_styles_doc.body[0]
        assert isinstance(para, Paragraph)
        strong_run = para.runs[1]
        assert isinstance(strong_run, TextRun)
        assert strong_run.formatting.char_style_id == "Strong"

    def test_emphasis_run_has_char_style(self, char_styles_doc):
        para = char_styles_doc.body[0]
        assert isinstance(para, Paragraph)
        em_run = para.runs[3]
        assert isinstance(em_run, TextRun)
        assert em_run.formatting.char_style_id == "Emphasis"
