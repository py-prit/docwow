"""Tests for MutableRun, MutableImageRun, MutableHyperlink, and RunCollection."""
from __future__ import annotations

import pytest

from docwow.api.run import MutableHyperlink, MutableImageRun, MutableRun, RunCollection
from docwow.models.image import InlineImage
from docwow.models.paragraph import Hyperlink, ImageRun, TextRun


# ---------------------------------------------------------------------------
# MutableRun
# ---------------------------------------------------------------------------

class TestMutableRunConstruction:
    def test_defaults(self):
        run = MutableRun()
        assert run.get_text() == ""
        assert run.bold is False
        assert run.italic is False
        assert run.underline is False
        assert run.strike is False
        assert run.font_name is None
        assert run.font_size is None
        assert run.color is None
        assert run.highlight is None
        assert run.vertical_align is None

    def test_custom_text(self):
        run = MutableRun("hello")
        assert run.get_text() == "hello"

    def test_custom_formatting(self):
        run = MutableRun("x", bold=True, italic=True, font_size=12.0, color="FF0000")
        assert run.bold is True
        assert run.italic is True
        assert run.font_size == 12.0
        assert run.color == "FF0000"


class TestMutableRunSetters:
    def test_set_text(self):
        run = MutableRun("old")
        result = run.set_text("new")
        assert run.get_text() == "new"
        assert result is run  # chaining

    def test_set_bold(self):
        run = MutableRun()
        run.set_bold(True)
        assert run.bold is True
        run.set_bold(False)
        assert run.bold is False

    def test_set_italic(self):
        run = MutableRun()
        run.set_italic()
        assert run.italic is True

    def test_set_underline(self):
        run = MutableRun()
        run.set_underline()
        assert run.underline is True

    def test_set_strike(self):
        run = MutableRun()
        run.set_strike()
        assert run.strike is True

    def test_set_font_name(self):
        run = MutableRun()
        run.set_font_name("Arial")
        assert run.font_name == "Arial"
        run.set_font_name(None)
        assert run.font_name is None

    def test_set_font_size(self):
        run = MutableRun()
        run.set_font_size(14.0)
        assert run.font_size == 14.0

    def test_set_color(self):
        run = MutableRun()
        run.set_color("0000FF")
        assert run.color == "0000FF"

    def test_set_highlight(self):
        run = MutableRun()
        run.set_highlight("yellow")
        assert run.highlight == "yellow"

    def test_set_vertical_align_superscript(self):
        run = MutableRun()
        run.set_vertical_align("superscript")
        assert run.vertical_align == "superscript"

    def test_set_vertical_align_subscript(self):
        run = MutableRun()
        run.set_vertical_align("subscript")
        assert run.vertical_align == "subscript"

    def test_set_vertical_align_none(self):
        run = MutableRun()
        run.set_vertical_align("superscript")
        run.set_vertical_align(None)
        assert run.vertical_align is None

    def test_set_vertical_align_invalid(self):
        run = MutableRun()
        with pytest.raises(ValueError, match="vertical_align"):
            run.set_vertical_align("top")

    def test_chaining(self):
        run = MutableRun()
        result = run.set_text("hi").set_bold().set_italic().set_font_size(12.0)
        assert result is run
        assert run.get_text() == "hi"
        assert run.bold is True
        assert run.italic is True
        assert run.font_size == 12.0


class TestMutableRunToFrozen:
    def test_produces_text_run(self):
        run = MutableRun("hello", bold=True, italic=True)
        frozen = run._to_frozen()
        assert isinstance(frozen, TextRun)
        assert frozen.text == "hello"
        assert frozen.formatting.bold is True
        assert frozen.formatting.italic is True

    def test_all_formatting_fields(self):
        run = MutableRun(
            "x",
            bold=True,
            italic=True,
            underline=True,
            strike=True,
            font_name="Times",
            font_size=10.0,
            color="FF0000",
            highlight="yellow",
            vertical_align="superscript",
        )
        frozen = run._to_frozen()
        fmt = frozen.formatting
        assert fmt.bold is True
        assert fmt.italic is True
        assert fmt.underline is True
        assert fmt.strike is True
        assert fmt.font_name == "Times"
        assert fmt.font_size_pt == 10.0
        assert fmt.color == "FF0000"
        assert fmt.highlight == "yellow"
        assert fmt.vertical_align == "superscript"

    def test_frozen_is_immutable(self):
        run = MutableRun("hi")
        frozen = run._to_frozen()
        with pytest.raises(Exception):
            frozen.text = "changed"  # type: ignore[misc]

    def test_repr(self):
        run = MutableRun("hello", bold=True)
        r = repr(run)
        assert "hello" in r
        assert "bold" in r


# ---------------------------------------------------------------------------
# MutableImageRun
# ---------------------------------------------------------------------------

