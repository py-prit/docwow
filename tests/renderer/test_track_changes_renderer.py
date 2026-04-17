"""Tests for track changes HTML rendering."""
from __future__ import annotations

from docwow.models.paragraph import Paragraph, TextRun, TrackedChange
from docwow.renderer.paragraph_renderer import render_paragraph


def _tc(change_type: str, text: str, author: str = "Alice", date: str = "2024-01-15T10:00:00Z", change_id: int = 1) -> TrackedChange:
    return TrackedChange(
        change_type=change_type,
        runs=(TextRun(text=text),),
        author=author,
        date=date,
        change_id=change_id,
    )


class TestRenderInsertion:
    def test_uses_ins_tag(self):
        html = render_paragraph(Paragraph(runs=(_tc("insert", "hello"),)))
        assert "<ins " in html
        assert "</ins>" in html

    def test_css_class(self):
        html = render_paragraph(Paragraph(runs=(_tc("insert", "hi"),)))
        assert 'class="dw-ins"' in html

    def test_text_content(self):
        html = render_paragraph(Paragraph(runs=(_tc("insert", "added text"),)))
        assert "added text" in html

    def test_author_attribute(self):
        html = render_paragraph(Paragraph(runs=(_tc("insert", "x", author="Bob"),)))
        assert 'data-dw-author="Bob"' in html

    def test_date_attribute(self):
        html = render_paragraph(Paragraph(runs=(_tc("insert", "x", date="2024-06-01T00:00:00Z"),)))
        assert 'data-dw-date="2024-06-01T00:00:00Z"' in html

    def test_change_id_attribute(self):
        html = render_paragraph(Paragraph(runs=(_tc("insert", "x", change_id=7),)))
        assert 'data-dw-change-id="7"' in html

    def test_author_html_escaped(self):
        html = render_paragraph(Paragraph(runs=(_tc("insert", "x", author='A & "B"'),)))
        assert 'A &amp; &quot;B&quot;' in html
        assert 'A & "B"' not in html


class TestRenderDeletion:
    def test_uses_del_tag(self):
        html = render_paragraph(Paragraph(runs=(_tc("delete", "bye"),)))
        assert "<del " in html
        assert "</del>" in html

    def test_css_class(self):
        html = render_paragraph(Paragraph(runs=(_tc("delete", "bye"),)))
        assert 'class="dw-del"' in html

    def test_text_content(self):
        html = render_paragraph(Paragraph(runs=(_tc("delete", "removed text"),)))
        assert "removed text" in html


class TestRenderMixed:
    def test_insert_and_delete_both_present(self):
        para = Paragraph(runs=(
            TextRun(text="before "),
            _tc("insert", "new"),
            TextRun(text=" "),
            _tc("delete", "old"),
        ))
        html = render_paragraph(para)
        assert "<ins " in html
        assert "<del " in html
        assert "new" in html
        assert "old" in html
        assert "before" in html

    def test_tracked_change_not_wrapped_in_dw_r(self):
        html = render_paragraph(Paragraph(runs=(_tc("insert", "x"),)))
        # The outer ins/del element must not itself have class dw-r
        assert '<ins class="dw-ins"' in html or 'class="dw-ins"' in html
        # The paragraph wrapper (dw-p) should not add dw-r around the ins
        import re
        # Check dw-r only appears inside the ins (on inner text run spans), not wrapping it
        assert not re.search(r'class="dw-r"[^>]*>\s*<ins', html)
