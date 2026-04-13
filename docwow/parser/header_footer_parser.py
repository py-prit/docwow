"""Parse word/header*.xml and word/footer*.xml into HeaderFooter models."""
from __future__ import annotations

import zipfile

from lxml import etree

from docwow.models.header_footer import HeaderFooter
from docwow.utils.xml_utils import parse_xml, qn


def parse_header_footer(
    xml_bytes: bytes,
    zf: zipfile.ZipFile,
    relationships: dict[str, str],
) -> HeaderFooter:
    """Parse a header or footer XML part and return a HeaderFooter.

    The XML root is either ``<w:hdr>`` or ``<w:ftr>``; both have the same
    paragraph/run structure as ``<w:body>``.
    """
    # Import here to avoid a circular import (body_parser → header_footer_parser)
    from docwow.parser.body_parser import _parse_paragraph

    root = parse_xml(xml_bytes)
    paragraphs = []
    for child in root:
        if child.tag == qn("w:p"):
            paragraphs.append(_parse_paragraph(child, zf, relationships, {}))
    return HeaderFooter(paragraphs=tuple(paragraphs))
