"""Tests for CSS helper functions in element_parser."""
from __future__ import annotations

import warnings
import pytest

from docwow.html_parser.generic.element_parser import _css_color_to_hex, _css_alignment
from docwow.html_parser.generic.html_parser import parse_foreign_html
from docwow.warnings import DocwowConversionWarning


class TestCssColorToHex:
    def test_named_color(self):
        assert _css_color_to_hex("red") == "FF0000"

    def test_named_color_black(self):
        assert _css_color_to_hex("black") == "000000"

    def test_named_color_white(self):
        assert _css_color_to_hex("white") == "FFFFFF"

    def test_hex_6digit(self):
        assert _css_color_to_hex("#FF0000") == "FF0000"

    def test_hex_3digit_expands(self):
        assert _css_color_to_hex("#F00") == "FF0000"

    def test_hex_lowercase(self):
        assert _css_color_to_hex("#ff0000") == "FF0000"

    def test_rgb_function(self):
        assert _css_color_to_hex("rgb(255, 0, 0)") == "FF0000"

    def test_rgb_no_spaces(self):
        assert _css_color_to_hex("rgb(0,128,0)") == "008000"

    def test_rgba_ignores_alpha(self):
        assert _css_color_to_hex("rgba(255, 0, 0, 0.5)") == "FF0000"

    def test_transparent_returns_none(self):
        assert _css_color_to_hex("transparent") is None

    def test_inherit_returns_none(self):
        assert _css_color_to_hex("inherit") is None

    def test_none_returns_none(self):
        assert _css_color_to_hex(None) is None

    def test_invalid_returns_none(self):
        assert _css_color_to_hex("notacolor") is None

    def test_whitespace_stripped(self):
        assert _css_color_to_hex("  red  ") == "FF0000"


class TestCssAlignment:
    def test_left(self):
        assert _css_alignment("left") == "left"

    def test_center(self):
        assert _css_alignment("center") == "center"

    def test_right(self):
        assert _css_alignment("right") == "right"

    def test_justify(self):
        assert _css_alignment("justify") == "justify"

    def test_start_maps_to_left(self):
        assert _css_alignment("start") == "left"

    def test_end_maps_to_right(self):
        assert _css_alignment("end") == "right"

    def test_none_returns_none(self):
        assert _css_alignment(None) is None

    def test_unknown_returns_none(self):
        assert _css_alignment("inherit") is None


class TestExternalCssWarning:
    def test_warns_when_external_css_found_without_flag(self):
        html = '<html><head><link rel="stylesheet" href="https://example.com/style.css"></head><body><p>text</p></body></html>'
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            parse_foreign_html(html, fetch_external_css=False)
        msgs = [str(w.message) for w in caught if issubclass(w.category, DocwowConversionWarning)]
        assert any("fetch_external_css=True" in m for m in msgs)

    def test_no_warning_without_external_css(self):
        html = "<html><head><style>p{color:red}</style></head><body><p>text</p></body></html>"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            parse_foreign_html(html, fetch_external_css=False)
        msgs = [str(w.message) for w in caught if issubclass(w.category, DocwowConversionWarning)]
        assert not any("fetch_external_css" in m for m in msgs)
