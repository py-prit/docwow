"""Tests for DocwowConversionWarning and to_docx path selection."""
from __future__ import annotations

import warnings

import pytest

import docwow
from docwow.warnings import DocwowConversionWarning, suppress_warnings, strict_warnings, warn


class TestDocwowConversionWarning:
    def test_is_user_warning_subclass(self):
        assert issubclass(DocwowConversionWarning, UserWarning)

    def test_warn_issues_docwow_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warn("test message")
        assert len(caught) == 1
        assert issubclass(caught[0].category, DocwowConversionWarning)

    def test_warn_message_contains_github_link(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warn("unsupported element")
        msg = str(caught[0].message)
        assert "github.com/py-prit/docwow/issues" in msg

    def test_warn_message_contains_contributing_link(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warn("unsupported element")
        msg = str(caught[0].message)
        assert "CONTRIBUTING.md" in msg

    def test_warn_includes_original_message(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            warn("canvas element skipped")
        assert "canvas element skipped" in str(caught[0].message)

    def test_suppress_warnings(self):
        suppress_warnings()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DocwowConversionWarning)
            warn("should be suppressed")
        # restore
        warnings.resetwarnings()

    def test_strict_warnings_raises(self):
        strict_warnings()
        with pytest.raises(DocwowConversionWarning):
            warn("this should raise")
        warnings.resetwarnings()

    def test_exported_from_docwow_namespace(self):
        assert hasattr(docwow, "DocwowConversionWarning")
        assert hasattr(docwow, "suppress_warnings")
        assert hasattr(docwow, "strict_warnings")


class TestToDocxPathSelection:
    def test_docwow_html_accepted_without_flag(self, tmp_path):
        """Valid docwow HTML passes without is_foreign_html."""
        html = '<div class="dw-document"><p class="dw-p"><span class="dw-r">hi</span></p></div>'
        result = docwow.to_docx(html)
        assert isinstance(result, bytes)
        assert result[:2] == b"PK"  # ZIP magic bytes

    def test_foreign_html_without_flag_raises(self):
        """Plain HTML without dw-document raises ValueError."""
        html = "<html><body><p>Hello</p></body></html>"
        with pytest.raises(ValueError, match="is_foreign_html=True"):
            docwow.to_docx(html)

    def test_foreign_html_without_flag_error_message(self):
        """Error message shows the correct fix."""
        with pytest.raises(ValueError) as exc_info:
            docwow.to_docx("<p>hello</p>")
        assert "is_foreign_html=True" in str(exc_info.value)
        assert "dw-document" in str(exc_info.value)

    def test_foreign_html_with_flag_accepted(self):
        """Foreign HTML with is_foreign_html=True does not raise."""
        html = "<html><body><p>Hello</p></body></html>"
        result = docwow.to_docx(html, is_foreign_html=True)
        assert isinstance(result, bytes)

    def test_bytes_input_without_flag_raises(self):
        html = b"<html><body><p>Hello</p></body></html>"
        with pytest.raises(ValueError):
            docwow.to_docx(html)

    def test_bytes_input_with_flag_accepted(self):
        html = b"<html><body><p>Hello</p></body></html>"
        result = docwow.to_docx(html, is_foreign_html=True)
        assert isinstance(result, bytes)

    def test_fetch_images_flag_accepted(self):
        html = "<p>hello</p>"
        result = docwow.to_docx(html, is_foreign_html=True, fetch_images=True)
        assert isinstance(result, bytes)

    def test_fetch_external_css_flag_accepted(self):
        html = "<p>hello</p>"
        result = docwow.to_docx(html, is_foreign_html=True, fetch_external_css=True)
        assert isinstance(result, bytes)
