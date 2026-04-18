"""Tests for floating image (wp:anchor) support."""

from __future__ import annotations

import io
import zipfile

import docwow
from docwow.api.document import DocumentWrapper
from docwow.api.run import MutableFloatingImageRun
from docwow.models.image import FloatingImage


def _doc_xml(data: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.read("word/document.xml")


# Minimal 1×1 white PNG
_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _add_float(doc: DocumentWrapper, wrap: str = "square") -> MutableFloatingImageRun:
    para = doc.paragraphs.add_paragraph("anchor paragraph")
    return para.runs.add_floating_image(
        data=_PNG,
        content_type="image/png",
        width_pt=100.0,
        height_pt=80.0,
        pos_h_pt=36.0,
        pos_v_pt=72.0,
        h_anchor="column",
        v_anchor="paragraph",
        wrap=wrap,
    )


class TestFloatingImageModel:
    def test_properties(self):
        doc = DocumentWrapper()
        fi = _add_float(doc)
        assert fi.width_pt == 100.0
        assert fi.height_pt == 80.0
        assert fi.pos_h_pt == 36.0
        assert fi.pos_v_pt == 72.0
        assert fi.wrap == "square"
        assert fi.h_anchor == "column"
        assert fi.v_anchor == "paragraph"
        assert fi.behind_doc is False

    def test_set_wrap(self):
        doc = DocumentWrapper()
        fi = _add_float(doc)
        result = fi.set_wrap("topAndBottom")
        assert result is fi
        assert fi.wrap == "topAndBottom"

    def test_set_wrap_invalid(self):
        doc = DocumentWrapper()
        fi = _add_float(doc)
        import pytest
        with pytest.raises(ValueError):
            fi.set_wrap("bogus")

    def test_set_position_chainable(self):
        doc = DocumentWrapper()
        fi = _add_float(doc)
        result = fi.set_position(50.0, 100.0, h_anchor="margin", v_anchor="page")
        assert result is fi
        assert fi.pos_h_pt == 50.0
        assert fi.pos_v_pt == 100.0
        assert fi.h_anchor == "margin"
        assert fi.v_anchor == "page"

    def test_set_size_chainable(self):
        doc = DocumentWrapper()
        fi = _add_float(doc)
        result = fi.set_size(200.0, 150.0)
        assert result is fi
        assert fi.width_pt == 200.0
        assert fi.height_pt == 150.0


class TestFloatingImageDocxRoundTrip:
    def test_float_survives_docx_round_trip(self):
        doc = DocumentWrapper()
        _add_float(doc, wrap="square")

        data = doc.to_bytes()
        xml = _doc_xml(data)
        assert b"anchor" in xml
        assert b"wrapSquare" in xml

        doc2 = docwow.open(data)
        para = doc2.paragraphs[0]
        runs = list(para.runs)
        float_runs = [r for r in runs if isinstance(r, MutableFloatingImageRun)]
        assert len(float_runs) == 1

        fi = float_runs[0]
        assert abs(fi.width_pt - 100.0) < 1.0
        assert abs(fi.height_pt - 80.0) < 1.0
        assert fi.wrap == "square"
        assert fi.h_anchor == "column"
        assert fi.v_anchor == "paragraph"
        assert abs(fi.pos_h_pt - 36.0) < 1.0
        assert abs(fi.pos_v_pt - 72.0) < 1.0

    def test_wrap_none_survives_round_trip(self):
        doc = DocumentWrapper()
        _add_float(doc, wrap="none")
        data = doc.to_bytes()
        assert b"wrapNone" in _doc_xml(data)
        doc2 = docwow.open(data)
        fi = [r for r in doc2.paragraphs[0].runs if isinstance(r, MutableFloatingImageRun)][0]
        assert fi.wrap == "none"

    def test_wrap_topandbottom_survives_round_trip(self):
        doc = DocumentWrapper()
        _add_float(doc, wrap="topAndBottom")
        data = doc.to_bytes()
        assert b"wrapTopAndBottom" in _doc_xml(data)
        doc2 = docwow.open(data)
        fi = [r for r in doc2.paragraphs[0].runs if isinstance(r, MutableFloatingImageRun)][0]
        assert fi.wrap == "topAndBottom"

    def test_behind_doc_survives_round_trip(self):
        doc = DocumentWrapper()
        para = doc.paragraphs.add_paragraph("test")
        para.runs.add_floating_image(
            data=_PNG, content_type="image/png",
            width_pt=50.0, height_pt=50.0,
            behind_doc=True,
        )
        data = doc.to_bytes()
        assert b"behindDoc" in _doc_xml(data)
        doc2 = docwow.open(data)
        fi = [r for r in doc2.paragraphs[0].runs if isinstance(r, MutableFloatingImageRun)][0]
        assert fi.behind_doc is True

    def test_image_data_preserved(self):
        doc = DocumentWrapper()
        _add_float(doc)
        data = doc.to_bytes()
        doc2 = docwow.open(data)
        fi = [r for r in doc2.paragraphs[0].runs if isinstance(r, MutableFloatingImageRun)][0]
        assert fi.content_type == "image/png"
        assert len(fi.get_image().data) > 0


class TestFloatingImageHtmlRoundTrip:
    def test_renders_figure_element(self):
        doc = DocumentWrapper()
        _add_float(doc)
        html = doc.to_html()
        assert "dw-float-img" in html
        assert "data-dw-float-wrap" in html
        assert "<figure" in html

    def test_html_carries_position_metadata(self):
        doc = DocumentWrapper()
        _add_float(doc)
        html = doc.to_html()
        assert "data-dw-float-pos-h" in html
        assert "data-dw-float-pos-v" in html
        assert "data-dw-float-h-anchor" in html
        assert "data-dw-float-v-anchor" in html

    def test_float_survives_html_round_trip(self):
        doc = DocumentWrapper()
        _add_float(doc, wrap="topAndBottom")
        html = doc.to_html()
        data = docwow.to_docx(html)
        doc2 = docwow.open(data)
        float_runs = [r for r in doc2.paragraphs[0].runs if isinstance(r, MutableFloatingImageRun)]
        assert len(float_runs) == 1
        fi = float_runs[0]
        assert fi.wrap == "topAndBottom"
        assert abs(fi.width_pt - 100.0) < 1.0
