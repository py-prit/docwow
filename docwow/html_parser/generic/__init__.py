"""Generic (best-effort) HTML → DOCX converter.

Converts arbitrary HTML from any source — CMS output, rich text editors,
web pages — into a Word document.  Unlike the lossless docwow→DOCX path,
this conversion is best-effort: constructs with no Word equivalent are
skipped with a :class:`~docwow.DocwowConversionWarning`.

Entry point: :func:`~docwow.html_parser.generic.html_parser.parse_foreign_html`.
"""
