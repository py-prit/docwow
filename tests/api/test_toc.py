"""Tests for MutableTableOfContents and MutableTocEntry API."""
from __future__ import annotations

import pytest

from docwow.api.toc import MutableTableOfContents, MutableTocEntry
from docwow.models.toc import TableOfContents, TocEntry


class TestMutableTocEntry:
    def test_default_values(self):
        e = MutableTocEntry()
        assert e.text == ""
        assert e.url == ""
        assert e.level == 1

    def test_custom_values(self):
        e = MutableTocEntry(text="Intro", url="#_Toc1", level=2)
        assert e.text == "Intro"
        assert e.url == "#_Toc1"
        assert e.level == 2

    def test_set_text(self):
        e = MutableTocEntry()
        result = e.set_text("Hello")
        assert e.text == "Hello"
        assert result is e  # chainable

    def test_set_url(self):
        e = MutableTocEntry()
        result = e.set_url("#anchor")
        assert e.url == "#anchor"
        assert result is e

    def test_set_level(self):
        e = MutableTocEntry()
        result = e.set_level(3)
        assert e.level == 3
        assert result is e

    def test_set_level_invalid(self):
        e = MutableTocEntry()
        with pytest.raises(ValueError):
            e.set_level(0)
        with pytest.raises(ValueError):
            e.set_level(10)

    def test_to_frozen(self):
        e = MutableTocEntry(text="Intro", url="#_Toc1", level=2)
        frozen = e._to_frozen()
        assert isinstance(frozen, TocEntry)
        assert frozen.text == "Intro"
        assert frozen.url == "#_Toc1"
        assert frozen.level == 2


class TestMutableTableOfContents:
    def test_default_title(self):
        toc = MutableTableOfContents()
        assert toc.title == "Contents"

    def test_custom_title(self):
        toc = MutableTableOfContents(title="Table of Contents")
        assert toc.title == "Table of Contents"

    def test_set_title_chainable(self):
        toc = MutableTableOfContents()
        result = toc.set_title("My TOC")
        assert toc.title == "My TOC"
        assert result is toc

    def test_empty_entries(self):
        toc = MutableTableOfContents()
        assert toc.entries == []

    def test_add_entry(self):
        toc = MutableTableOfContents()
        entry = toc.add_entry("Introduction", url="#_Toc1", level=1)
        assert len(toc.entries) == 1
        assert entry is toc.entries[0]
        assert entry.text == "Introduction"

    def test_add_entry_defaults(self):
        toc = MutableTableOfContents()
        entry = toc.add_entry("x")
        assert entry.url == ""
        assert entry.level == 1

    def test_add_multiple_entries(self):
        toc = MutableTableOfContents()
        toc.add_entry("Ch 1", "#_Toc1", 1)
        toc.add_entry("Sec 1.1", "#_Toc2", 2)
        assert len(toc.entries) == 2

    def test_to_frozen(self):
        toc = MutableTableOfContents(title="TOC")
        toc.add_entry("Intro", "#_Toc1", 1)
        frozen = toc._to_frozen()
        assert isinstance(frozen, TableOfContents)
        assert frozen.title == "TOC"
        assert len(frozen.entries) == 1
        assert frozen.entries[0].text == "Intro"

    def test_to_frozen_empty_entries(self):
        toc = MutableTableOfContents()
        frozen = toc._to_frozen()
        assert frozen.entries == ()


class TestParagraphCollectionAddToc:
    def test_add_toc(self):
        from docwow.api.paragraph import ParagraphCollection
        coll = ParagraphCollection()
        toc = coll.add_toc("My TOC")
        assert isinstance(toc, MutableTableOfContents)
        assert toc.title == "My TOC"
        assert len(coll) == 1

    def test_add_toc_default_title(self):
        from docwow.api.paragraph import ParagraphCollection
        coll = ParagraphCollection()
        toc = coll.add_toc()
        assert toc.title == "Contents"

    def test_toc_in_frozen_body(self):
        from docwow.api.paragraph import ParagraphCollection
        from docwow.models.toc import TableOfContents
        coll = ParagraphCollection()
        coll.add_toc("TOC")
        body = coll._to_frozen_body()
        assert len(body) == 1
        assert isinstance(body[0], TableOfContents)

    def test_type_check_accepts_toc(self):
        from docwow.api.paragraph import ParagraphCollection
        coll = ParagraphCollection()
        toc = MutableTableOfContents()
        # Should not raise
        coll.append(toc)
        assert len(coll) == 1

    def test_type_check_rejects_unknown(self):
        from docwow.api.paragraph import ParagraphCollection
        coll = ParagraphCollection()
        with pytest.raises(TypeError):
            coll.append("not a valid item")  # type: ignore[arg-type]
