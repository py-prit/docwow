"""
Unit conversion utilities for docwow.

OOXML stores lengths in several units depending on context:

  EMU (English Metric Units)
    Used for drawing/image dimensions.
    1 inch = 914,400 EMU  |  1 pt = 12,700 EMU

  Twips (twentieths of a point)
    Used for page size, margins, paragraph indents, and spacing.
    1 pt = 20 twips  |  1 inch = 1,440 twips

  Half-points
    Used for font sizes (w:sz).
    1 pt = 2 half-points

The internal Document Model stores ALL lengths in points (pt).
Conversion direction:
  Parse time  (DOCX → Model): EMU/twips/half-pts → pt
  Render time (Model → HTML): pt → CSS string ("12.5pt") or px
  Write time  (Model → DOCX): pt → EMU/twips/half-pts
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMU_PER_INCH: int = 914_400
PT_PER_INCH: int = 72
EMU_PER_PT: int = 12_700        # 914400 / 72
TWIPS_PER_PT: int = 20          # 1 twip = 1/20 of a point
TWIPS_PER_INCH: int = 1_440     # 20 * 72
DEFAULT_DPI: int = 96           # CSS/screen standard DPI


# ---------------------------------------------------------------------------
# EMU ↔ pt
# ---------------------------------------------------------------------------

def emu_to_pt(emu: int) -> float:
    """Convert EMU to points.  Used for image/drawing dimensions at parse time."""
    return emu / EMU_PER_PT


def pt_to_emu(pt: float) -> int:
    """Convert points to EMU, rounded to the nearest integer.  Used at write time."""
    return round(pt * EMU_PER_PT)


# ---------------------------------------------------------------------------
# Twips ↔ pt
# ---------------------------------------------------------------------------

def twips_to_pt(twips: int) -> float:
    """Convert twips (twentieths of a point) to points.
    Used for page geometry, margins, indents, and paragraph spacing at parse time.
    """
    return twips / TWIPS_PER_PT


def pt_to_twips(pt: float) -> int:
    """Convert points to twips, rounded to the nearest integer.  Used at write time."""
    return round(pt * TWIPS_PER_PT)


# ---------------------------------------------------------------------------
# Half-points ↔ pt
# ---------------------------------------------------------------------------

def half_pt_to_pt(half_pt: int) -> float:
    """Convert half-points to points.
    Used for font sizes (w:sz XML attribute) at parse time.
    Example: w:sz val="24" → 12 pt.
    """
    return half_pt / 2.0


def pt_to_half_pt(pt: float) -> int:
    """Convert points to half-points, rounded to the nearest integer.
    Used for font sizes at write time.
    """
    return round(pt * 2)


# ---------------------------------------------------------------------------
# pt ↔ px
# ---------------------------------------------------------------------------

def pt_to_px(pt: float, dpi: int = DEFAULT_DPI) -> float:
    """Convert points to pixels at a given screen DPI.
    Used at render time for CSS pixel values.
    Default DPI is 96 (the CSS/screen standard).
    """
    return pt * dpi / PT_PER_INCH


def px_to_pt(px: float, dpi: int = DEFAULT_DPI) -> float:
    """Convert pixels to points at a given screen DPI.
    Used at HTML parse time when CSS specifies sizes in px.
    """
    return px * PT_PER_INCH / dpi


# ---------------------------------------------------------------------------
# pt → CSS string
# ---------------------------------------------------------------------------

def pt_to_css(pt: float) -> str:
    """Format a point value as a CSS length string.

    Uses up to 2 decimal places, stripping unnecessary trailing zeros.
    Examples:
        12.0  → "12pt"
        12.5  → "12.5pt"
        12.75 → "12.75pt"
    """
    formatted = f"{pt:.2f}".rstrip("0").rstrip(".")
    return f"{formatted}pt"
