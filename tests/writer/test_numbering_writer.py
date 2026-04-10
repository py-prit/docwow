"""Tests for docwow.writer.numbering_writer."""
from lxml import etree

from docwow.models.lists import ListLevel, NumberingDefinition
from docwow.models.styles import RunFormatting
from docwow.writer.numbering_writer import build_numbering_xml


def _xml(numbering):
    return build_numbering_xml(numbering).decode("utf-8")


class TestBuildNumberingXml:
    def test_returns_bytes(self):
        assert isinstance(build_numbering_xml(()), bytes)

    def test_root_is_numbering(self):
        root = etree.fromstring(build_numbering_xml(()))
        assert "numbering" in root.tag

    def test_empty_numbering_has_no_children(self):
        root = etree.fromstring(build_numbering_xml(()))
        assert len(root) == 0

    def test_abstract_num_present(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        )
        assert "abstractNum" in _xml((nd,))

    def test_abstract_num_id_attribute(self):
        nd = NumberingDefinition(
            abstract_num_id="3",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        )
        assert '"3"' in _xml((nd,))

    def test_num_element_present(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        )
        assert "<w:num " in _xml((nd,))

    def test_num_references_abstract(self):
        nd = NumberingDefinition(
            abstract_num_id="2",
            levels=(ListLevel(level=0, num_fmt="decimal"),),
        )
        xml = _xml((nd,))
        assert "abstractNumId" in xml
        assert '"2"' in xml

    def test_bullet_format(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        )
        assert "bullet" in _xml((nd,))

    def test_decimal_format(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="decimal"),),
        )
        assert "decimal" in _xml((nd,))

    def test_bullet_lvl_text_is_bullet_char(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        )
        assert "\u2022" in _xml((nd,))

    def test_lower_letter_format(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="lowerLetter"),),
        )
        assert "lowerLetter" in _xml((nd,))

    def test_upper_roman_format(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="upperRoman"),),
        )
        assert "upperRoman" in _xml((nd,))

    def test_none_format_empty_lvl_text(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="none"),),
        )
        xml = _xml((nd,))
        assert "none" in xml

    def test_multiple_levels(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(
                ListLevel(level=0, num_fmt="bullet"),
                ListLevel(level=1, num_fmt="bullet"),
            ),
        )
        xml = _xml((nd,))
        assert 'ilvl="0"' in xml
        assert 'ilvl="1"' in xml

    def test_level_indent_written(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet", indent_pt=72.0, hanging_pt=36.0),),
        )
        xml = _xml((nd,))
        assert "1440" in xml   # 72 * 20
        assert "720" in xml    # 36 * 20

    def test_default_indent_applied_when_zero(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet"),),
        )
        # Level 0 default: 36 * 1 * 20 = 720 twips left
        assert "720" in _xml((nd,))

    def test_multiple_definitions(self):
        nds = (
            NumberingDefinition(abstract_num_id="1", levels=(ListLevel(level=0, num_fmt="bullet"),)),
            NumberingDefinition(abstract_num_id="2", levels=(ListLevel(level=0, num_fmt="decimal"),)),
        )
        xml = _xml(nds)
        assert "bullet" in xml
        assert "decimal" in xml

    def test_run_fmt_on_level(self):
        nd = NumberingDefinition(
            abstract_num_id="1",
            levels=(ListLevel(level=0, num_fmt="bullet", run_fmt=RunFormatting(bold=True)),),
        )
        assert "<w:b" in _xml((nd,))
