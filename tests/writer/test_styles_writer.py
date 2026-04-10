"""Tests for docwow.writer.styles_writer."""
from lxml import etree

from docwow.models.styles import ParagraphFormatting, RunFormatting, Style
from docwow.writer.styles_writer import build_styles_xml


def _parse(xml_bytes: bytes) -> etree._Element:
    return etree.fromstring(xml_bytes)


def _style(style_id, para_fmt=None, run_fmt=None, style_type="paragraph", based_on=None):
    return Style(
        style_id=style_id,
        name=style_id,
        style_type=style_type,
        based_on=based_on,
        paragraph_fmt=para_fmt,
        run_fmt=run_fmt,
    )


def _xml_str(styles):
    return build_styles_xml(styles).decode("utf-8")


class TestBuildStylesXml:
    def test_returns_bytes(self):
        assert isinstance(build_styles_xml(()), bytes)

    def test_root_is_styles(self):
        root = _parse(build_styles_xml(()))
        assert "styles" in root.tag

    def test_doc_defaults_present(self):
        assert "docDefaults" in _xml_str(())

    def test_default_font_calibri(self):
        assert "Calibri" in _xml_str(())

    def test_empty_styles_emits_normal_style(self):
        # build_styles_xml always injects a "Normal" base style for correct Word defaults
        xml = _xml_str(())
        assert "Normal" in xml
        assert 'styleId' in xml

    def test_style_id_present(self):
        s = _style("Heading1")
        assert "Heading1" in _xml_str((s,))

    def test_style_name_present(self):
        s = _style("MyStyle")
        assert "MyStyle" in _xml_str((s,))

    def test_style_type_attribute(self):
        s = _style("Normal", style_type="paragraph")
        assert 'type="paragraph"' in _xml_str((s,))

    def test_based_on(self):
        s = _style("Child", based_on="Normal")
        assert "basedOn" in _xml_str((s,))
        assert "Normal" in _xml_str((s,))

    def test_no_based_on_when_none(self):
        s = _style("Lone")
        assert "basedOn" not in _xml_str((s,))

    def test_multiple_styles(self):
        styles = (_style("A"), _style("B"))
        xml = _xml_str(styles)
        assert "A" in xml
        assert "B" in xml


class TestParaFmtInStyle:
    def _xml(self, **kw):
        return _xml_str((_style("S", para_fmt=ParagraphFormatting(**kw)),))

    def test_alignment_center(self):
        assert "center" in self._xml(alignment="center")

    def test_alignment_justify_becomes_both(self):
        assert "both" in self._xml(alignment="justify")

    def test_alignment_left(self):
        assert "left" in self._xml(alignment="left")

    def test_alignment_right(self):
        assert "right" in self._xml(alignment="right")

    def test_indent_left(self):
        assert "720" in self._xml(indent_left_pt=36.0)   # 36 * 20

    def test_indent_right(self):
        assert "360" in self._xml(indent_right_pt=18.0)

    def test_first_line_indent(self):
        xml = self._xml(indent_first_line_pt=18.0)
        assert "firstLine" in xml

    def test_hanging_indent(self):
        xml = self._xml(indent_first_line_pt=-18.0)
        assert "hanging" in xml
        assert "firstLine" not in xml

    def test_space_before(self):
        assert "240" in self._xml(space_before_pt=12.0)

    def test_space_after(self):
        assert "160" in self._xml(space_after_pt=8.0)

    def test_line_spacing(self):
        xml = self._xml(line_spacing_pt=14.0)
        assert "280" in xml       # 14 * 20
        assert "lineRule" in xml
        assert "exact" in xml

    def test_keep_together(self):
        assert "keepLines" in self._xml(keep_together=True)

    def test_keep_with_next(self):
        assert "keepNext" in self._xml(keep_with_next=True)

    def test_page_break_before(self):
        assert "pageBreakBefore" in self._xml(page_break_before=True)

    def test_default_formatting_no_jc(self):
        assert "jc" not in self._xml()

    def test_default_formatting_no_ind(self):
        assert "ind" not in self._xml()

    def test_default_formatting_no_spacing(self):
        assert "spacing" not in self._xml()


class TestRunFmtInStyle:
    def _xml(self, **kw):
        return _xml_str((_style("S", run_fmt=RunFormatting(**kw)),))

    def test_bold(self):
        assert "<w:b" in self._xml(bold=True)

    def test_italic(self):
        assert "<w:i" in self._xml(italic=True)

    def test_underline(self):
        xml = self._xml(underline=True)
        assert "u" in xml
        assert "single" in xml

    def test_strike(self):
        assert "strike" in self._xml(strike=True)

    def test_font_name(self):
        assert "Arial" in self._xml(font_name="Arial")

    def test_font_size(self):
        assert "28" in self._xml(font_size_pt=14.0)   # 14 * 2

    def test_color(self):
        assert "FF0000" in self._xml(color="FF0000")

    def test_highlight(self):
        assert "yellow" in self._xml(highlight="yellow")

    def test_superscript(self):
        assert "superscript" in self._xml(vertical_align="superscript")

    def test_subscript(self):
        assert "subscript" in self._xml(vertical_align="subscript")

    def test_default_run_fmt_no_b(self):
        assert "<w:b" not in self._xml()
