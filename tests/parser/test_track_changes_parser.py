"""Tests for track changes parsing (w:ins / w:del)."""
from __future__ import annotations

import zipfile
import io
from lxml import etree

from docwow.models.paragraph import TextRun, TrackedChange
from docwow.parser.body_parser import parse_body
from docwow.utils.xml_utils import qn


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _body_xml(inner: str) -> etree._Element:
    xml = f'<w:body xmlns:w="{W}">{inner}</w:body>'
    return etree.fromstring(xml)


def _empty_zf() -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w"):
        pass
    buf.seek(0)
    return zipfile.ZipFile(buf, "r")


class TestParseInsertion:
    def test_basic_insert(self):
        body = _body_xml(
            '<w:p>'
            '<w:ins w:id="1" w:author="Alice" w:date="2024-01-15T10:00:00Z">'
            '<w:r><w:t>inserted</w:t></w:r>'
            '</w:ins>'
            '</w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        assert len(elements) == 1
        runs = elements[0].runs
        assert len(runs) == 1
        tc = runs[0]
        assert isinstance(tc, TrackedChange)
        assert tc.change_type == "insert"
        assert tc.author == "Alice"
        assert tc.date == "2024-01-15T10:00:00Z"
        assert tc.change_id == 1
        assert len(tc.runs) == 1
        assert isinstance(tc.runs[0], TextRun)
        assert tc.runs[0].text == "inserted"

    def test_insert_multiple_runs(self):
        body = _body_xml(
            '<w:p>'
            '<w:ins w:id="2" w:author="Bob" w:date="">'
            '<w:r><w:t>hello</w:t></w:r>'
            '<w:r><w:t> world</w:t></w:r>'
            '</w:ins>'
            '</w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        tc = elements[0].runs[0]
        assert isinstance(tc, TrackedChange)
        assert len(tc.runs) == 2
        assert tc.runs[0].text == "hello"
        assert tc.runs[1].text == " world"

    def test_insert_no_author(self):
        body = _body_xml(
            '<w:p>'
            '<w:ins w:id="0">'
            '<w:r><w:t>text</w:t></w:r>'
            '</w:ins>'
            '</w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        tc = elements[0].runs[0]
        assert tc.author == ""

    def test_empty_insert_skipped(self):
        body = _body_xml('<w:p><w:ins w:id="1" w:author="X" w:date=""></w:ins></w:p>')
        elements = parse_body(body, _empty_zf(), {})
        assert len(elements[0].runs) == 0


class TestParseDeletion:
    def test_basic_delete(self):
        body = _body_xml(
            '<w:p>'
            '<w:del w:id="5" w:author="Carol" w:date="2024-02-01T08:00:00Z">'
            '<w:r><w:delText>removed</w:delText></w:r>'
            '</w:del>'
            '</w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        tc = elements[0].runs[0]
        assert isinstance(tc, TrackedChange)
        assert tc.change_type == "delete"
        assert tc.author == "Carol"
        assert tc.runs[0].text == "removed"

    def test_delete_uses_del_text_not_t(self):
        """w:del must read w:delText, not w:t."""
        body = _body_xml(
            '<w:p>'
            '<w:del w:id="1" w:author="X" w:date="">'
            '<w:r>'
            '<w:t>wrong</w:t>'
            '<w:delText>correct</w:delText>'
            '</w:r>'
            '</w:del>'
            '</w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        tc = elements[0].runs[0]
        assert tc.runs[0].text == "correct"

    def test_empty_delete_skipped(self):
        body = _body_xml('<w:p><w:del w:id="1" w:author="X" w:date=""></w:del></w:p>')
        elements = parse_body(body, _empty_zf(), {})
        assert len(elements[0].runs) == 0


class TestMixedContent:
    def test_insert_and_delete_in_same_paragraph(self):
        body = _body_xml(
            '<w:p>'
            '<w:r><w:t>normal </w:t></w:r>'
            '<w:ins w:id="1" w:author="A" w:date="">'
            '<w:r><w:t>added</w:t></w:r>'
            '</w:ins>'
            '<w:del w:id="2" w:author="B" w:date="">'
            '<w:r><w:delText>removed</w:delText></w:r>'
            '</w:del>'
            '</w:p>'
        )
        elements = parse_body(body, _empty_zf(), {})
        runs = elements[0].runs
        assert len(runs) == 3
        assert isinstance(runs[0], TextRun)
        assert isinstance(runs[1], TrackedChange)
        assert runs[1].change_type == "insert"
        assert isinstance(runs[2], TrackedChange)
        assert runs[2].change_type == "delete"
