"""
Color utilities for docwow.

Word colors come in three forms:

  1. Direct hex RGB  — <w:color w:val="FF0000"/>
  2. Auto/inherited  — <w:color w:val="auto"/> or absent entirely
  3. Theme color     — <w:color w:themeColor="accent1" w:themeTint="80"/>
                       or            w:themeColor="dk1"  w:themeShade="A0"/>

Theme colors are resolved against the document's theme palette (a dict mapping
theme color names such as "accent1" to 6-char hex RGB strings extracted from
word/theme/theme1.xml).

Tint and shade modify the resolved base color:
  - Shade darkens: R_new = round(R * shade_val / 255)
  - Tint lightens: R_new = round(R + (255 - R) * tint_val / 255)

In OOXML, tint and shade values are stored as 2-char hex strings (e.g. "80").
They are mutually exclusive in practice; if both are somehow present, shade
is applied first and tint second.

All colors in the Document Model are stored as uppercase 6-char hex RGB
strings (e.g. "FF0000"), or None to indicate auto/inherited.
"""

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_rgb: str) -> tuple[int, int, int]:
    """Convert a 6-char hex string (no leading #) to an (R, G, B) tuple."""
    h = hex_rgb.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert clamped (R, G, B) integers to an uppercase 6-char hex string."""
    return f"{r:02X}{g:02X}{b:02X}"


def _clamp(value: int) -> int:
    """Clamp an integer to the valid 0–255 byte range."""
    return max(0, min(255, value))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_hex(hex_rgb: str) -> str:
    """Return an uppercase 6-char hex RGB string, stripping any leading '#'."""
    return hex_rgb.lstrip("#").upper()


def apply_shade(hex_rgb: str, shade_hex: str) -> str:
    """Darken *hex_rgb* by a shade factor encoded as a 2-char hex byte.

    shade_hex "00" → black (fully shaded)
    shade_hex "FF" → original color (no shading)
    shade_hex "80" → ~50% darker

    Formula: R_new = round(R * shade_val / 255)
    """
    shade_val = int(shade_hex, 16)
    r, g, b = _hex_to_rgb(hex_rgb)
    return _rgb_to_hex(
        _clamp(round(r * shade_val / 255)),
        _clamp(round(g * shade_val / 255)),
        _clamp(round(b * shade_val / 255)),
    )


def apply_tint(hex_rgb: str, tint_hex: str) -> str:
    """Lighten *hex_rgb* by a tint factor encoded as a 2-char hex byte.

    tint_hex "00" → original color (no tinting)
    tint_hex "FF" → white (fully tinted)
    tint_hex "80" → ~50% lighter

    Formula: R_new = round(R + (255 - R) * tint_val / 255)
    """
    tint_val = int(tint_hex, 16)
    r, g, b = _hex_to_rgb(hex_rgb)
    return _rgb_to_hex(
        _clamp(round(r + (255 - r) * tint_val / 255)),
        _clamp(round(g + (255 - g) * tint_val / 255)),
        _clamp(round(b + (255 - b) * tint_val / 255)),
    )


def resolve_color(
    val: str | None,
    theme_color: str | None = None,
    theme_colors: dict[str, str] | None = None,
    tint: str | None = None,
    shade: str | None = None,
) -> str | None:
    """Resolve a Word color specification to an uppercase 6-char hex RGB string,
    or None if the color is auto/inherited.

    Args:
        val:          The w:val attribute ("FF0000", "auto", or None).
        theme_color:  The w:themeColor attribute name (e.g. "accent1", "dk1").
        theme_colors: Mapping of theme color names → 6-char hex RGB, extracted
                      from the document theme XML.  May be None if no theme.
        tint:         The w:themeTint attribute value (2-char hex, e.g. "80").
        shade:        The w:themeShade attribute value (2-char hex, e.g. "A0").

    Returns:
        Uppercase 6-char hex RGB string, or None for auto/inherited.
    """
    # Determine base color
    base: str | None = None

    if theme_color is not None and theme_colors is not None:
        base = theme_colors.get(theme_color)

    if base is None:
        if val is None or val.lower() == "auto":
            return None
        base = normalize_hex(val)
    else:
        base = normalize_hex(base)

    # Apply shade first (darkens), then tint (lightens) — OOXML convention
    if shade is not None:
        base = apply_shade(base, shade)
    if tint is not None:
        base = apply_tint(base, tint)

    return base
