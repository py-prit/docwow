"""Parse a ``<nav class="dw-toc">`` element back into a :class:`TableOfContents`."""

from __future__ import annotations

from docwow.html_parser._utils import has_class
from docwow.models.toc import TableOfContents, TocEntry


def parse_toc(nav_el) -> TableOfContents:
    """Convert a ``<nav class="dw-toc">`` lxml element into a :class:`TableOfContents`.

    Reads the ``data-dw-toc-title`` attribute for the heading text, then
    iterates ``<li class="dw-toc-entry">`` children for entries.
    """
    title = nav_el.get("data-dw-toc-title", "")

    entries: list[TocEntry] = []
    ul = nav_el.find(".//ul[@class]")
    if ul is None:
        # Try without class restriction
        ul = nav_el.find("ul")

    if ul is not None:
        for li in ul:
            if li.tag != "li" or not has_class(li, "dw-toc-entry"):
                continue
            level_str = li.get("data-dw-toc-level", "1")
            try:
                level = int(level_str)
            except ValueError:
                level = 1

            # Entry text and URL come from <a class="dw-toc-link"> or
            # <span class="dw-toc-text"> inside the <li>
            text = ""
            url = ""
            for child in li:
                if child.tag == "a" and has_class(child, "dw-toc-link"):
                    text = child.text_content() if hasattr(child, "text_content") else (child.text or "")
                    url = child.get("href", "")
                    break
                elif child.tag == "span" and has_class(child, "dw-toc-text"):
                    text = child.text_content() if hasattr(child, "text_content") else (child.text or "")
                    break

            entries.append(TocEntry(text=text, url=url, level=level))

    return TableOfContents(title=title, entries=tuple(entries))
