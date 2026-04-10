"""Tests for docwow.models.image — InlineImage."""

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.image import InlineImage

PNG_HEADER = b"\x89PNG\r\n\x1a\n"
JPEG_HEADER = b"\xff\xd8\xff\xe0"


class TestInlineImageConstruction:
    def test_basic(self):
        img = InlineImage(
            relationship_id="rId1",
            content_type="image/png",
            data=PNG_HEADER,
            width_pt=100.0,
            height_pt=50.0,
        )
        assert img.relationship_id == "rId1"
        assert img.content_type == "image/png"
        assert img.data == PNG_HEADER
        assert img.width_pt == 100.0
        assert img.height_pt == 50.0

    def test_default_alt_text_is_empty_string(self):
        img = InlineImage(
            relationship_id="rId2",
            content_type="image/jpeg",
            data=JPEG_HEADER,
            width_pt=72.0,
            height_pt=72.0,
        )
        assert img.alt_text == ""

    def test_custom_alt_text(self):
        img = InlineImage(
            relationship_id="rId3",
            content_type="image/png",
            data=PNG_HEADER,
            width_pt=50.0,
            height_pt=25.0,
            alt_text="Company logo",
        )
        assert img.alt_text == "Company logo"

    def test_data_is_bytes(self):
        img = InlineImage(
            relationship_id="rId1",
            content_type="image/png",
            data=PNG_HEADER,
            width_pt=1.0,
            height_pt=1.0,
        )
        assert isinstance(img.data, bytes)

    def test_empty_bytes_data(self):
        # edge case: empty bytes (shouldn't be rejected at model level)
        img = InlineImage(
            relationship_id="rId1",
            content_type="image/png",
            data=b"",
            width_pt=1.0,
            height_pt=1.0,
        )
        assert img.data == b""

    def test_large_dimensions(self):
        img = InlineImage(
            relationship_id="rId1",
            content_type="image/png",
            data=PNG_HEADER,
            width_pt=595.28,
            height_pt=841.89,
        )
        assert img.width_pt == pytest.approx(595.28)
        assert img.height_pt == pytest.approx(841.89)

    def test_fractional_dimensions(self):
        # sub-point precision is valid (EMU→pt conversion yields floats)
        img = InlineImage(
            relationship_id="rId1",
            content_type="image/png",
            data=PNG_HEADER,
            width_pt=72.567,
            height_pt=36.123,
        )
        assert img.width_pt == pytest.approx(72.567)
        assert img.height_pt == pytest.approx(36.123)


@pytest.mark.parametrize("content_type", [
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/tiff",
])
class TestInlineImageContentTypes:
    def test_content_type_stored(self, content_type):
        img = InlineImage(
            relationship_id="rId1",
            content_type=content_type,
            data=b"\x00",
            width_pt=10.0,
            height_pt=10.0,
        )
        assert img.content_type == content_type


class TestInlineImageImmutability:
    def test_cannot_set_relationship_id(self, sample_image):
        with pytest.raises(FrozenInstanceError):
            sample_image.relationship_id = "rId99"  # type: ignore[misc]

    def test_cannot_set_data(self, sample_image):
        with pytest.raises(FrozenInstanceError):
            sample_image.data = b"new data"  # type: ignore[misc]

    def test_cannot_set_width(self, sample_image):
        with pytest.raises(FrozenInstanceError):
            sample_image.width_pt = 999.0  # type: ignore[misc]

    def test_cannot_set_alt_text(self, sample_image):
        with pytest.raises(FrozenInstanceError):
            sample_image.alt_text = "new"  # type: ignore[misc]


class TestInlineImageEquality:
    def test_equal(self):
        kwargs = dict(
            relationship_id="rId1",
            content_type="image/png",
            data=PNG_HEADER,
            width_pt=100.0,
            height_pt=50.0,
        )
        assert InlineImage(**kwargs) == InlineImage(**kwargs)

    def test_not_equal_different_rid(self):
        base = dict(content_type="image/png", data=PNG_HEADER, width_pt=100.0, height_pt=50.0)
        assert InlineImage(relationship_id="rId1", **base) != InlineImage(relationship_id="rId2", **base)

    def test_not_equal_different_data(self):
        base = dict(relationship_id="rId1", content_type="image/png", width_pt=100.0, height_pt=50.0)
        assert InlineImage(data=PNG_HEADER, **base) != InlineImage(data=JPEG_HEADER, **base)


class TestInlineImageHashable:
    def test_can_be_used_in_set(self, sample_image):
        s = {sample_image, sample_image}
        assert len(s) == 1
