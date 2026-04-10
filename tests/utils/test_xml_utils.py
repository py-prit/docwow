"""Tests for docwow.utils.xml_utils."""

import pytest
from lxml import etree

from docwow.utils.xml_utils import (
    NAMESPACES,
    attrib,
    find,
    findall,
    parse_xml,
    qn,
)

# Shorthand for building test elements without going through qn()
W_NS  = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS  = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS  = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _el(tag_clark: str, attribs: dict | None = None) -> etree._Element:
    """Create a bare lxml element for testing."""
    el = etree.Element(tag_clark, attrib=attribs or {})
    return el


def _child(parent: etree._Element, tag_clark: str, attribs: dict | None = None) -> etree._Element:
    child = etree.SubElement(parent, tag_clark, attrib=attribs or {})
    return child


# ---------------------------------------------------------------------------
# NAMESPACES registry
# ---------------------------------------------------------------------------

class TestNamespacesRegistry:
    def test_w_namespace(self):
        assert NAMESPACES["w"] == "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    def test_r_namespace(self):
        assert NAMESPACES["r"] == "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

    def test_wp_namespace(self):
        assert NAMESPACES["wp"] == "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

    def test_a_namespace(self):
        assert NAMESPACES["a"] == "http://schemas.openxmlformats.org/drawingml/2006/main"

    def test_pic_namespace(self):
        assert "pic" in NAMESPACES

    def test_v_namespace(self):
        assert "v" in NAMESPACES

    def test_mc_namespace(self):
        assert "mc" in NAMESPACES

    def test_w14_namespace(self):
        assert "w14" in NAMESPACES

    def test_w15_namespace(self):
        assert "w15" in NAMESPACES

    def test_ct_namespace(self):
        assert "ct" in NAMESPACES

    def test_rel_namespace(self):
        assert "rel" in NAMESPACES

    def test_all_values_are_strings(self):
        for k, v in NAMESPACES.items():
            assert isinstance(v, str), f"Namespace value for {k!r} is not a string"

    def test_all_values_are_uris(self):
        for k, v in NAMESPACES.items():
            assert v.startswith("http") or v.startswith("urn"), \
                f"Namespace URI for {k!r} looks invalid: {v!r}"


# ---------------------------------------------------------------------------
# qn
# ---------------------------------------------------------------------------

class TestQn:
    def test_w_paragraph(self):
        assert qn("w:p") == f"{{{W_NS}}}p"

    def test_w_run(self):
        assert qn("w:r") == f"{{{W_NS}}}r"

    def test_w_text(self):
        assert qn("w:t") == f"{{{W_NS}}}t"

    def test_r_prefix(self):
        assert qn("r:id") == f"{{{R_NS}}}id"

    def test_wp_prefix(self):
        assert qn("wp:inline") == f"{{{WP_NS}}}inline"

    def test_a_prefix(self):
        assert qn("a:blip") == f"{{{A_NS}}}blip"

    def test_all_registered_prefixes(self):
        # Every prefix in NAMESPACES must work
        local = "testElement"
        for prefix, uri in NAMESPACES.items():
            assert qn(f"{prefix}:{local}") == f"{{{uri}}}{local}"

    def test_unknown_prefix_raises_key_error(self):
        with pytest.raises(KeyError, match="not registered"):
            qn("xyz:foo")

    def test_no_colon_raises_value_error(self):
        with pytest.raises(ValueError, match="prefix:localname"):
            qn("wparagraph")

    def test_two_colons_raises_value_error(self):
        with pytest.raises(ValueError):
            qn("w:p:extra")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            qn("")

    def test_result_is_clark_notation(self):
        result = qn("w:p")
        assert result.startswith("{")
        assert "}" in result

    def test_localname_preserved(self):
        # The local part after the colon must be preserved exactly
        assert qn("w:sectPr").endswith("}sectPr")
        assert qn("w:pPr").endswith("}pPr")


# ---------------------------------------------------------------------------
# attrib
# ---------------------------------------------------------------------------

class TestAttrib:
    def test_namespaced_attr_present(self):
        el = _el(f"{{{W_NS}}}pPr", {f"{{{W_NS}}}val": "center"})
        assert attrib(el, "w:val") == "center"

    def test_namespaced_attr_absent_returns_default(self):
        el = _el(f"{{{W_NS}}}pPr")
        assert attrib(el, "w:val") is None

    def test_namespaced_attr_absent_custom_default(self):
        el = _el(f"{{{W_NS}}}pPr")
        assert attrib(el, "w:val", "auto") == "auto"

    def test_plain_attr_present(self):
        el = _el(f"{{{W_NS}}}p", {"id": "para1"})
        assert attrib(el, "id") == "para1"

    def test_plain_attr_absent_returns_none(self):
        el = _el(f"{{{W_NS}}}p")
        assert attrib(el, "id") is None

    def test_plain_attr_absent_custom_default(self):
        el = _el(f"{{{W_NS}}}p")
        assert attrib(el, "id", "fallback") == "fallback"

    def test_r_namespace_attr(self):
        el = _el(f"{{{W_NS}}}drawing", {f"{{{R_NS}}}id": "rId1"})
        assert attrib(el, "r:id") == "rId1"

    def test_multiple_attrs(self):
        el = _el(f"{{{W_NS}}}pgSz", {
            f"{{{W_NS}}}w": "12240",
            f"{{{W_NS}}}h": "15840",
        })
        assert attrib(el, "w:w") == "12240"
        assert attrib(el, "w:h") == "15840"


