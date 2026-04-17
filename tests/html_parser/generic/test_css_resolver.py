"""Tests for the CSS cascade resolver."""
from __future__ import annotations

import pytest
import lxml.html

from docwow.html_parser.generic.css_resolver import CssResolver, parse_inline_style


def _el(html: str):
    return lxml.html.fragment_fromstring(html)


def _doc(html: str):
    return lxml.html.document_fromstring(html)


# ---------------------------------------------------------------------------
# parse_inline_style
# ---------------------------------------------------------------------------

class TestParseInlineStyle:
    def test_single_property(self):
        assert parse_inline_style("font-size: 14px") == {"font-size": "14px"}

    def test_multiple_properties(self):
        result = parse_inline_style("font-weight: bold; color: red")
        assert result == {"font-weight": "bold", "color": "red"}

    def test_strips_important(self):
        result = parse_inline_style("font-size: 14px !important")
        assert result["font-size"] == "14px"

    def test_empty_string(self):
        assert parse_inline_style("") == {}

    def test_trailing_semicolon(self):
        assert parse_inline_style("color: red;") == {"color": "red"}

    def test_property_names_lowercased(self):
        result = parse_inline_style("Font-Size: 14px")
        assert "font-size" in result

    def test_whitespace_stripped(self):
        result = parse_inline_style("  color :  red  ")
        assert result.get("color") == "red"


# ---------------------------------------------------------------------------
# CssResolver — basic rule parsing
# ---------------------------------------------------------------------------

class TestCssResolverBasic:
    def test_element_selector(self):
        resolver = CssResolver(["p { font-size: 14px; }"])
        el = _el("<p>text</p>")
        assert resolver.resolve(el).get("font-size") == "14px"

    def test_element_selector_no_match(self):
        resolver = CssResolver(["p { font-size: 14px; }"])
        el = _el("<div>text</div>")
        assert "font-size" not in resolver.resolve(el)

    def test_class_selector(self):
        resolver = CssResolver([".intro { color: red; }"])
        el = _el('<p class="intro">text</p>')
        assert resolver.resolve(el).get("color") == "red"

    def test_class_selector_no_match(self):
        resolver = CssResolver([".intro { color: red; }"])
        el = _el("<p>text</p>")
        assert "color" not in resolver.resolve(el)

    def test_id_selector(self):
        resolver = CssResolver(["#main { color: blue; }"])
        el = _el('<div id="main">text</div>')
        assert resolver.resolve(el).get("color") == "blue"

    def test_element_class_combined(self):
        resolver = CssResolver(["p.intro { font-weight: bold; }"])
        match = _el('<p class="intro">text</p>')
        no_match = _el('<div class="intro">text</div>')
        assert resolver.resolve(match).get("font-weight") == "bold"
        assert "font-weight" not in resolver.resolve(no_match)

    def test_multiple_selectors_comma(self):
        resolver = CssResolver(["h1, h2 { font-family: Arial; }"])
        h1 = _el("<h1>text</h1>")
        h2 = _el("<h2>text</h2>")
        p = _el("<p>text</p>")
        assert resolver.resolve(h1).get("font-family") == "Arial"
        assert resolver.resolve(h2).get("font-family") == "Arial"
        assert "font-family" not in resolver.resolve(p)

    def test_multiple_properties_in_rule(self):
        resolver = CssResolver(["p { font-size: 14px; color: red; font-weight: bold; }"])
        el = _el("<p>text</p>")
        props = resolver.resolve(el)
        assert props.get("font-size") == "14px"
        assert props.get("color") == "red"
        assert props.get("font-weight") == "bold"


# ---------------------------------------------------------------------------
# Specificity
# ---------------------------------------------------------------------------

