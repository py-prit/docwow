"""Tests for docwow.utils.units."""

import pytest

from docwow.utils.units import (
    DEFAULT_DPI,
    EMU_PER_INCH,
    EMU_PER_PT,
    PT_PER_INCH,
    TWIPS_PER_INCH,
    TWIPS_PER_PT,
    emu_to_pt,
    half_pt_to_pt,
    pt_to_css,
    pt_to_emu,
    pt_to_half_pt,
    pt_to_px,
    pt_to_twips,
    px_to_pt,
    twips_to_pt,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_emu_per_inch(self):
        assert EMU_PER_INCH == 914_400

    def test_pt_per_inch(self):
        assert PT_PER_INCH == 72

    def test_emu_per_pt(self):
        # 914400 / 72 = 12700 exactly
        assert EMU_PER_PT == 12_700
        assert EMU_PER_INCH == EMU_PER_PT * PT_PER_INCH

    def test_twips_per_pt(self):
        assert TWIPS_PER_PT == 20

    def test_twips_per_inch(self):
        assert TWIPS_PER_INCH == 1_440
        assert TWIPS_PER_INCH == TWIPS_PER_PT * PT_PER_INCH

    def test_default_dpi(self):
        assert DEFAULT_DPI == 96


# ---------------------------------------------------------------------------
# emu_to_pt
# ---------------------------------------------------------------------------

class TestEmuToPt:
    def test_zero(self):
        assert emu_to_pt(0) == 0.0

    def test_one_inch(self):
        # 914400 EMU = 72 pt (1 inch)
        assert emu_to_pt(914_400) == pytest.approx(72.0)

    def test_one_point(self):
        assert emu_to_pt(12_700) == pytest.approx(1.0)

    def test_half_point(self):
        assert emu_to_pt(6_350) == pytest.approx(0.5)

    def test_a4_width(self):
        # A4 width: 7,094,400 EMU = 558.8 pt? No — let's verify:
        # A4 = 210mm = 8.2677 inches = 595.276 pt ≈ 7,560,960 EMU
        assert emu_to_pt(7_560_960) == pytest.approx(595.35, abs=0.1)

    def test_returns_float(self):
        assert isinstance(emu_to_pt(12_700), float)

    def test_large_value(self):
        assert emu_to_pt(914_400 * 10) == pytest.approx(720.0)


# ---------------------------------------------------------------------------
# pt_to_emu
# ---------------------------------------------------------------------------

class TestPtToEmu:
    def test_zero(self):
        assert pt_to_emu(0.0) == 0

    def test_one_point(self):
        assert pt_to_emu(1.0) == 12_700

    def test_one_inch(self):
        assert pt_to_emu(72.0) == 914_400

    def test_returns_int(self):
        assert isinstance(pt_to_emu(12.0), int)

    def test_rounds_to_nearest(self):
        # 0.5 pt = 6350 EMU exactly
        assert pt_to_emu(0.5) == 6_350

    def test_fractional_rounds(self):
        # 1.1 pt = 13970 EMU (1.1 * 12700 = 13970.0)
        assert pt_to_emu(1.1) == 13_970

    def test_round_trip(self):
        for pt in [1.0, 12.0, 72.0, 36.5]:
            assert emu_to_pt(pt_to_emu(pt)) == pytest.approx(pt, rel=1e-4)


# ---------------------------------------------------------------------------
# twips_to_pt
# ---------------------------------------------------------------------------

class TestTwipsToPt:
    def test_zero(self):
        assert twips_to_pt(0) == 0.0

    def test_one_point(self):
        # 20 twips = 1 pt
        assert twips_to_pt(20) == pytest.approx(1.0)

    def test_one_inch(self):
        # 1440 twips = 72 pt = 1 inch
        assert twips_to_pt(1_440) == pytest.approx(72.0)

    def test_a4_width_twips(self):
        # Word stores A4 width as 11906 twips → 595.3 pt
        assert twips_to_pt(11_906) == pytest.approx(595.3, abs=0.1)

    def test_us_letter_width(self):
        # Letter width: 12240 twips → 612 pt
        assert twips_to_pt(12_240) == pytest.approx(612.0)

    def test_returns_float(self):
        assert isinstance(twips_to_pt(20), float)

    def test_half_point(self):
        # 10 twips = 0.5 pt
        assert twips_to_pt(10) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# pt_to_twips
# ---------------------------------------------------------------------------

class TestPtToTwips:
    def test_zero(self):
        assert pt_to_twips(0.0) == 0

    def test_one_point(self):
        assert pt_to_twips(1.0) == 20

    def test_one_inch(self):
        assert pt_to_twips(72.0) == 1_440

    def test_returns_int(self):
        assert isinstance(pt_to_twips(1.0), int)

    def test_rounds_to_nearest(self):
        # 0.5 pt = 10 twips exactly
        assert pt_to_twips(0.5) == 10

    def test_fractional_rounds(self):
        # 0.51 pt * 20 = 10.2 → rounds to 10
        assert pt_to_twips(0.51) == 10

    def test_round_trip(self):
        for pt in [1.0, 12.0, 72.0, 36.5]:
            assert twips_to_pt(pt_to_twips(pt)) == pytest.approx(pt, rel=1e-3)


# ---------------------------------------------------------------------------
# half_pt_to_pt
# ---------------------------------------------------------------------------

class TestHalfPtToPt:
    def test_zero(self):
        assert half_pt_to_pt(0) == 0.0

    def test_twelve_pt(self):
        # w:sz val="24" → 12 pt (the most common body text size)
        assert half_pt_to_pt(24) == pytest.approx(12.0)

    def test_eleven_pt(self):
        # Calibri 11 pt = val="22"
        assert half_pt_to_pt(22) == pytest.approx(11.0)

    def test_odd_half_point(self):
        # val="23" → 11.5 pt
        assert half_pt_to_pt(23) == pytest.approx(11.5)

    def test_large_size(self):
        # 72 pt heading = val="144"
        assert half_pt_to_pt(144) == pytest.approx(72.0)

    def test_returns_float(self):
        assert isinstance(half_pt_to_pt(24), float)


# ---------------------------------------------------------------------------
# pt_to_half_pt
# ---------------------------------------------------------------------------

class TestPtToHalfPt:
    def test_zero(self):
        assert pt_to_half_pt(0.0) == 0

    def test_twelve_pt(self):
        assert pt_to_half_pt(12.0) == 24

    def test_eleven_pt(self):
        assert pt_to_half_pt(11.0) == 22

    def test_half_pt_size(self):
        # 11.5 pt → 23
        assert pt_to_half_pt(11.5) == 23

    def test_returns_int(self):
        assert isinstance(pt_to_half_pt(12.0), int)

    def test_rounds_to_nearest(self):
        # 11.1 pt * 2 = 22.2 → rounds to 22
        assert pt_to_half_pt(11.1) == 22

    def test_round_trip(self):
        for pt in [8.0, 10.0, 11.0, 12.0, 14.0, 16.0, 24.0, 36.0, 72.0]:
            assert half_pt_to_pt(pt_to_half_pt(pt)) == pytest.approx(pt)


# ---------------------------------------------------------------------------
# pt_to_px
# ---------------------------------------------------------------------------

class TestPtToPx:
    def test_zero(self):
        assert pt_to_px(0.0) == 0.0

    def test_one_inch_at_96dpi(self):
        # 72 pt = 1 inch = 96 px at 96 DPI
        assert pt_to_px(72.0) == pytest.approx(96.0)

    def test_one_pt_at_96dpi(self):
        # 1 pt = 96/72 px ≈ 1.333 px
        assert pt_to_px(1.0) == pytest.approx(96 / 72)

    def test_custom_72dpi(self):
        # At 72 DPI, 1 pt = 1 px exactly
        assert pt_to_px(1.0, dpi=72) == pytest.approx(1.0)

    def test_custom_300dpi(self):
        # At 300 DPI, 72 pt = 300 px
        assert pt_to_px(72.0, dpi=300) == pytest.approx(300.0)

    def test_returns_float(self):
        assert isinstance(pt_to_px(12.0), float)

    def test_default_dpi_is_96(self):
        assert pt_to_px(72.0) == pt_to_px(72.0, dpi=96)


# ---------------------------------------------------------------------------
# px_to_pt
# ---------------------------------------------------------------------------

class TestPxToPt:
    def test_zero(self):
        assert px_to_pt(0.0) == 0.0

    def test_one_inch_at_96dpi(self):
        # 96 px at 96 DPI = 72 pt
        assert px_to_pt(96.0) == pytest.approx(72.0)

    def test_one_px_at_96dpi(self):
        assert px_to_pt(1.0) == pytest.approx(72 / 96)

    def test_custom_72dpi(self):
        assert px_to_pt(1.0, dpi=72) == pytest.approx(1.0)

    def test_round_trip(self):
        for pt in [1.0, 12.0, 72.0, 36.5]:
            assert px_to_pt(pt_to_px(pt)) == pytest.approx(pt, rel=1e-6)

    def test_returns_float(self):
        assert isinstance(px_to_pt(96.0), float)


# ---------------------------------------------------------------------------
# pt_to_css
# ---------------------------------------------------------------------------

class TestPtToCss:
    def test_integer_value(self):
        assert pt_to_css(12.0) == "12pt"

    def test_one_decimal(self):
        assert pt_to_css(12.5) == "12.5pt"

    def test_two_decimals(self):
        assert pt_to_css(12.75) == "12.75pt"

    def test_zero(self):
        assert pt_to_css(0.0) == "0pt"

    def test_strips_trailing_zeros(self):
        # 12.10 should become "12.1pt", not "12.10pt"
        assert pt_to_css(12.10) == "12.1pt"

    def test_no_trailing_dot(self):
        # 12.00 should become "12pt", not "12.pt"
        assert pt_to_css(12.00) == "12pt"

    def test_large_value(self):
        assert pt_to_css(595.28) == "595.28pt"

    def test_small_fractional(self):
        assert pt_to_css(0.5) == "0.5pt"

    def test_returns_string(self):
        assert isinstance(pt_to_css(12.0), str)

    def test_ends_with_pt(self):
        for val in [0.0, 1.0, 12.5, 72.0, 100.25]:
            assert pt_to_css(val).endswith("pt")

    @pytest.mark.parametrize("pt,expected", [
        (8.0,   "8pt"),
        (10.0,  "10pt"),
        (11.0,  "11pt"),
        (12.0,  "12pt"),
        (14.0,  "14pt"),
        (18.0,  "18pt"),
        (24.0,  "24pt"),
        (36.0,  "36pt"),
        (72.0,  "72pt"),
        (6.5,   "6.5pt"),
        (10.5,  "10.5pt"),
    ])
    def test_common_font_sizes(self, pt, expected):
        assert pt_to_css(pt) == expected
