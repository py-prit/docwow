"""Tests for w:smallCaps and w:caps parsing."""

from __future__ import annotations

from lxml import etree

from docwow.parser.style_parser import parse_run_fmt

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _rPr(inner: str = "") -> etree._Element:
    xml = f'<w:rPr xmlns:w="{W}">{inner}</w:rPr>'
    return etree.fromstring(xml)


class TestSmallCapsParser:
    def test_small_caps_element_present(self):
        fmt = parse_run_fmt(_rPr("<w:smallCaps/>"))
        assert fmt.small_caps is True

    def test_small_caps_with_val_one(self):
        fmt = parse_run_fmt(_rPr('<w:smallCaps w:val="1"/>'))
        assert fmt.small_caps is True

    def test_small_caps_val_zero_is_false(self):
        fmt = parse_run_fmt(_rPr('<w:smallCaps w:val="0"/>'))
        assert fmt.small_caps is False

    def test_no_small_caps_element(self):
        fmt = parse_run_fmt(_rPr())
        assert fmt.small_caps is False


class TestAllCapsParser:
    def test_caps_element_present(self):
        fmt = parse_run_fmt(_rPr("<w:caps/>"))
        assert fmt.all_caps is True

    def test_caps_with_val_one(self):
        fmt = parse_run_fmt(_rPr('<w:caps w:val="1"/>'))
        assert fmt.all_caps is True

    def test_caps_val_zero_is_false(self):
        fmt = parse_run_fmt(_rPr('<w:caps w:val="0"/>'))
        assert fmt.all_caps is False

    def test_no_caps_element(self):
        fmt = parse_run_fmt(_rPr())
        assert fmt.all_caps is False


class TestBothTogether:
    def test_both_present(self):
        fmt = parse_run_fmt(_rPr("<w:smallCaps/><w:caps/>"))
        assert fmt.small_caps is True
        assert fmt.all_caps is True