# ---------------------------------------------------------------------------
# find
# ---------------------------------------------------------------------------

class TestFind:
    def test_finds_direct_child(self):
        parent = _el(f"{{{W_NS}}}p")
        _child(parent, f"{{{W_NS}}}pPr")
        result = find(parent, "w:pPr")
        assert result is not None
        assert result.tag == f"{{{W_NS}}}pPr"

    def test_returns_none_when_missing(self):
        parent = _el(f"{{{W_NS}}}p")
        assert find(parent, "w:pPr") is None

    def test_finds_nested_path(self):
        p = _el(f"{{{W_NS}}}p")
        pPr = _child(p, f"{{{W_NS}}}pPr")
        _child(pPr, f"{{{W_NS}}}jc", {f"{{{W_NS}}}val": "center"})
        result = find(p, "w:pPr/w:jc")
        assert result is not None
        assert result.get(f"{{{W_NS}}}val") == "center"

    def test_finds_first_of_multiple(self):
        parent = _el(f"{{{W_NS}}}p")
        first = _child(parent, f"{{{W_NS}}}r")
        first.set(f"{{{W_NS}}}val", "first")
        second = _child(parent, f"{{{W_NS}}}r")
        second.set(f"{{{W_NS}}}val", "second")
        result = find(parent, "w:r")
        assert result is not None
        assert result.get(f"{{{W_NS}}}val") == "first"

    def test_different_namespaces_in_path(self):
        p = _el(f"{{{W_NS}}}p")
        drawing = _child(p, f"{{{W_NS}}}drawing")
        _child(drawing, f"{{{WP_NS}}}inline")
        result = find(p, "w:drawing/wp:inline")
        assert result is not None


# ---------------------------------------------------------------------------
# findall
# ---------------------------------------------------------------------------

class TestFindall:
    def test_finds_all_children(self):
        parent = _el(f"{{{W_NS}}}p")
        for _ in range(3):
            _child(parent, f"{{{W_NS}}}r")
        results = findall(parent, "w:r")
        assert len(results) == 3

    def test_empty_when_no_match(self):
        parent = _el(f"{{{W_NS}}}p")
        assert findall(parent, "w:r") == []

    def test_returns_list(self):
        parent = _el(f"{{{W_NS}}}p")
        result = findall(parent, "w:r")
        assert isinstance(result, list)

    def test_single_match(self):
        parent = _el(f"{{{W_NS}}}p")
        _child(parent, f"{{{W_NS}}}r")
        results = findall(parent, "w:r")
        assert len(results) == 1

    def test_does_not_return_wrong_tag(self):
        parent = _el(f"{{{W_NS}}}p")
        _child(parent, f"{{{W_NS}}}pPr")
        _child(parent, f"{{{W_NS}}}r")
        results = findall(parent, "w:pPr")
        assert len(results) == 1
        assert all(el.tag == f"{{{W_NS}}}pPr" for el in results)

    def test_nested_path(self):
        parent = _el(f"{{{W_NS}}}body")
        for _ in range(2):
            p = _child(parent, f"{{{W_NS}}}p")
            _child(p, f"{{{W_NS}}}r")
        # findall with nested path finds all matching descendants
        results = findall(parent, "w:p/w:r")
        assert len(results) == 2


# ---------------------------------------------------------------------------
# parse_xml
# ---------------------------------------------------------------------------

class TestParseXml:
    def test_parses_valid_xml(self):
        xml = b'<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'
        el = parse_xml(xml)
        assert el.tag == f"{{{W_NS}}}p"

    def test_returns_element(self):
        xml = b'<root/>'
        assert isinstance(parse_xml(xml), etree._Element)

    def test_parses_with_children(self):
        xml = (
            b'<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            b'  <w:r><w:t>Hello</w:t></w:r>'
            b'</w:p>'
        )
        el = parse_xml(xml)
        runs = el.findall(f"{{{W_NS}}}r")
        assert len(runs) == 1

    def test_strips_comments(self):
        xml = b'<root><!-- this is a comment --><child/></root>'
        el = parse_xml(xml)
        # Comments should be removed
        assert len(el) == 1
        assert el[0].tag == "child"

    def test_recovery_mode_tolerates_minor_issues(self):
        # Slightly malformed XML — recovery mode should not raise
        xml = b'<root><unclosed></root>'
        # lxml with recover=True will parse this without raising
        el = parse_xml(xml)
        assert el is not None

    def test_parses_attributes(self):
        xml = (
            b'<w:pgSz xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
            b' w:w="12240" w:h="15840"/>'
        )
        el = parse_xml(xml)
        assert el.get(f"{{{W_NS}}}w") == "12240"
        assert el.get(f"{{{W_NS}}}h") == "15840"
