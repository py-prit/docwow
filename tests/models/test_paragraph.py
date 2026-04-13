"""Tests for docwow.models.paragraph — TextRun, ImageRun, Run, Paragraph."""

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.image import InlineImage
from docwow.models.lists import ListInfo
from docwow.models.paragraph import Hyperlink, ImageRun, Paragraph, TextRun
from docwow.models.styles import ParagraphFormatting, RunFormatting

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# TextRun
# ---------------------------------------------------------------------------

class TestTextRunConstruction:
    def test_text_stored(self):
        run = TextRun(text="Hello")
        assert run.text == "Hello"

    def test_empty_string(self):
        run = TextRun(text="")
        assert run.text == ""

    def test_unicode_text(self):
        run = TextRun(text="こんにちは 🌍")
        assert run.text == "こんにちは 🌍"

    def test_whitespace_text(self):
        run = TextRun(text="   ")
        assert run.text == "   "

    def test_newline_in_text(self):
        # soft line breaks (\n within a run) are valid
        run = TextRun(text="line one\nline two")
        assert run.text == "line one\nline two"

    def test_default_formatting_is_run_formatting(self):
        run = TextRun(text="x")
        assert isinstance(run.formatting, RunFormatting)

    def test_default_formatting_is_all_defaults(self):
        run = TextRun(text="x")
        assert run.formatting == RunFormatting()

    def test_custom_formatting(self):
        fmt = RunFormatting(bold=True, font_size_pt=14.0)
        run = TextRun(text="Bold", formatting=fmt)
        assert run.formatting.bold is True
        assert run.formatting.font_size_pt == 14.0

    def test_each_instance_gets_independent_default_formatting(self):
        r1 = TextRun(text="a")
        r2 = TextRun(text="b")
        # Both are equal (both defaults) but are distinct objects
        assert r1.formatting == r2.formatting
        assert r1.formatting is not r2.formatting


class TestTextRunImmutability:
    def test_cannot_set_text(self):
        run = TextRun(text="Hello")
        with pytest.raises(FrozenInstanceError):
            run.text = "World"  # type: ignore[misc]

    def test_cannot_set_formatting(self):
        run = TextRun(text="Hello")
        with pytest.raises(FrozenInstanceError):
            run.formatting = RunFormatting(bold=True)  # type: ignore[misc]


class TestTextRunEquality:
    def test_equal(self):
        assert TextRun(text="Hi") == TextRun(text="Hi")

    def test_not_equal_different_text(self):
        assert TextRun(text="Hi") != TextRun(text="Bye")

    def test_not_equal_different_formatting(self):
        assert TextRun(text="Hi") != TextRun(text="Hi", formatting=RunFormatting(bold=True))


class TestTextRunHashable:
    def test_can_be_in_set(self):
        r = TextRun(text="x")
        s = {r, TextRun(text="x"), TextRun(text="y")}
        assert len(s) == 2


# ---------------------------------------------------------------------------
# ImageRun
# ---------------------------------------------------------------------------

@pytest.fixture
def png_image():
    return InlineImage(
        relationship_id="rId5",
        content_type="image/png",
        data=PNG_HEADER,
        width_pt=72.0,
        height_pt=72.0,
    )


class TestImageRunConstruction:
    def test_image_stored(self, png_image):
        run = ImageRun(image=png_image)
        assert run.image == png_image

    def test_default_formatting(self, png_image):
        run = ImageRun(image=png_image)
        assert run.formatting == RunFormatting()

    def test_custom_formatting(self, png_image):
        fmt = RunFormatting(vertical_align="superscript")
        run = ImageRun(image=png_image, formatting=fmt)
        assert run.formatting.vertical_align == "superscript"


