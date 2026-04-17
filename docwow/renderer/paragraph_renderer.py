"""Render Paragraph and Run objects to HTML."""

from __future__ import annotations

import html

from docwow.models.comment import Comment
from docwow.models.paragraph import BookmarkStart, CommentRef, FootnoteRef, Hyperlink, ImageRun, PageNumberField, Paragraph, Run, TextRun, TrackedChange
from docwow.models.styles import ParagraphFormatting, RunFormatting
from docwow.renderer.image_renderer import render_image
from docwow.utils.units import pt_to_css


def render_paragraph(
    p: Paragraph,
    extra_classes: list[str] | None = None,
    comments: dict[int, Comment] | None = None,
) -> str:
    """Return a <p> HTML element for a paragraph."""
    fmt = p.formatting
    classes = ["dw-p"]
    if fmt.style_id:
        classes.append(f"dw-style-{_css_ident(fmt.style_id)}")
    if extra_classes:
        classes.extend(extra_classes)

    data_attrs = _para_data_attrs(fmt)
    if p.list_info is not None:
        data_attrs["data-dw-num-id"] = p.list_info.num_id
        data_attrs["data-dw-level"] = str(p.list_info.level)

    inline_style = _para_inline_style(fmt)
    inner = "".join(_render_run(r, comments=comments) for r in p.runs)

    return _tag("p", classes, data_attrs, inline_style, inner)


def _render_run(run: Run, comments: dict[int, Comment] | None = None) -> str:
    if isinstance(run, ImageRun):
        return render_image(run.image)
    if isinstance(run, Hyperlink):
        return _render_hyperlink(run)
    if isinstance(run, PageNumberField):
        return _render_page_number_field(run)
    if isinstance(run, FootnoteRef):
        return _render_footnote_ref(run)
    if isinstance(run, BookmarkStart):
        return _render_bookmark(run)
    if isinstance(run, CommentRef):
        comment = comments.get(run.comment_id) if comments else None
        return _render_comment_ref(run, comment)
    if isinstance(run, TrackedChange):
        return _render_tracked_change(run)
    return _render_text_run(run)


def _render_footnote_ref(ref: FootnoteRef) -> str:
    """Render a footnote/endnote reference as a superscript anchor."""
    css_class = "dw-footnote-ref" if ref.note_type == "footnote" else "dw-endnote-ref"
    anchor = f"fn-{ref.note_id}" if ref.note_type == "footnote" else f"en-{ref.note_id}"
    return (
        f'<a href="#{anchor}" class="{css_class}" '
        f'data-dw-note-type="{ref.note_type}" '
        f'data-dw-note-id="{ref.note_id}">'
        f"[{ref.note_id}]</a>"
    )


def _render_page_number_field(field: PageNumberField) -> str:
    inline_style = _run_inline_style(field.formatting)
    style_attr = f' style="{inline_style}"' if inline_style else ""
    placeholder = "1"  # visual placeholder in HTML
    return (
        f'<span class="dw-field" data-dw-field="{field.field_type}"{style_attr}>'
        f"{placeholder}</span>"
    )


def _render_comment_ref(ref: CommentRef, comment: Comment | None = None) -> str:
    """Render a comment reference as a superscript anchor with a hover popup."""
    popup = ""
    if comment is not None:
        author = html.escape(comment.author)
        date = html.escape(comment.date)
        text = html.escape(_comment_text(comment))
        date_part = f' <span class="dw-comment-popup-date">· {date}</span>' if date else ""
        popup = (
            f'<span class="dw-comment-popup">'
            f'<span class="dw-comment-popup-author">{author}{date_part}</span>'
            f'<span class="dw-comment-popup-text">{text}</span>'
            f"</span>"
        )
    return (
        f'<a href="#comment-{ref.comment_id}" class="dw-comment-ref" '
        f'data-dw-comment-id="{ref.comment_id}">'
        f"[{ref.comment_id}]{popup}</a>"
    )


