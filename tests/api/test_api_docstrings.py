"""Enforce that every public method and property in docwow.api has a docstring.

This test exists so that the CI fails immediately when a developer adds a new
public API member without a docstring, rather than the gap being discovered
later during a manual documentation audit.

Rules:
- Every class in docwow.api.__all__ must have a class docstring.
- Every public method (not starting with '_') must have a docstring.
- Every public property (not starting with '_') must have a docstring.
  For properties the check looks at the fget function's __doc__.
"""

from __future__ import annotations

import inspect

import docwow.api as _api


# ---------------------------------------------------------------------------
# All public API classes (mirrors docs/api-reference/api-classes.md)
# ---------------------------------------------------------------------------

PUBLIC_CLASSES = [
    _api.DocumentWrapper,
    _api.ParagraphCollection,
    _api.MutableParagraph,
    _api.MutableListItem,
    _api.RunCollection,
    _api.MutableRun,
    _api.MutableImageRun,
    _api.MutableHyperlink,
    _api.MutablePageNumberField,
    _api.MutableHeaderFooter,
    _api.MutableImage,
    _api.MutableTable,
    _api.MutableTableRow,
    _api.MutableTableCell,
    _api.MutableBookmark,
    _api.MutableTableOfContents,
    _api.MutableTocEntry,
    _api.MutableFootnote,
    _api.MutableFootnoteRef,
    _api.MutableComment,
    _api.MutableCommentRef,
    _api.MutableTrackedChange,
    _api.MutableSectionBreak,
]


def _public_members(cls: type) -> list[tuple[str, object]]:
    """Return (name, member) pairs for all public members defined on cls itself."""
    results = []
    for name, member in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        # Only include members actually defined on this class, not inherited
        # from builtins (object) — avoids false positives on __repr__ etc.
        if name in ("mro",):
            continue
        results.append((name, member))
    return results


def test_class_docstrings() -> None:
    """Every public API class must have a class-level docstring."""
    missing = [cls.__name__ for cls in PUBLIC_CLASSES if not cls.__doc__]
    assert not missing, (
        f"Missing class docstrings: {missing}\n"
        "Add a docstring to each class listed above."
    )


def test_method_and_property_docstrings() -> None:
    """Every public method and property must have a docstring."""
    missing: list[str] = []

    for cls in PUBLIC_CLASSES:
        for name, member in _public_members(cls):
            if isinstance(member, property):
                doc = member.fget.__doc__ if member.fget else None
            elif callable(member):
                doc = member.__doc__
            else:
                continue  # plain attribute, not a method/property

            if not doc or not doc.strip():
                missing.append(f"{cls.__name__}.{name}")

    assert not missing, (
        "The following public API members are missing docstrings:\n"
        + "\n".join(f"  - {m}" for m in missing)
        + "\n\nAdd a one-line docstring to each member listed above."
    )
