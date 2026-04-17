"""CSS length unit → points conversion.

Only converts to pt — the internal unit used throughout docwow.
Unsupported units (%, vw, vh, etc.) return None; the caller decides
whether to warn or use a fallback.
"""
from __future__ import annotations

# 1 rem = root font size.  We assume the browser default of 16px = 12pt.
_ROOT_PT = 12.0

# CSS named font sizes mapped to pt
_NAMED_SIZES: dict[str, float] = {
    "xx-small": 6.0,
    "x-small":  7.5,
    "small":    9.0,
    "medium":   12.0,
    "large":    13.5,
    "x-large":  18.0,
    "xx-large": 24.0,
}


def css_value_to_pt(value: str, inherited_pt: float = 12.0) -> float | None:
    """Convert a CSS length value string to points.

    Args:
        value:        A CSS length string, e.g. ``"14px"``, ``"1.2em"``, ``"10pt"``.
        inherited_pt: The inherited font size in points, used to resolve ``em`` units.
                      Defaults to 12pt (Word / browser default).

    Returns:
        The equivalent value in points, or ``None`` if the unit is unsupported
        or the value cannot be parsed.
    """
    v = value.strip().lower()

    if v in _NAMED_SIZES:
        return _NAMED_SIZES[v]

    if v.endswith("pt"):
        return _parse_float(v[:-2])
    if v.endswith("px"):
        n = _parse_float(v[:-2])
        return n * 0.75 if n is not None else None   # 96 dpi → 72 pt/inch
    if v.endswith("rem"):
        n = _parse_float(v[:-3])
        return n * _ROOT_PT if n is not None else None
    if v.endswith("em"):
        n = _parse_float(v[:-2])
        return n * inherited_pt if n is not None else None
    if v.endswith("cm"):
        n = _parse_float(v[:-2])
        return n * 28.3465 if n is not None else None  # 1 cm ≈ 28.35 pt
    if v.endswith("mm"):
        n = _parse_float(v[:-2])
        return n * 2.83465 if n is not None else None
    if v.endswith("in"):
        n = _parse_float(v[:-2])
        return n * 72.0 if n is not None else None

    # Bare number — treat as px (common in older HTML)
    n = _parse_float(v)
    return n * 0.75 if n is not None else None


def _parse_float(s: str) -> float | None:
    try:
        return float(s.strip())
    except (ValueError, AttributeError):
        return None