class TestImageRunImmutability:
    def test_cannot_set_image(self, png_image):
        run = ImageRun(image=png_image)
        with pytest.raises(FrozenInstanceError):
            run.image = png_image  # type: ignore[misc]

    def test_cannot_set_formatting(self, png_image):
        run = ImageRun(image=png_image)
        with pytest.raises(FrozenInstanceError):
            run.formatting = RunFormatting()  # type: ignore[misc]


class TestImageRunEquality:
    def test_equal(self, png_image):
        assert ImageRun(image=png_image) == ImageRun(image=png_image)

    def test_not_equal_different_image(self):
        img1 = InlineImage(relationship_id="rId1", content_type="image/png",
                           data=PNG_HEADER, width_pt=10.0, height_pt=10.0)
        img2 = InlineImage(relationship_id="rId2", content_type="image/png",
                           data=PNG_HEADER, width_pt=10.0, height_pt=10.0)
        assert ImageRun(image=img1) != ImageRun(image=img2)


# ---------------------------------------------------------------------------
# Paragraph
# ---------------------------------------------------------------------------

class TestParagraphConstruction:
    def test_empty_runs(self):
        p = Paragraph(runs=())
        assert p.runs == ()

    def test_single_text_run(self, sample_text_run):
        p = Paragraph(runs=(sample_text_run,))
        assert len(p.runs) == 1
        assert p.runs[0] == sample_text_run

    def test_multiple_text_runs(self):
        r1 = TextRun(text="Hello, ")
        r2 = TextRun(text="World")
        p = Paragraph(runs=(r1, r2))
        assert len(p.runs) == 2
        assert p.runs[0].text == "Hello, "
        assert p.runs[1].text == "World"

    def test_mixed_runs(self, sample_text_run, sample_image_run):
        p = Paragraph(runs=(sample_text_run, sample_image_run))
        assert isinstance(p.runs[0], TextRun)
        assert isinstance(p.runs[1], ImageRun)

    def test_image_only_paragraph(self, sample_image_run):
        p = Paragraph(runs=(sample_image_run,))
        assert isinstance(p.runs[0], ImageRun)

    def test_default_formatting(self):
        p = Paragraph(runs=())
        assert isinstance(p.formatting, ParagraphFormatting)
        assert p.formatting == ParagraphFormatting()

    def test_custom_formatting(self):
        fmt = ParagraphFormatting(alignment="center", space_after_pt=12.0)
        p = Paragraph(runs=(), formatting=fmt)
        assert p.formatting.alignment == "center"
        assert p.formatting.space_after_pt == 12.0

    def test_default_list_info_is_none(self):
        p = Paragraph(runs=())
        assert p.list_info is None

    def test_with_list_info(self, sample_list_info):
        p = Paragraph(runs=(), list_info=sample_list_info)
        assert p.list_info == sample_list_info
        assert p.list_info.num_id == "1"
        assert p.list_info.level == 0

    def test_each_instance_gets_independent_default_formatting(self):
        p1 = Paragraph(runs=())
        p2 = Paragraph(runs=())
        assert p1.formatting == p2.formatting
        assert p1.formatting is not p2.formatting


class TestParagraphImmutability:
    def test_cannot_set_runs(self, sample_paragraph):
        with pytest.raises(FrozenInstanceError):
            sample_paragraph.runs = ()  # type: ignore[misc]

    def test_cannot_set_formatting(self, sample_paragraph):
        with pytest.raises(FrozenInstanceError):
            sample_paragraph.formatting = ParagraphFormatting()  # type: ignore[misc]

    def test_cannot_set_list_info(self, sample_paragraph):
        with pytest.raises(FrozenInstanceError):
            sample_paragraph.list_info = ListInfo(num_id="1", level=0)  # type: ignore[misc]


