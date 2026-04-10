"""Tests for MutableImage."""
from __future__ import annotations

import pytest

from docwow.api.image import MutableImage
from docwow.api.paragraph import MutableParagraph
from docwow.models.paragraph import ImageRun, Paragraph


class TestMutableImage:
    def test_inherits_mutable_paragraph(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        assert isinstance(img, MutableParagraph)

    def test_construction(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0, alt_text="test")
        assert img.width_pt == 100.0
        assert img.height_pt == 80.0
        assert img.alt_text == "test"
        assert img.content_type == "image/png"

    def test_single_run(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        assert len(img.runs) == 1

    def test_replace(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        new_bytes = b"fake jpeg"
        result = img.replace(new_bytes, "image/jpeg", width_pt=200.0, height_pt=150.0)
        assert result is img
        assert img.content_type == "image/jpeg"
        assert img.width_pt == 200.0
        assert img.height_pt == 150.0

    def test_replace_preserves_dimensions(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        img.replace(b"new data", "image/png")
        assert img.width_pt == 100.0
        assert img.height_pt == 80.0


class TestMutableImageToFrozen:
    def test_produces_paragraph(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        frozen = img._to_frozen()
        assert isinstance(frozen, Paragraph)

    def test_contains_image_run(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        frozen = img._to_frozen()
        assert len(frozen.runs) == 1
        assert isinstance(frozen.runs[0], ImageRun)

    def test_image_data_preserved(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        frozen = img._to_frozen()
        assert frozen.runs[0].image.data == png_bytes
        assert frozen.runs[0].image.width_pt == 100.0

    def test_repr(self, png_bytes):
        img = MutableImage(png_bytes, "image/png", 100.0, 80.0)
        assert "MutableImage" in repr(img)
        assert "image/png" in repr(img)
