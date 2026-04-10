"""Shared low-level helpers for the HTML parser."""
from __future__ import annotations


def has_class(el, cls: str) -> bool:
    """Return True if *el* carries the given CSS class."""
    return cls in el.get("class", "").split()


def pt_val(s: str | None, default: float | None = None) -> float | None:
    """Parse a CSS pt string to float.

    Examples::

        pt_val("36pt")       -> 36.0
        pt_val("36.5pt")     -> 36.5
        pt_val(None)         -> None  (or *default*)
        pt_val(None, 0.0)    -> 0.0
    """
    if s is None:
        return default
    s = s.strip()
    if s.endswith("pt"):
        try:
            return float(s[:-2])
        except ValueError:
            return default
    return default
