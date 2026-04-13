"""Shared fixtures for api layer tests."""
from __future__ import annotations

import pytest

from docwow.api.document import DocumentWrapper
from docwow.api.paragraph import MutableParagraph, ParagraphCollection
from docwow.api.run import MutableImageRun, MutableRun, RunCollection
from docwow.models.image import InlineImage
from docwow.models.styles import ParagraphFormatting, RunFormatting

# Minimal valid PNG bytes (1x1 pixel)
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
    b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture()
def empty_doc():
    return DocumentWrapper()


@pytest.fixture()
def simple_doc():
    doc = DocumentWrapper()
    doc.paragraphs.add_paragraph("Hello world")
    return doc


@pytest.fixture()
def mutable_run():
    return MutableRun("test text", bold=True)


@pytest.fixture()
def mutable_para():
    para = MutableParagraph()
    para.runs.add_text("Hello")
    para.runs.add_text(" world", bold=True)
    return para


@pytest.fixture()
def png_bytes():
    return PNG_BYTES


@pytest.fixture()
def inline_image():
    return InlineImage(
        relationship_id="rId1",
        content_type="image/png",
        data=PNG_BYTES,
        width_pt=100.0,
        height_pt=80.0,
        alt_text="test image",
    )