class TestSpecificity:
    def test_class_overrides_element(self):
        resolver = CssResolver([
            "p { color: black; }",
            ".highlight { color: yellow; }",
        ])
        el = _el('<p class="highlight">text</p>')
        assert resolver.resolve(el).get("color") == "yellow"

    def test_id_overrides_class(self):
        resolver = CssResolver([
            ".intro { color: blue; }",
            "#special { color: green; }",
        ])
        el = _el('<p class="intro" id="special">text</p>')
        assert resolver.resolve(el).get("color") == "green"

    def test_source_order_breaks_ties(self):
        resolver = CssResolver([
            "p { color: red; }",
            "p { color: blue; }",
        ])
        el = _el("<p>text</p>")
        assert resolver.resolve(el).get("color") == "blue"

    def test_inline_overrides_stylesheet(self):
        resolver = CssResolver(["p { color: red; }"])
        el = _el('<p style="color: blue">text</p>')
        assert resolver.resolve(el).get("color") == "blue"


# ---------------------------------------------------------------------------
# !important
# ---------------------------------------------------------------------------

class TestImportant:
    def test_important_stylesheet_beats_normal_inline(self):
        resolver = CssResolver(["p { color: red !important; }"])
        el = _el('<p style="color: blue">text</p>')
        assert resolver.resolve(el).get("color") == "red"

    def test_important_inline_beats_important_stylesheet(self):
        resolver = CssResolver(["p { color: red !important; }"])
        el = _el('<p style="color: blue !important">text</p>')
        assert resolver.resolve(el).get("color") == "blue"

    def test_normal_stylesheet_loses_to_normal_inline(self):
        resolver = CssResolver(["p { color: red; }"])
        el = _el('<p style="color: blue">text</p>')
        assert resolver.resolve(el).get("color") == "blue"

    def test_important_does_not_affect_other_properties(self):
        resolver = CssResolver(["p { color: red !important; font-size: 14px; }"])
        el = _el('<p style="font-size: 16px">text</p>')
        props = resolver.resolve(el)
        assert props.get("color") == "red"
        assert props.get("font-size") == "16px"  # inline wins on non-important


# ---------------------------------------------------------------------------
# Descendant selectors
# ---------------------------------------------------------------------------

class TestDescendantSelectors:
    def test_descendant_match(self):
        resolver = CssResolver(["div p { color: red; }"])
        doc = lxml.html.document_fromstring("<div><p>text</p></div>")
        p = doc.find(".//p")
        assert resolver.resolve(p).get("color") == "red"

    def test_descendant_no_match_wrong_ancestor(self):
        resolver = CssResolver(["div p { color: red; }"])
        el = _el("<p>text</p>")
        assert "color" not in resolver.resolve(el)

    def test_deep_descendant(self):
        resolver = CssResolver(["div p { color: red; }"])
        doc = lxml.html.document_fromstring("<div><section><p>text</p></section></div>")
        p = doc.find(".//p")
        assert resolver.resolve(p).get("color") == "red"


# ---------------------------------------------------------------------------
# CSS comments and edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_css_comments_stripped(self):
        resolver = CssResolver(["/* comment */ p { color: red; } /* end */"])
        el = _el("<p>text</p>")
        assert resolver.resolve(el).get("color") == "red"

    def test_unsupported_selector_ignored(self):
        resolver = CssResolver(["p:hover { color: red; }"])
        el = _el("<p>text</p>")
        assert "color" not in resolver.resolve(el)

    def test_at_rules_ignored(self):
        resolver = CssResolver(["@media print { p { color: red; } } p { color: blue; }"])
        el = _el("<p>text</p>")
        assert resolver.resolve(el).get("color") == "blue"

    def test_empty_block(self):
        resolver = CssResolver(["p { }"])
        el = _el("<p>text</p>")
        assert resolver.resolve(el) == {}

    def test_multiple_classes_on_element(self):
        resolver = CssResolver([".a { color: red; } .b { font-weight: bold; }"])
        el = _el('<p class="a b">text</p>')
        props = resolver.resolve(el)
        assert props.get("color") == "red"
        assert props.get("font-weight") == "bold"

    def test_add_block_after_init(self):
        resolver = CssResolver()
        resolver.add_block("p { color: red; }")
        el = _el("<p>text</p>")
        assert resolver.resolve(el).get("color") == "red"

    def test_no_style_returns_empty(self):
        resolver = CssResolver()
        el = _el("<p>text</p>")
        assert resolver.resolve(el) == {}
