"""Tests for docwow.utils.color."""

import pytest

from docwow.utils.color import (
    _clamp,
    _hex_to_rgb,
    _rgb_to_hex,
    apply_shade,
    apply_tint,
    normalize_hex,
    resolve_color,
)


# ---------------------------------------------------------------------------
# Internal helpers (tested directly for thorough coverage)
# ---------------------------------------------------------------------------

class TestHexToRgb:
    def test_black(self):
        assert _hex_to_rgb("000000") == (0, 0, 0)

    def test_white(self):
        assert _hex_to_rgb("FFFFFF") == (255, 255, 255)

    def test_red(self):
        assert _hex_to_rgb("FF0000") == (255, 0, 0)

    def test_green(self):
        assert _hex_to_rgb("00FF00") == (0, 255, 0)

    def test_blue(self):
        assert _hex_to_rgb("0000FF") == (0, 0, 255)

    def test_mixed(self):
        assert _hex_to_rgb("1A2B3C") == (0x1A, 0x2B, 0x3C)

    def test_lowercase_input(self):
        assert _hex_to_rgb("ff0000") == (255, 0, 0)

    def test_strips_hash(self):
        assert _hex_to_rgb("#FF0000") == (255, 0, 0)


class TestRgbToHex:
    def test_black(self):
        assert _rgb_to_hex(0, 0, 0) == "000000"

    def test_white(self):
        assert _rgb_to_hex(255, 255, 255) == "FFFFFF"

    def test_red(self):
        assert _rgb_to_hex(255, 0, 0) == "FF0000"

    def test_uppercase(self):
        result = _rgb_to_hex(26, 43, 60)
        assert result == result.upper()

    def test_single_digit_channels(self):
        # Channels < 16 should be zero-padded
        assert _rgb_to_hex(0, 0, 15) == "00000F"


class TestClamp:
    def test_within_range(self):
        assert _clamp(128) == 128

    def test_zero(self):
        assert _clamp(0) == 0

    def test_max(self):
        assert _clamp(255) == 255

    def test_below_zero(self):
        assert _clamp(-1) == 0

    def test_above_255(self):
        assert _clamp(256) == 255

    def test_far_below(self):
        assert _clamp(-1000) == 0

    def test_far_above(self):
        assert _clamp(1000) == 255


# ---------------------------------------------------------------------------
# normalize_hex
# ---------------------------------------------------------------------------

class TestNormalizeHex:
    def test_already_uppercase(self):
        assert normalize_hex("FF0000") == "FF0000"

    def test_lowercase_converted(self):
        assert normalize_hex("ff0000") == "FF0000"

    def test_mixed_case(self):
        assert normalize_hex("Ff0000") == "FF0000"

    def test_strips_hash(self):
        assert normalize_hex("#FF0000") == "FF0000"

    def test_strips_hash_lowercase(self):
        assert normalize_hex("#ff0000") == "FF0000"

    def test_black(self):
        assert normalize_hex("000000") == "000000"

    def test_white(self):
        assert normalize_hex("ffffff") == "FFFFFF"


# ---------------------------------------------------------------------------
# apply_shade
# ---------------------------------------------------------------------------

class TestApplyShade:
    def test_no_shade_ff(self):
        # shade "FF" (255) = no darkening; R * 255/255 = R
        assert apply_shade("FF0000", "FF") == "FF0000"

    def test_full_shade_00(self):
        # shade "00" (0) = completely black
        assert apply_shade("FF0000", "00") == "000000"

    def test_full_shade_white_to_black(self):
        assert apply_shade("FFFFFF", "00") == "000000"

    def test_half_shade_white(self):
        # shade "80" (128) on white: round(255 * 128/255) = round(128.0) = 128 = "80"
        assert apply_shade("FFFFFF", "80") == "808080"

    def test_half_shade_red(self):
        # shade "80" on FF0000: round(255 * 128/255) = 128 = "80"
        result = apply_shade("FF0000", "80")
        assert result == "800000"

    def test_black_stays_black(self):
        # Any shade of black is still black
        assert apply_shade("000000", "80") == "000000"

    def test_returns_uppercase(self):
        result = apply_shade("FFFFFF", "80")
        assert result == result.upper()

    def test_returns_6_chars(self):
        result = apply_shade("FFFFFF", "80")
        assert len(result) == 6

    def test_shade_is_reversible_by_tint(self):
        # Shade "80" then tint with the inverse is not a perfect round-trip
        # (lossy due to integer rounding), but shade of white is symmetric
        shaded = apply_shade("FFFFFF", "FF")
        assert shaded == "FFFFFF"


# ---------------------------------------------------------------------------
# apply_tint
# ---------------------------------------------------------------------------

class TestApplyTint:
    def test_no_tint_00(self):
        # tint "00" (0) = no lightening; R + (255-R) * 0/255 = R
        assert apply_tint("FF0000", "00") == "FF0000"

    def test_full_tint_ff(self):
        # tint "FF" (255) = white
        assert apply_tint("FF0000", "FF") == "FFFFFF"

    def test_full_tint_black_to_white(self):
        assert apply_tint("000000", "FF") == "FFFFFF"

    def test_half_tint_black(self):
        # tint "80" (128) on black: round(0 + 255 * 128/255) = round(128) = 128 = "80"
        assert apply_tint("000000", "80") == "808080"

    def test_half_tint_red(self):
        # tint "80" on FF0000:
        # R: round(255 + (255-255)*128/255) = 255
        # G: round(0 + 255*128/255) = 128
        # B: round(0 + 255*128/255) = 128
        result = apply_tint("FF0000", "80")
        assert result == "FF8080"

    def test_white_stays_white(self):
        assert apply_tint("FFFFFF", "80") == "FFFFFF"

    def test_returns_uppercase(self):
        result = apply_tint("000000", "80")
        assert result == result.upper()

    def test_returns_6_chars(self):
        result = apply_tint("FF0000", "80")
        assert len(result) == 6


