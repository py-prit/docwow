"""Tests for docwow.writer.parts_writer and ._xml utilities."""
import pytest
from lxml import etree

from docwow.writer._xml import pt_tw, pt_emu, pt_hp, wn, rn, sub, to_bytes, W
from docwow.writer.parts_writer import (
    build_content_types_xml,
    build_root_rels_xml,
    build_document_rels_xml,
    build_settings_xml,
)


def _parse(xml_bytes: bytes) -> etree._Element:
    return etree.fromstring(xml_bytes)


# ---------------------------------------------------------------------------
# Unit conversion helpers
# ---------------------------------------------------------------------------

class TestXmlHelpers:
    def test_wn_produces_clark_notation(self):
        from docwow.writer._xml import wn, W
        assert wn("body") == f"{{{W}}}body"

    def test_rn_produces_r_namespace(self):
        from docwow.writer._xml import rn, R
        assert rn("embed") == f"{{{R}}}embed"

    def test_sub_creates_child(self):
        from lxml import etree
        from docwow.writer._xml import sub, wn, W
        parent = etree.Element(wn("root"))
        child = sub(parent, "child", val="x")
        assert child.tag == wn("child")
        assert child.get(wn("val")) == "x"


class TestUnitConversions:
    def test_pt_tw_integer(self):
        assert pt_tw(36.0) == "720"

    def test_pt_tw_fractional(self):
        assert pt_tw(0.5) == "10"

    def test_pt_tw_zero(self):
        assert pt_tw(0.0) == "0"

    def test_pt_emu(self):
        assert pt_emu(72.0) == "914400"

    def test_pt_emu_fractional(self):
        # 1pt = 12700 EMU
        assert pt_emu(1.0) == "12700"

    def test_pt_hp(self):
        assert pt_hp(12.0) == "24"

    def test_pt_hp_fractional(self):
        assert pt_hp(10.5) == "21"


# ---------------------------------------------------------------------------
# Content Types
# ---------------------------------------------------------------------------

class TestBuildContentTypes:
    def test_returns_bytes(self):
        assert isinstance(build_content_types_xml([], False), bytes)

    def test_xml_declaration(self):
        xml = build_content_types_xml([], False).decode("utf-8")
        assert xml.startswith("<?xml")

    def test_document_override_present(self):
        xml = build_content_types_xml([], False).decode("utf-8")
        assert "wordprocessingml.document.main" in xml

    def test_styles_override_present(self):
        assert "wordprocessingml.styles" in build_content_types_xml([], False).decode()

    def test_settings_override_present(self):
        assert "wordprocessingml.settings" in build_content_types_xml([], False).decode()

    def test_numbering_absent_when_false(self):
        assert "numbering" not in build_content_types_xml([], False).decode()

    def test_numbering_present_when_true(self):
        assert "numbering" in build_content_types_xml([], True).decode()

    def test_image_entry_added(self):
        xml = build_content_types_xml([("/word/media/image1.png", "image/png")], False)
        assert "image1.png" in xml.decode()
        assert "image/png" in xml.decode()

    def test_multiple_images(self):
        entries = [
            ("/word/media/image1.png", "image/png"),
            ("/word/media/image2.jpg", "image/jpeg"),
        ]
        xml = build_content_types_xml(entries, False).decode()
        assert "image1.png" in xml
        assert "image2.jpg" in xml

    def test_rels_default_present(self):
        assert "relationships+xml" in build_content_types_xml([], False).decode()


# ---------------------------------------------------------------------------
# Root rels
# ---------------------------------------------------------------------------

class TestBuildRootRels:
    def test_returns_bytes(self):
        assert isinstance(build_root_rels_xml(), bytes)

    def test_contains_document_relationship(self):
        xml = build_root_rels_xml().decode()
        assert "officeDocument" in xml
        assert "word/document.xml" in xml

    def test_rid_is_rId1(self):
        assert 'Id="rId1"' in build_root_rels_xml().decode()


# ---------------------------------------------------------------------------
# Document rels
# ---------------------------------------------------------------------------

class TestBuildDocumentRels:
    def _entries(self):
        return [
            ("rId1", "http://example.com/image", "media/image1.png"),
            ("rId2", "http://example.com/styles", "styles.xml"),
        ]

    def test_returns_bytes(self):
        assert isinstance(build_document_rels_xml([]), bytes)

    def test_empty_has_no_relationships(self):
        root = _parse(build_document_rels_xml([]))
        assert len(root) == 0

    def test_entries_written(self):
        xml = build_document_rels_xml(self._entries()).decode()
        assert "rId1" in xml
        assert "rId2" in xml
        assert "media/image1.png" in xml
        assert "styles.xml" in xml

    def test_entry_count_matches(self):
        root = _parse(build_document_rels_xml(self._entries()))
        assert len(root) == 2


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestBuildSettings:
    def test_returns_bytes(self):
        assert isinstance(build_settings_xml(), bytes)

    def test_settings_root_element(self):
        root = _parse(build_settings_xml())
        assert "settings" in root.tag

    def test_default_tab_stop(self):
        assert "720" in build_settings_xml().decode()

    def test_compat_element_present(self):
        assert "compat" in build_settings_xml().decode()
