"""docwow warning infrastructure.

All warnings issued during conversion are instances of
:class:`DocwowConversionWarning`.  Use the standard Python ``warnings``
module to control their behaviour::

    import warnings

    # Suppress all docwow warnings
    warnings.filterwarnings("ignore", category=docwow.DocwowConversionWarning)

    # Treat as errors (useful in CI / strict mode)
    warnings.filterwarnings("error", category=docwow.DocwowConversionWarning)

    # Redirect to a log file
    import logging
    logging.captureWarnings(True)
    logging.basicConfig(filename="conversion.log")

Or use the convenience helpers::

    docwow.suppress_warnings()
    docwow.strict_warnings()
"""
from __future__ import annotations

import warnings


class DocwowParseError(ValueError):
    """Raised when a DOCX file contains an invalid or unreadable value.

    This is raised instead of a bare ``ValueError`` or ``TypeError`` so
    callers can catch docwow-specific parse failures without accidentally
    swallowing unrelated errors.

    The exception message includes the element name, the offending value, and
    the file/attribute path to help users diagnose corrupted or non-standard
    DOCX files.
    """


class DocwowConversionWarning(UserWarning):
    """Issued when general HTML→DOCX conversion encounters something it
    cannot fully represent in Word, or skips an unsupported construct.

    The warning message always ends with a GitHub link so users can report
    missing features or contribute an implementation.
    """


_GITHUB_ISSUES = "https://github.com/py-prit/docwow/issues"
_CONTRIBUTING = "https://github.com/py-prit/docwow/blob/main/CONTRIBUTING.md"

_FOOTER = (
    f"\n  Want this supported? Open an issue: {_GITHUB_ISSUES}"
    f"\n  Contributions welcome: {_CONTRIBUTING}"
)


def warn(message: str) -> None:
    """Issue a :class:`DocwowConversionWarning` with the standard footer."""
    warnings.warn(message + _FOOTER, DocwowConversionWarning, stacklevel=3)


def suppress_warnings() -> None:
    """Suppress all :class:`DocwowConversionWarning` warnings globally."""
    warnings.filterwarnings("ignore", category=DocwowConversionWarning)


def strict_warnings() -> None:
    """Raise :class:`DocwowConversionWarning` as an exception (useful in CI)."""
    warnings.filterwarnings("error", category=DocwowConversionWarning)