class TestMutableImageRun:
    def test_construction(self, inline_image):
        img_run = MutableImageRun(inline_image)
        assert img_run.width_pt == 100.0
        assert img_run.height_pt == 80.0
        assert img_run.alt_text == "test image"
        assert img_run.content_type == "image/png"

    def test_get_image(self, inline_image):
        img_run = MutableImageRun(inline_image)
        assert img_run.get_image() is inline_image

    def test_replace_image(self, inline_image, png_bytes):
        img_run = MutableImageRun(inline_image)
        result = img_run.replace_image(
            data=png_bytes,
            content_type="image/jpeg",
            width_pt=200.0,
            height_pt=150.0,
            alt_text="new image",
        )
        assert result is img_run
        assert img_run.content_type == "image/jpeg"
        assert img_run.width_pt == 200.0
        assert img_run.height_pt == 150.0
        assert img_run.alt_text == "new image"

    def test_replace_image_preserves_dimensions_when_not_given(self, inline_image, png_bytes):
        img_run = MutableImageRun(inline_image)
        img_run.replace_image(data=png_bytes, content_type="image/png")
        assert img_run.width_pt == 100.0
        assert img_run.height_pt == 80.0

    def test_replace_image_generates_unique_rid(self, inline_image, png_bytes):
        img_run1 = MutableImageRun(inline_image)
        img_run2 = MutableImageRun(inline_image)
        img_run1.replace_image(png_bytes, "image/png")
        img_run2.replace_image(png_bytes, "image/png")
        assert img_run1.get_image().relationship_id != img_run2.get_image().relationship_id

    def test_to_frozen(self, inline_image):
        img_run = MutableImageRun(inline_image)
        frozen = img_run._to_frozen()
        assert isinstance(frozen, ImageRun)
        assert frozen.image is inline_image

    def test_repr(self, inline_image):
        img_run = MutableImageRun(inline_image)
        assert "image/png" in repr(img_run)


# ---------------------------------------------------------------------------
# RunCollection
# ---------------------------------------------------------------------------

class TestRunCollection:
    def test_empty(self):
        rc = RunCollection()
        assert len(rc) == 0

    def test_append_and_len(self):
        rc = RunCollection()
        rc.append(MutableRun("a"))
        rc.append(MutableRun("b"))
        assert len(rc) == 2

    def test_getitem(self):
        rc = RunCollection()
        run = MutableRun("hello")
        rc.append(run)
        assert rc[0] is run

    def test_iter(self):
        rc = RunCollection()
        r1 = MutableRun("a")
        r2 = MutableRun("b")
        rc.append(r1)
        rc.append(r2)
        assert list(rc) == [r1, r2]

    def test_insert(self):
        rc = RunCollection()
        r1 = MutableRun("a")
        r2 = MutableRun("b")
        rc.append(r1)
        rc.insert(0, r2)
        assert rc[0] is r2
        assert rc[1] is r1

    def test_remove(self):
        rc = RunCollection()
        rc.append(MutableRun("a"))
        rc.append(MutableRun("b"))
        rc.remove(0)
        assert len(rc) == 1
        assert rc[0].get_text() == "b"

    def test_clear(self):
        rc = RunCollection()
        rc.append(MutableRun("a"))
        rc.clear()
        assert len(rc) == 0

    def test_add_text_returns_mutable_run(self):
        rc = RunCollection()
        run = rc.add_text("hello", bold=True)
        assert isinstance(run, MutableRun)
        assert run.get_text() == "hello"
        assert run.bold is True
        assert rc[0] is run

    def test_add_text_all_kwargs(self):
        rc = RunCollection()
        run = rc.add_text(
            "x",
            bold=True,
            italic=True,
            underline=True,
            strike=True,
            font_name="Arial",
            font_size=12.0,
            color="FF0000",
            highlight="yellow",
            vertical_align="superscript",
        )
        assert run.bold is True
        assert run.font_name == "Arial"
        assert run.vertical_align == "superscript"

    def test_append_image_run(self, inline_image):
        rc = RunCollection()
        img_run = MutableImageRun(inline_image)
        rc.append(img_run)
        assert rc[0] is img_run


class TestRunCollectionTypeEnforcement:
    def test_rejects_frozen_text_run(self):
        rc = RunCollection()
        with pytest.raises(TypeError, match="frozen TextRun"):
            rc.append(TextRun("hi"))

    def test_rejects_frozen_image_run(self, inline_image):
        rc = RunCollection()
        with pytest.raises(TypeError, match="frozen ImageRun"):
            rc.append(ImageRun(inline_image))

    def test_rejects_string(self):
        rc = RunCollection()
        with pytest.raises(TypeError, match="MutableRun"):
            rc.append("hello")  # type: ignore[arg-type]

    def test_rejects_on_insert(self):
        rc = RunCollection()
        with pytest.raises(TypeError):
            rc.insert(0, TextRun("hi"))


