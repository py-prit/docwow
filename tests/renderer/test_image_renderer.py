"""Tests for docwow.renderer.image_renderer."""
import base64
import pytest
from docwow.models.image import InlineImage
from docwow.renderer.image_renderer import render_image, _escape_attr

PNG = b"\x89PNG\r\n\x1a\n"
JPEG = b"\xff\xd8\xff\xe0"


def _img(data=PNG, width=100.0, height=50.0, alt="", rid="rId1", ct="image/png"):
    return InlineImage(
        relationship_id=rid, content_type=ct, data=data,
        width_pt=width, height_pt=height, alt_text=alt,
    )


class TestRenderImage:
    def test_produces_img_tag(self):
        assert render_image(_img()).startswith("<img ")

    def test_self_closing_no_slash(self):
        # HTML5 void elements don't need /
        html = render_image(_img())
        assert html.endswith(">")
        assert "</img>" not in html

    def test_contains_base64_data_uri(self):
        img = _img(data=PNG, ct="image/png")
        html = render_image(img)
        expected_b64 = base64.b64encode(PNG).decode()
        assert f"data:image/png;base64,{expected_b64}" in html

    def test_src_attribute_present(self):
        html = render_image(_img())
        assert 'src="data:image/png;base64,' in html

    def test_dw_class(self):
        assert 'class="dw-img"' in render_image(_img())

    def test_width_in_style(self):
        html = render_image(_img(width=72.0))
        assert "width:72pt" in html

    def test_height_in_style(self):
        html = render_image(_img(height=36.0))
        assert "height:36pt" in html

    def test_data_dw_width_attribute(self):
        html = render_image(_img(width=100.0))
        assert 'data-dw-width="100pt"' in html

    def test_data_dw_height_attribute(self):
        html = render_image(_img(height=50.0))
        assert 'data-dw-height="50pt"' in html

    def test_data_dw_rid_attribute(self):
        html = render_image(_img(rid="rId5"))
        assert 'data-dw-rid="rId5"' in html

    def test_alt_attribute_empty(self):
        html = render_image(_img(alt=""))
        assert 'alt=""' in html

    def test_alt_attribute_set(self):
        html = render_image(_img(alt="Company logo"))
        assert 'alt="Company logo"' in html

    def test_alt_attribute_escapes_quotes(self):
        html = render_image(_img(alt='Say "hello"'))
        assert '&quot;' in html

    def test_jpeg_content_type(self):
        img = _img(data=JPEG, ct="image/jpeg")
        assert "data:image/jpeg;base64," in render_image(img)

    def test_fractional_dimensions(self):
        html = render_image(_img(width=72.567, height=36.123))
        assert "72.57pt" in html  # rounded to 2dp

    def test_vertical_align_middle_in_style(self):
        assert "vertical-align:middle" in render_image(_img())


class TestEscapeAttr:
    def test_plain_text(self):
        assert _escape_attr("hello") == "hello"

    def test_ampersand(self):
        assert _escape_attr("a&b") == "a&amp;b"

    def test_double_quote(self):
        assert _escape_attr('"hi"') == "&quot;hi&quot;"

    def test_less_than(self):
        assert _escape_attr("<tag>") == "&lt;tag&gt;"

    def test_empty_string(self):
        assert _escape_attr("") == ""