class TestParagraphEquality:
    def test_equal_empty(self):
        assert Paragraph(runs=()) == Paragraph(runs=())

    def test_equal_with_runs(self):
        r = TextRun(text="Hi")
        assert Paragraph(runs=(r,)) == Paragraph(runs=(r,))

    def test_not_equal_different_runs(self):
        p1 = Paragraph(runs=(TextRun(text="A"),))
        p2 = Paragraph(runs=(TextRun(text="B"),))
        assert p1 != p2

    def test_not_equal_different_formatting(self):
        p1 = Paragraph(runs=())
        p2 = Paragraph(runs=(), formatting=ParagraphFormatting(alignment="center"))
        assert p1 != p2


class TestParagraphHashable:
    def test_can_be_used_in_set(self, sample_paragraph):
        s = {sample_paragraph, sample_paragraph}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# Hyperlink
# ---------------------------------------------------------------------------

class TestHyperlinkConstruction:
    def test_url_and_runs_stored(self):
        run = TextRun(text="Click here")
        link = Hyperlink(url="https://example.com", runs=(run,))
        assert link.url == "https://example.com"
        assert len(link.runs) == 1
        assert link.runs[0].text == "Click here"

    def test_empty_runs(self):
        link = Hyperlink(url="https://example.com", runs=())
        assert link.runs == ()

    def test_multiple_runs(self):
        runs = (TextRun(text="Hello "), TextRun(text="world"))
        link = Hyperlink(url="https://example.com", runs=runs)
        assert len(link.runs) == 2

    def test_mailto_url(self):
        link = Hyperlink(url="mailto:test@example.com", runs=(TextRun(text="email"),))
        assert link.url == "mailto:test@example.com"

    def test_anchor_url(self):
        link = Hyperlink(url="#section1", runs=(TextRun(text="jump"),))
        assert link.url == "#section1"


class TestHyperlinkImmutability:
    def test_cannot_set_url(self):
        link = Hyperlink(url="https://example.com", runs=())
        with pytest.raises(FrozenInstanceError):
            link.url = "https://other.com"  # type: ignore[misc]

    def test_cannot_set_runs(self):
        link = Hyperlink(url="https://example.com", runs=())
        with pytest.raises(FrozenInstanceError):
            link.runs = ()  # type: ignore[misc]


class TestHyperlinkEquality:
    def test_equal(self):
        run = TextRun(text="x")
        a = Hyperlink(url="https://example.com", runs=(run,))
        b = Hyperlink(url="https://example.com", runs=(run,))
        assert a == b

    def test_not_equal_different_url(self):
        run = TextRun(text="x")
        a = Hyperlink(url="https://a.com", runs=(run,))
        b = Hyperlink(url="https://b.com", runs=(run,))
        assert a != b

    def test_not_equal_different_runs(self):
        a = Hyperlink(url="https://example.com", runs=(TextRun(text="a"),))
        b = Hyperlink(url="https://example.com", runs=(TextRun(text="b"),))
        assert a != b


class TestHyperlinkInParagraph:
    def test_paragraph_accepts_hyperlink_as_run(self):
        link = Hyperlink(url="https://example.com", runs=(TextRun(text="link"),))
        para = Paragraph(runs=(link,))
        assert len(para.runs) == 1
        assert isinstance(para.runs[0], Hyperlink)

    def test_paragraph_with_mixed_runs_and_hyperlink(self):
        text_run = TextRun(text="See ")
        link = Hyperlink(url="https://example.com", runs=(TextRun(text="this"),))
        para = Paragraph(runs=(text_run, link))
        assert len(para.runs) == 2


# ---------------------------------------------------------------------------
# Run type alias
# ---------------------------------------------------------------------------

class TestRunTypeAlias:
    def test_text_run_is_valid_run(self, sample_text_run):
        assert isinstance(sample_text_run, (TextRun, ImageRun))

    def test_image_run_is_valid_run(self, sample_image_run):
        assert isinstance(sample_image_run, (TextRun, ImageRun))

    def test_text_run_is_not_image_run(self, sample_text_run):
        assert not isinstance(sample_text_run, ImageRun)

    def test_image_run_is_not_text_run(self, sample_image_run):
        assert not isinstance(sample_image_run, TextRun)