def _render_tracked_change(tc: TrackedChange) -> str:
    """Render a tracked change as an HTML <ins> or <del> element with a
    hover popup showing author, date, and Accept / Reject buttons."""
    tag = "ins" if tc.change_type == "insert" else "del"
    css_class = "dw-ins" if tc.change_type == "insert" else "dw-del"
    label = "Inserted" if tc.change_type == "insert" else "Deleted"
    author_attr = html.escape(tc.author, quote=True)
    author_display = html.escape(tc.author)
    date_attr = html.escape(tc.date, quote=True)
    # Show only the date part of the ISO timestamp (e.g. "2025-07-10")
    date_display = html.escape(tc.date[:10]) if tc.date else ""
    inner = "".join(
        _render_text_run(r) if isinstance(r, TextRun) else render_image(r.image)
        for r in tc.runs
    )
    popup = (
        '<span class="dw-tc-popup">'
        f'<span class="dw-tc-popup-label">{label}</span>'
        f'<span class="dw-tc-popup-meta">{author_display}'
        + (f' \u00b7 {date_display}' if date_display else '')
        + '</span>'
        '<span class="dw-tc-popup-actions">'
        '<button class="dw-tc-accept" onclick="dwTcAccept(this)">&#10003; Accept</button>'
        '<button class="dw-tc-reject" onclick="dwTcReject(this)">&#10007; Reject</button>'
        '</span>'
        '</span>'
    )
    return (
        f'<{tag} class="{css_class}"'
        f' data-dw-author="{author_attr}"'
        f' data-dw-date="{date_attr}"'
        f' data-dw-change-id="{tc.change_id}">'
        f"{popup}{inner}</{tag}>"
    )


def _comment_text(comment: Comment) -> str:
    """Extract plain text from all paragraphs of a comment."""
    parts: list[str] = []
    for para in comment.paragraphs:
        for run in para.runs:
            if isinstance(run, TextRun):
                parts.append(run.text)
    return " ".join(parts)


def _render_bookmark(start: BookmarkStart) -> str:
    name = html.escape(start.name, quote=True)
    return f'<a id="{name}" class="dw-bookmark" data-dw-bookmark="{name}"></a>'


def _render_hyperlink(link: Hyperlink) -> str:
    inner = "".join(_render_text_run(r) for r in link.runs)
    url = html.escape(link.url, quote=True)
    return f'<a href="{url}" class="dw-hyperlink" data-dw-href="{url}">{inner}</a>'


def _render_text_run(run: TextRun) -> str:
    fmt = run.formatting
    classes = ["dw-r"]
    data_attrs = _run_data_attrs(fmt)
    inline_style = _run_inline_style(fmt)
    inner = _escape_text(run.text)
    return _tag("span", classes, data_attrs, inline_style, inner)


# ---------------------------------------------------------------------------
# Attribute builders
# ---------------------------------------------------------------------------

def _para_data_attrs(fmt: ParagraphFormatting) -> dict[str, str]:
    attrs: dict[str, str] = {}
    if fmt.style_id:
        attrs["data-dw-style"] = fmt.style_id
    if fmt.alignment:
        attrs["data-dw-alignment"] = fmt.alignment
    if fmt.indent_left_pt:
        attrs["data-dw-indent-left"] = pt_to_css(fmt.indent_left_pt)
    if fmt.indent_right_pt:
        attrs["data-dw-indent-right"] = pt_to_css(fmt.indent_right_pt)
    if fmt.indent_first_line_pt:
        attrs["data-dw-indent-first-line"] = pt_to_css(fmt.indent_first_line_pt)
    if fmt.space_before_pt:
        attrs["data-dw-space-before"] = pt_to_css(fmt.space_before_pt)
    if fmt.space_after_pt:
        attrs["data-dw-space-after"] = pt_to_css(fmt.space_after_pt)
    if fmt.line_spacing_pt is not None:
        attrs["data-dw-line-spacing"] = pt_to_css(fmt.line_spacing_pt)
    if fmt.keep_together:
        attrs["data-dw-keep-together"] = "true"
    if fmt.keep_with_next:
        attrs["data-dw-keep-with-next"] = "true"
    if fmt.page_break_before:
        attrs["data-dw-page-break-before"] = "true"
    return attrs


