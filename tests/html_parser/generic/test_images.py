"""Tests for generic HTML image parsing (<img>, data URIs, fetch_images)."""
from __future__ import annotations

import base64
import io
import warnings

import pytest

from docwow.html_parser.generic.html_parser import parse_foreign_html
from docwow.models.paragraph import ImageRun, Paragraph, TextRun

# 80×40 red PNG encoded as base64
_PNG_80x40_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAFAAAAAoCAIAAADmAupWAAAAWElEQVR4nOXOMQEAMAyAMIZ/YZU1"
    "F+1BFOQNLRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIjMRIj"
    "MRIjMRIjMRIjMV4Htn10bQEY2dy1lAAAAABJRU5ErkJggg=="
)
_PNG_DATA_URI = f"data:image/png;base64,{_PNG_80x40_B64}"


def _parse(html: str):
    return parse_foreign_html(html)


def _img_runs(html: str) -> list[ImageRun]:
    doc = _parse(html)
    runs: list[ImageRun] = []
    for el in doc.body:
        if isinstance(el, Paragraph):
            runs.extend(r for r in el.runs if isinstance(r, ImageRun))
    return runs


# ---------------------------------------------------------------------------
# data: URI parsing
# ---------------------------------------------------------------------------

class TestDataUri:
    def test_inline_img_produces_image_run(self):
        runs = _img_runs(f'<p><img src="{_PNG_DATA_URI}" alt="test"></p>')
        assert len(runs) == 1

    def test_content_type_from_data_uri(self):
        runs = _img_runs(f'<p><img src="{_PNG_DATA_URI}"></p>')
        assert runs[0].image.content_type == "image/png"

    def test_data_decoded(self):
        runs = _img_runs(f'<p><img src="{_PNG_DATA_URI}"></p>')
        assert len(runs[0].image.data) > 0

    def test_alt_text_captured(self):
        runs = _img_runs(f'<p><img src="{_PNG_DATA_URI}" alt="red square"></p>')
        assert runs[0].image.alt_text == "red square"

    def test_natural_size_from_pillow(self):
        # No explicit width/height → Pillow reads 80×40 px → 60pt × 30pt
        runs = _img_runs(f'<p><img src="{_PNG_DATA_URI}"></p>')
        assert runs[0].image.width_pt == pytest.approx(60.0)
        assert runs[0].image.height_pt == pytest.approx(30.0)

    def test_explicit_width_overrides_natural(self):
        runs = _img_runs(f'<p><img src="{_PNG_DATA_URI}" width="120"></p>')
        # 120 px = 90 pt; height scales proportionally (30 / 60 * 90 = 45)
        assert runs[0].image.width_pt == pytest.approx(90.0)
        assert runs[0].image.height_pt == pytest.approx(45.0)

    def test_explicit_height_scales_width(self):
        runs = _img_runs(f'<p><img src="{_PNG_DATA_URI}" height="20"></p>')
        # 20 px = 15 pt; width scales (60 / 30 * 15 = 30)
        assert runs[0].image.height_pt == pytest.approx(15.0)
        assert runs[0].image.width_pt == pytest.approx(30.0)

    def test_both_width_and_height_explicit(self):
        runs = _img_runs(f'<p><img src="{_PNG_DATA_URI}" width="200" height="100"></p>')
        assert runs[0].image.width_pt == pytest.approx(150.0)
        assert runs[0].image.height_pt == pytest.approx(75.0)

    def test_css_width_takes_priority_over_attribute(self):
        runs = _img_runs(
            f'<p><img src="{_PNG_DATA_URI}" width="80"'
            f' style="width: 100pt; height: 50pt"></p>'
        )
        assert runs[0].image.width_pt == pytest.approx(100.0)
        assert runs[0].image.height_pt == pytest.approx(50.0)

    def test_unique_relationship_ids(self):
        html = (
            f'<p><img src="{_PNG_DATA_URI}"></p>'
            f'<p><img src="{_PNG_DATA_URI}"></p>'
        )
        runs = _img_runs(html)
        assert len(runs) == 2
        assert runs[0].image.relationship_id != runs[1].image.relationship_id

    def test_malformed_data_uri_skipped(self):
        # URI with no comma (missing base64 payload section) → skipped
        runs = _img_runs('<p><img src="data:image/png;base64"></p>')
        assert len(runs) == 0

    def test_block_level_img_produces_paragraph(self):
        doc = _parse(f'<img src="{_PNG_DATA_URI}" alt="standalone">')
        paras = [el for el in doc.body if isinstance(el, Paragraph)]
        assert any(
            any(isinstance(r, ImageRun) for r in p.runs) for p in paras
        )

    def test_inline_img_surrounded_by_text(self):
        doc = _parse(f'<p>Before <img src="{_PNG_DATA_URI}"> after</p>')
        para = next(el for el in doc.body if isinstance(el, Paragraph))
        types = [type(r).__name__ for r in para.runs]
        assert "TextRun" in types
        assert "ImageRun" in types


# ---------------------------------------------------------------------------
# Remote URLs — fetch_images=False (default)
# ---------------------------------------------------------------------------

class TestRemoteSkip:
    def test_remote_url_skipped_without_flag(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            runs = _img_runs('<p><img src="https://example.com/pic.png"></p>')
        assert len(runs) == 0
        assert any("fetch_images" in str(x.message) for x in w)

    def test_relative_url_skipped(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            runs = _img_runs('<p><img src="images/photo.jpg"></p>')
        assert len(runs) == 0


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_docx_roundtrip_data_uri(self):
        import docwow
        html = (
            f'<h1>Image test</h1>'
            f'<p>Inline image: <img src="{_PNG_DATA_URI}" alt="test png" width="80" height="40"> done.</p>'
        )
        docx_bytes = docwow.to_docx(html, is_foreign_html=True)
        assert len(docx_bytes) > 0

        doc = docwow.open(docx_bytes)
        from docwow.api import MutableParagraph
        from docwow.api.run import MutableImageRun
        img_runs = []
        for p in doc.paragraphs:
            if isinstance(p, MutableParagraph):
                img_runs.extend(r for r in p.runs if isinstance(r, MutableImageRun))
        assert len(img_runs) == 1
        assert img_runs[0].get_image().content_type == "image/png"

    def test_multiple_images_in_document(self):
        import docwow
        html = (
            f'<p><img src="{_PNG_DATA_URI}" width="40" height="20"></p>'
            f'<p><img src="{_PNG_DATA_URI}" width="80" height="40"></p>'
        )
        docx_bytes = docwow.to_docx(html, is_foreign_html=True)
        assert len(docx_bytes) > 0