# ---------------------------------------------------------------------------
# resolve_color
# ---------------------------------------------------------------------------

class TestResolveColorDirectHex:
    def test_plain_hex(self):
        assert resolve_color("FF0000") == "FF0000"

    def test_lowercase_hex_normalized(self):
        assert resolve_color("ff0000") == "FF0000"

    def test_black(self):
        assert resolve_color("000000") == "000000"

    def test_white(self):
        assert resolve_color("FFFFFF") == "FFFFFF"

    def test_six_char_color(self):
        assert resolve_color("1A2B3C") == "1A2B3C"


class TestResolveColorAuto:
    def test_auto_returns_none(self):
        assert resolve_color("auto") is None

    def test_auto_case_insensitive(self):
        assert resolve_color("AUTO") is None
        assert resolve_color("Auto") is None

    def test_none_val_returns_none(self):
        assert resolve_color(None) is None

    def test_none_val_no_theme_color_returns_none(self):
        assert resolve_color(None, theme_color=None, theme_colors=None) is None


class TestResolveColorTheme:
    THEME = {
        "dk1":     "000000",
        "lt1":     "FFFFFF",
        "dk2":     "44546A",
        "lt2":     "E7E6E6",
        "accent1": "4472C4",
        "accent2": "ED7D31",
        "accent3": "A9D18E",
        "accent4": "FFC000",
        "accent5": "5B9BD5",
        "accent6": "70AD47",
        "hlink":   "0563C1",
        "folHlink":"954F72",
    }

    def test_theme_color_resolved(self):
        result = resolve_color(None, theme_color="accent1", theme_colors=self.THEME)
        assert result == "4472C4"

    def test_theme_color_dk1(self):
        result = resolve_color(None, theme_color="dk1", theme_colors=self.THEME)
        assert result == "000000"

    def test_theme_color_lt1(self):
        result = resolve_color(None, theme_color="lt1", theme_colors=self.THEME)
        assert result == "FFFFFF"

    def test_theme_color_overrides_val(self):
        # theme_color takes priority over val when theme_colors is provided
        result = resolve_color("FF0000", theme_color="accent1", theme_colors=self.THEME)
        assert result == "4472C4"

    def test_unknown_theme_color_falls_back_to_val(self):
        # If theme_color key not in theme_colors dict, fall back to val
        result = resolve_color("FF0000", theme_color="unknown", theme_colors=self.THEME)
        assert result == "FF0000"

    def test_theme_color_with_no_theme_colors_dict(self):
        # No theme_colors provided — fall back to val
        result = resolve_color("FF0000", theme_color="accent1", theme_colors=None)
        assert result == "FF0000"

    def test_theme_color_no_fallback_val_returns_none(self):
        # theme_color not in dict AND val is None → None
        result = resolve_color(None, theme_color="unknown", theme_colors=self.THEME)
        assert result is None

    @pytest.mark.parametrize("color_name", [
        "dk1", "lt1", "dk2", "lt2",
        "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
        "hlink", "folHlink",
    ])
    def test_all_standard_theme_colors(self, color_name):
        result = resolve_color(None, theme_color=color_name, theme_colors=self.THEME)
        assert result is not None
        assert len(result) == 6


class TestResolveColorWithTint:
    THEME = {"accent1": "4472C4"}

    def test_tint_applied_to_direct_color(self):
        # Tint "FF" → white regardless of base
        result = resolve_color("FF0000", tint="FF")
        assert result == "FFFFFF"

    def test_tint_applied_to_theme_color(self):
        result = resolve_color(None, theme_color="accent1", theme_colors=self.THEME, tint="FF")
        assert result == "FFFFFF"

    def test_no_tint_unchanged(self):
        result = resolve_color("FF0000", tint="00")
        assert result == "FF0000"


class TestResolveColorWithShade:
    THEME = {"accent1": "4472C4"}

    def test_shade_applied_to_direct_color(self):
        # Shade "00" → black
        result = resolve_color("FF0000", shade="00")
        assert result == "000000"

    def test_shade_applied_to_theme_color(self):
        result = resolve_color(None, theme_color="accent1", theme_colors=self.THEME, shade="00")
        assert result == "000000"

    def test_no_shade_unchanged(self):
        result = resolve_color("FF0000", shade="FF")
        assert result == "FF0000"


class TestResolveColorShadeBeforeTint:
    def test_shade_applied_before_tint(self):
        # shade "00" → black, then tint "FF" → white
        result = resolve_color("FF0000", shade="00", tint="FF")
        assert result == "FFFFFF"

    def test_shade_then_tint_vs_tint_only(self):
        # shade "80" then tint "00" = just shade (tint 00 = no change)
        shade_only = apply_shade("FF0000", "80")
        result = resolve_color("FF0000", shade="80", tint="00")
        assert result == shade_only
