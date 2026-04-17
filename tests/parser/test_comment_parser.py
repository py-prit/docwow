"""Tests for docwow.parser.comment_parser."""
from __future__ import annotations

import io
import zipfile

import pytest

from docwow.parser.comment_parser import parse_comments


def _make_zf() -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        pass
    buf.seek(0)
    return zipfile.ZipFile(buf)


def _xml(body: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        + body
        + "</w:comments>"
    ).encode()


class TestParseCommentsEmpty:
    def test_empty_document(self):
        result = parse_comments(_xml(""), _make_zf(), {})
        assert result == ()


class TestParseCommentsSingle:
    def test_basic_comment(self):
        xml = _xml(
            '<w:comment xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'w:id="1" w:author="Alice" w:date="2024-01-15T10:00:00Z" w:initials="A">'
            "<w:p>"
            "<w:r><w:t>Great point!</w:t></w:r>"
            "</w:p>"
            "</w:comment>"
        )
        result = parse_comments(xml, _make_zf(), {})
        assert len(result) == 1
        c = result[0]
        assert c.comment_id == 1
        assert c.author == "Alice"
        assert c.date == "2024-01-15T10:00:00Z"
        assert c.initials == "A"
        assert len(c.paragraphs) == 1

    def test_comment_text_content(self):
        xml = _xml(
            '<w:comment xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'w:id="2" w:author="Bob" w:date="" w:initials="">'
            "<w:p><w:r><w:t>Fix this.</w:t></w:r></w:p>"
            "</w:comment>"
        )
        result = parse_comments(xml, _make_zf(), {})
        assert len(result) == 1
        para = result[0].paragraphs[0]
        from docwow.models.paragraph import TextRun
        assert any(isinstance(r, TextRun) and "Fix this" in r.text for r in para.runs)

    def test_missing_date_defaults_to_empty(self):
        xml = _xml(
            '<w:comment xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'w:id="1" w:author="Alice">'
            "<w:p><w:r><w:t>x</w:t></w:r></w:p>"
            "</w:comment>"
        )
        result = parse_comments(xml, _make_zf(), {})
        assert result[0].date == ""
        assert result[0].initials == ""


class TestParseCommentsMultiple:
    def test_two_comments(self):
        xml = _xml(
            '<w:comment xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'w:id="1" w:author="Alice" w:date="" w:initials="">'
            "<w:p><w:r><w:t>First</w:t></w:r></w:p>"
            "</w:comment>"
            '<w:comment xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'w:id="2" w:author="Bob" w:date="" w:initials="">'
            "<w:p><w:r><w:t>Second</w:t></w:r></w:p>"
            "</w:comment>"
        )
        result = parse_comments(xml, _make_zf(), {})
        assert len(result) == 2
        assert result[0].comment_id == 1
        assert result[1].comment_id == 2
        assert result[0].author == "Alice"
        assert result[1].author == "Bob"

    def test_invalid_id_skipped(self):
        xml = _xml(
            '<w:comment xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'w:id="bad" w:author="X" w:date="" w:initials="">'
            "<w:p><w:r><w:t>x</w:t></w:r></w:p>"
            "</w:comment>"
            '<w:comment xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'w:id="2" w:author="Y" w:date="" w:initials="">'
            "<w:p><w:r><w:t>y</w:t></w:r></w:p>"
            "</w:comment>"
        )
        result = parse_comments(xml, _make_zf(), {})
        assert len(result) == 1
        assert result[0].comment_id == 2
