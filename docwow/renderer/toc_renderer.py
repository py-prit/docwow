"""Render a TableOfContents model to HTML."""

from __future__ import annotations

import html

from docwow.models.toc import TableOfContents


def render_toc(toc: TableOfContents) -> str:
    """Return a ``<nav class="dw-toc">`` HTML fragment for a :class:`TableOfContents`.

    The ``data-dw-toc-title`` attribute preserves the heading so the round-trip
    can reconstruct the original title.
    """
    title_escaped = html.escape(toc.title, quote=True)
    parts: list[str] = [
        f'<nav class="dw-toc" data-dw-toc="true" data-dw-toc-title="{title_escaped}">',
    ]

    if toc.title:
        parts.append(f'<p class="dw-toc-title">{html.escape(toc.title)}</p>')

    if toc.entries:
        parts.append('<ul class="dw-toc-list">')
        for entry in toc.entries:
            level = entry.level
            text_escaped = html.escape(entry.text)
            level_class = f"dw-toc-level-{level}"
            if entry.url:
                url_escaped = html.escape(entry.url, quote=True)
                inner = (
                    f'<a class="dw-toc-link" href="{url_escaped}">'
                    f"{text_escaped}</a>"
                )
            else:
                inner = f'<span class="dw-toc-text">{text_escaped}</span>'
            parts.append(
                f'<li class="dw-toc-entry {level_class}" '
                f'data-dw-toc-level="{level}">{inner}</li>'
            )
        parts.append("</ul>")

    parts.append("</nav>")
    return "\n".join(parts)
