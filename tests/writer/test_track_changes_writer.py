"""Tests for track changes DOCX writing."""
from __future__ import annotations

from lxml import etree

from docwow.models.document import Document
from docwow.models.paragraph import Paragraph, TextRun, TrackedChange
from docwow.writer.document_writer import build_document_xml

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _build(para: Paragraph) -> etree._Element:
    doc = Document(body=(para,), styles=(), numbering=())
    xml_bytes = build_document_xml(doc, image_rids={})
    return etree.fromstring(xml_bytes)


def _find_all(root, local_tag: str) -> list:
    return root.findall(f".//{{{W}}}{local_tag}")


class TestWriteInsertion:
    def test_ins_element_present(self):
        tc = TrackedChange(
            change_type="insert",
            runs=(TextRun(text="added"),),
            author="Alice",
            date="2024-01-15T10:00:00Z",
            change_id=1,
        )
        root = _build(Paragraph(runs=(tc,)))
        ins_els = _find_all(root, "ins")
        assert len(ins_els) == 1

    def test_ins_author_attribute(self):
        tc = TrackedChange(change_type="insert", runs=(TextRun(text="x"),), author="Bob", date="", change_id=2)
        root = _build(Paragraph(runs=(tc,)))
        ins = _find_all(root, "ins")[0]
        assert ins.get(f"{{{W}}}author") == "Bob"

    def test_ins_date_attribute(self):
        tc = TrackedChange(change_type="insert", runs=(TextRun(text="x"),), author="", date="2024-06-01T00:00:00Z", change_id=3)
        root = _build(Paragraph(runs=(tc,)))
        ins = _find_all(root, "ins")[0]
        assert ins.get(f"{{{W}}}date") == "2024-06-01T00:00:00Z"

    def test_ins_text_in_w_t(self):
        tc = TrackedChange(change_type="insert", runs=(TextRun(text="hello"),), author="", date="", change_id=1)
        root = _build(Paragraph(runs=(tc,)))
        t_els = _find_all(root, "t")
        assert any(t.text == "hello" for t in t_els)

    def test_ins_no_del_text(self):
        tc = TrackedChange(change_type="insert", runs=(TextRun(text="x"),), author="", date="", change_id=1)
        root = _build(Paragraph(runs=(tc,)))
        assert _find_all(root, "delText") == []


class TestWriteDeletion:
    def test_del_element_present(self):
        tc = TrackedChange(
            change_type="delete",
            runs=(TextRun(text="removed"),),
            author="Carol",
            date="2024-02-01T08:00:00Z",
            change_id=5,
        )
        root = _build(Paragraph(runs=(tc,)))
        del_els = _find_all(root, "del")
        assert len(del_els) == 1

    def test_del_author_attribute(self):
        tc = TrackedChange(change_type="delete", runs=(TextRun(text="x"),), author="Dave", date="", change_id=6)
        root = _build(Paragraph(runs=(tc,)))
        del_el = _find_all(root, "del")[0]
        assert del_el.get(f"{{{W}}}author") == "Dave"

    def test_del_text_in_del_text_element(self):
        tc = TrackedChange(change_type="delete", runs=(TextRun(text="gone"),), author="", date="", change_id=1)
        root = _build(Paragraph(runs=(tc,)))
        dt_els = _find_all(root, "delText")
        assert any(dt.text == "gone" for dt in dt_els)

    def test_del_no_w_t(self):
        tc = TrackedChange(change_type="delete", runs=(TextRun(text="x"),), author="", date="", change_id=1)
        root = _build(Paragraph(runs=(tc,)))
        # w:t elements only appear for regular runs, not deletions
        t_els = _find_all(root, "t")
        assert all(t.text != "x" for t in t_els)
