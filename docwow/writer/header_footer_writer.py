"""Build word/header*.xml and word/footer*.xml parts."""
from __future__ import annotations

from lxml import etree

from docwow.models.header_footer import HeaderFooter
from docwow.models.paragraph import Paragraph
from docwow.writer._xml import W, DOC_NSMAP, sub, to_bytes


_CT_HEADER = "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"
_CT_FOOTER = "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"


def build_header_xml(hf: HeaderFooter, image_rids: dict, hyperlink_rids: dict) -> bytes:
    """Build a word/header*.xml part."""
    return _build_hf_xml("hdr", hf, image_rids, hyperlink_rids)


def build_footer_xml(hf: HeaderFooter, image_rids: dict, hyperlink_rids: dict) -> bytes:
    """Build a word/footer*.xml part."""
    return _build_hf_xml("ftr", hf, image_rids, hyperlink_rids)


def _build_hf_xml(
    root_tag: str,
    hf: HeaderFooter,
    image_rids: dict,
    hyperlink_rids: dict,
) -> bytes:
    root = etree.Element(f"{{{W}}}{root_tag}", nsmap=DOC_NSMAP)

    # Import here to avoid circular dependency
    from docwow.writer.document_writer import _write_paragraph

    draw_counter = [0]
    if hf.paragraphs:
        for para in hf.paragraphs:
            _write_paragraph(root, para, image_rids, draw_counter, hyperlink_rids)
    else:
        # Every header/footer must have at least one paragraph
        p_el = etree.SubElement(root, f"{{{W}}}p")
        etree.SubElement(p_el, f"{{{W}}}pPr")

    return to_bytes(root)
