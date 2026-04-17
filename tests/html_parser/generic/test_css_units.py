"""Tests for CSS unit conversion."""
from __future__ import annotations

import pytest
from docwow.html_parser.generic.css_units import css_value_to_pt


class TestPtConversion:
    def test_pt_direct(self):
        assert css_value_to_pt("12pt") == pytest.approx(12.0)

    def test_pt_float(self):
        assert css_value_to_pt("10.5pt") == pytest.approx(10.5)


class TestPxConversion:
    def test_px_to_pt(self):
        assert css_value_to_pt("16px") == pytest.approx(12.0)

    def test_px_96dpi(self):
        assert css_value_to_pt("96px") == pytest.approx(72.0)

    def test_px_float(self):
        assert css_value_to_pt("14.4px") == pytest.approx(10.8)


class TestEmConversion:
    def test_em_with_default_inherited(self):
        assert css_value_to_pt("1em") == pytest.approx(12.0)

    def test_em_with_custom_inherited(self):
        assert css_value_to_pt("2em", inherited_pt=14.0) == pytest.approx(28.0)

    def test_em_fraction(self):
        assert css_value_to_pt("0.75em", inherited_pt=16.0) == pytest.approx(12.0)


class TestRemConversion:
    def test_rem_uses_root_12pt(self):
        assert css_value_to_pt("1rem") == pytest.approx(12.0)

    def test_rem_double(self):
        assert css_value_to_pt("2rem") == pytest.approx(24.0)


class TestPhysicalUnits:
    def test_cm(self):
        assert css_value_to_pt("1cm") == pytest.approx(28.3465, abs=0.01)

    def test_mm(self):
        assert css_value_to_pt("10mm") == pytest.approx(28.3465, abs=0.01)

    def test_inch(self):
        assert css_value_to_pt("1in") == pytest.approx(72.0)


class TestNamedSizes:
    def test_medium(self):
        assert css_value_to_pt("medium") == pytest.approx(12.0)

    def test_large(self):
        assert css_value_to_pt("large") == pytest.approx(13.5)

    def test_small(self):
        assert css_value_to_pt("small") == pytest.approx(9.0)


class TestUnsupportedUnits:
    def test_percent_returns_none(self):
        assert css_value_to_pt("50%") is None

    def test_vw_returns_none(self):
        assert css_value_to_pt("10vw") is None

    def test_empty_returns_none(self):
        assert css_value_to_pt("") is None

    def test_non_numeric_returns_none(self):
        assert css_value_to_pt("abc") is None

    def test_bare_percent_returns_none(self):
        assert css_value_to_pt("100%") is None


class TestBareNumber:
    def test_bare_number_treated_as_px(self):
        assert css_value_to_pt("16") == pytest.approx(12.0)

    def test_bare_zero(self):
        assert css_value_to_pt("0") == pytest.approx(0.0)


class TestWhitespace:
    def test_leading_trailing_whitespace(self):
        assert css_value_to_pt("  12pt  ") == pytest.approx(12.0)