class TestRunCollectionToFrozen:
    def test_empty(self):
        rc = RunCollection()
        assert rc._to_frozen() == ()

    def test_text_runs(self):
        rc = RunCollection()
        rc.add_text("hello")
        rc.add_text("world", bold=True)
        frozen = rc._to_frozen()
        assert len(frozen) == 2
        assert isinstance(frozen[0], TextRun)
        assert frozen[0].text == "hello"
        assert frozen[1].formatting.bold is True

    def test_mixed_runs(self, inline_image):
        rc = RunCollection()
        rc.add_text("before")
        rc.append(MutableImageRun(inline_image))
        rc.add_text("after")
        frozen = rc._to_frozen()
        assert isinstance(frozen[0], TextRun)
        assert isinstance(frozen[1], ImageRun)
        assert isinstance(frozen[2], TextRun)

    def test_repr(self):
        rc = RunCollection()
        rc.add_text("a")
        assert "1 run" in repr(rc)


# ---------------------------------------------------------------------------
# MutableHyperlink
# ---------------------------------------------------------------------------

class TestMutableHyperlinkConstruction:
    def test_defaults(self):
        link = MutableHyperlink()
        assert link.get_text() == ""
        assert link.url == ""

    def test_custom_text_and_url(self):
        link = MutableHyperlink(text="Click here", url="https://example.com")
        assert link.get_text() == "Click here"
        assert link.url == "https://example.com"

    def test_mailto_url(self):
        link = MutableHyperlink(text="email", url="mailto:hi@example.com")
        assert link.url == "mailto:hi@example.com"


class TestMutableHyperlinkSetters:
    def test_set_text(self):
        link = MutableHyperlink()
        result = link.set_text("new text")
        assert link.get_text() == "new text"
        assert result is link  # chaining

    def test_set_url(self):
        link = MutableHyperlink()
        result = link.set_url("https://example.com")
        assert link.url == "https://example.com"
        assert result is link  # chaining

    def test_chaining(self):
        link = MutableHyperlink()
        link.set_text("Link").set_url("https://example.com")
        assert link.get_text() == "Link"
        assert link.url == "https://example.com"


class TestMutableHyperlinkToFrozen:
    def test_produces_hyperlink(self):
        link = MutableHyperlink(text="Click", url="https://example.com")
        frozen = link._to_frozen()
        assert isinstance(frozen, Hyperlink)
        assert frozen.url == "https://example.com"
        assert frozen.runs[0].text == "Click"

    def test_empty_text_produces_empty_runs(self):
        link = MutableHyperlink(text="", url="https://example.com")
        frozen = link._to_frozen()
        assert isinstance(frozen, Hyperlink)
        assert len(frozen.runs) == 0

    def test_frozen_runs_are_text_runs(self):
        link = MutableHyperlink(text="Hello", url="https://example.com")
        frozen = link._to_frozen()
        assert isinstance(frozen.runs[0], TextRun)

    def test_frozen_is_immutable(self):
        link = MutableHyperlink(text="x", url="https://example.com")
        frozen = link._to_frozen()
        with pytest.raises(Exception):
            frozen.url = "https://other.com"  # type: ignore[misc]


class TestRunCollectionHyperlink:
    def test_append_hyperlink(self):
        rc = RunCollection()
        link = MutableHyperlink(text="click", url="https://example.com")
        rc.append(link)
        assert rc[0] is link
        assert len(rc) == 1

    def test_add_hyperlink_factory(self):
        rc = RunCollection()
        link = rc.add_hyperlink(text="click", url="https://example.com")
        assert isinstance(link, MutableHyperlink)
        assert link.get_text() == "click"
        assert link.url == "https://example.com"
        assert rc[0] is link

    def test_to_frozen_includes_hyperlink(self):
        rc = RunCollection()
        rc.add_hyperlink("Click", "https://example.com")
        frozen = rc._to_frozen()
        assert len(frozen) == 1
        assert isinstance(frozen[0], Hyperlink)
        assert frozen[0].url == "https://example.com"

    def test_mixed_runs_with_hyperlink(self):
        rc = RunCollection()
        rc.add_text("See ")
        rc.add_hyperlink("this", "https://example.com")
        rc.add_text(" for details")
        frozen = rc._to_frozen()
        assert isinstance(frozen[0], TextRun)
        assert isinstance(frozen[1], Hyperlink)
        assert isinstance(frozen[2], TextRun)

    def test_rejects_frozen_hyperlink(self):
        rc = RunCollection()
        frozen = Hyperlink(url="https://example.com", runs=(TextRun(text="x"),))
        with pytest.raises(TypeError, match="frozen Hyperlink"):
            rc.append(frozen)  # type: ignore[arg-type]