def _run_data_attrs(fmt: RunFormatting) -> dict[str, str]:
    attrs: dict[str, str] = {}
    if fmt.bold:
        attrs["data-dw-bold"] = "true"
    if fmt.italic:
        attrs["data-dw-italic"] = "true"
    if fmt.underline:
        attrs["data-dw-underline"] = "true"
    if fmt.strike:
        attrs["data-dw-strike"] = "true"
    if fmt.font_name:
        attrs["data-dw-font-name"] = fmt.font_name
    if fmt.font_size_pt is not None:
        attrs["data-dw-font-size"] = pt_to_css(fmt.font_size_pt)
    if fmt.color:
        attrs["data-dw-color"] = fmt.color
    if fmt.highlight:
        attrs["data-dw-highlight"] = fmt.highlight
    if fmt.vertical_align:
        attrs["data-dw-vertical-align"] = fmt.vertical_align
    return attrs


# ---------------------------------------------------------------------------
# Inline style builders
# ---------------------------------------------------------------------------

def _para_inline_style(fmt: ParagraphFormatting) -> str:
    rules: list[str] = []
    if fmt.alignment:
        rules.append(f"text-align:{fmt.alignment}")
    if fmt.indent_left_pt:
        rules.append(f"padding-left:{pt_to_css(fmt.indent_left_pt)}")
    if fmt.indent_right_pt:
        rules.append(f"padding-right:{pt_to_css(fmt.indent_right_pt)}")
    if fmt.indent_first_line_pt > 0:
        rules.append(f"text-indent:{pt_to_css(fmt.indent_first_line_pt)}")
    if fmt.space_before_pt:
        rules.append(f"margin-top:{pt_to_css(fmt.space_before_pt)}")
    if fmt.space_after_pt:
        rules.append(f"margin-bottom:{pt_to_css(fmt.space_after_pt)}")
    if fmt.line_spacing_pt is not None:
        rules.append(f"line-height:{pt_to_css(fmt.line_spacing_pt)}")
    return ";".join(rules)


def _run_inline_style(fmt: RunFormatting) -> str:
    rules: list[str] = []
    if fmt.bold:
        rules.append("font-weight:bold")
    if fmt.italic:
        rules.append("font-style:italic")
    decorations: list[str] = []
    if fmt.underline:
        decorations.append("underline")
    if fmt.strike:
        decorations.append("line-through")
    if decorations:
        rules.append(f"text-decoration:{' '.join(decorations)}")
    if fmt.font_name:
        rules.append(f"font-family:{fmt.font_name}")
    if fmt.font_size_pt is not None:
        rules.append(f"font-size:{pt_to_css(fmt.font_size_pt)}")
    if fmt.color:
        rules.append(f"color:#{fmt.color}")
    if fmt.highlight:
        rules.append(f"background-color:{_highlight_to_css(fmt.highlight)}")
    if fmt.vertical_align == "superscript":
        rules.append("vertical-align:super;font-size:smaller")
    elif fmt.vertical_align == "subscript":
        rules.append("vertical-align:sub;font-size:smaller")
    return ";".join(rules)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tag(
    tag_name: str,
    classes: list[str],
    data_attrs: dict[str, str],
    inline_style: str,
    inner: str,
) -> str:
    parts = [f'class="{" ".join(classes)}"']
    if inline_style:
        parts.append(f'style="{inline_style}"')
    for k, v in data_attrs.items():
        parts.append(f'{k}="{html.escape(v, quote=True)}"')
    attrs_str = " ".join(parts)
    return f"<{tag_name} {attrs_str}>{inner}</{tag_name}>"


def _css_ident(style_id: str) -> str:
    """Convert a Word style ID to a safe CSS class name component."""
    return style_id.replace(" ", "-")


def _escape_text(text: str) -> str:
    """Escape text for HTML, preserving line breaks as <br>."""
    escaped = html.escape(text)
    return escaped.replace("\n", "<br>")


_HIGHLIGHT_COLOURS: dict[str, str] = {
    "black":     "#000000",
    "blue":      "#0000FF",
    "cyan":      "#00FFFF",
    "darkBlue":  "#000080",
    "darkCyan":  "#008080",
    "darkGray":  "#808080",
    "darkGreen": "#008000",
    "darkMagenta": "#800080",
    "darkRed":   "#800000",
    "darkYellow": "#808000",
    "green":     "#00FF00",
    "lightGray": "#C0C0C0",
    "magenta":   "#FF00FF",
    "none":      "transparent",
    "red":       "#FF0000",
    "white":     "#FFFFFF",
    "yellow":    "#FFFF00",
}


def _highlight_to_css(highlight: str) -> str:
    return _HIGHLIGHT_COLOURS.get(highlight, "yellow")
