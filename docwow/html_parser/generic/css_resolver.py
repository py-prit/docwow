"""CSS cascade resolver for generic HTML → DOCX conversion.

Parses ``<style>`` blocks and inline ``style=""`` attributes, then resolves
the CSS cascade for any element in the DOM, returning a flat dict of
CSS property → raw value string.

Supported selectors:
  element         p { }
  class           .intro { }
  id              #main { }
  element.class   p.intro { }
  descendant      div p { }
  multiple        h1, h2 { }

Unsupported (silently ignored):
  pseudo-classes  p:first-child { }
  pseudo-elements p::before { }
  attribute       [type="text"] { }
  complex         div > p, p + span, p ~ span

Specificity: ID (100) > class (10) > element (1).
!important overrides specificity ordering.
Inline style always wins (treated as specificity 1000) unless a stylesheet
rule also has !important on the same property (in which case specificity
ordering among !important rules applies).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class _Rule:
    """A single parsed CSS rule."""
    selector: str
    properties: dict[str, str]          # property → value (raw, stripped)
    important: set[str]                 # properties marked !important
    specificity: int                    # numeric specificity score
    order: int                          # source order for stable sort


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class CssResolver:
    """Parses CSS style blocks and resolves cascade for DOM elements.

    Usage::

        resolver = CssResolver(style_blocks=["p { font-size: 14px; }"])
        props = resolver.resolve(lxml_element)
        # props == {"font-size": "14px"}
    """

    def __init__(self, style_blocks: list[str] | None = None) -> None:
        self._rules: list[_Rule] = []
        for block in (style_blocks or []):
            self._parse_block(block)

    def add_block(self, css: str) -> None:
        """Parse and add rules from a CSS string (e.g. a ``<style>`` tag body)."""
        self._parse_block(css)

    def resolve(self, element) -> dict[str, str]:
        """Return resolved CSS properties for *element* (an lxml element).

        Cascade order (highest priority last, so it wins):
          1. Matching stylesheet rules, sorted by specificity + source order
          2. ``!important`` stylesheet rules override normal inline
          3. Inline ``style=""`` attribute (treated as specificity 1000)
          4. ``!important`` inline beats everything

        Returns a flat ``{property: value}`` dict of raw CSS strings.
        """
        matching = [r for r in self._rules if _matches(element, r.selector)]

        # Separate important vs normal rules
        normal_rules = sorted(
            matching, key=lambda r: (r.specificity, r.order)
        )
        important_rules = sorted(
            [r for r in matching if r.important],
            key=lambda r: (r.specificity, r.order),
        )

        merged: dict[str, str] = {}

        # Apply normal rules (lower specificity first, higher overwrites)
        for rule in normal_rules:
            for prop, val in rule.properties.items():
                if prop not in rule.important:
                    merged[prop] = val

        # Apply inline style (beats normal rules)
        inline = parse_inline_style(element.get("style", "") or "")
        normal_inline = {p: v for p, v in inline.items() if p not in _important_inline(element)}
        merged.update(normal_inline)

        # Apply !important stylesheet rules (beats normal inline)
        for rule in important_rules:
            for prop in rule.important:
                merged[prop] = rule.properties[prop]

        # Apply !important inline (beats everything)
        merged.update(_important_inline(element))

        return merged

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _parse_block(self, css: str) -> None:
        css = _strip_comments(css)
        # Remove @rules (@media, @font-face, etc.) — not supported
        css = _strip_at_rules(css)

        order = len(self._rules)
        for selector_text, declarations in _iter_rules(css):
            props, important = _parse_declarations(declarations)
            if not props:
                continue
            for selector in _split_selectors(selector_text):
                selector = selector.strip()
                if not selector or _is_unsupported_selector(selector):
                    continue
                self._rules.append(_Rule(
                    selector=selector,
                    properties=props,
                    important=important,
                    specificity=_specificity(selector),
                    order=order,
                ))
                order += 1


# ---------------------------------------------------------------------------
# Standalone helpers (also used by element_parser)
# ---------------------------------------------------------------------------

def parse_inline_style(style_attr: str) -> dict[str, str]:
    """Parse a ``style=""`` attribute string into a ``{property: value}`` dict.

    ``!important`` is stripped from values; use :func:`_important_inline` to
    retrieve the set of important property names.
    """
    result: dict[str, str] = {}
    for declaration in style_attr.split(";"):
        declaration = declaration.strip()
        if not declaration or ":" not in declaration:
            continue
        prop, _, val = declaration.partition(":")
        prop = prop.strip().lower()
        val = val.replace("!important", "").strip()
        if prop and val:
            result[prop] = val
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _important_inline(element) -> dict[str, str]:
    """Return {prop: val} for !important properties in the inline style."""
    result: dict[str, str] = {}
    style_attr = element.get("style", "") or ""
    for declaration in style_attr.split(";"):
        if "!important" not in declaration or ":" not in declaration:
            continue
        prop, _, val = declaration.partition(":")
        prop = prop.strip().lower()
        val = val.replace("!important", "").strip()
        if prop and val:
            result[prop] = val
    return result


def _strip_comments(css: str) -> str:
    return re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)


def _strip_at_rules(css: str) -> str:
    """Remove all @-rules, handling nested braces correctly."""
    # First strip simple @rules ending in semicolons (@import, @charset, etc.)
    css = re.sub(r'@[^{;]+;', '', css)
    # Then strip block @rules (@media, @keyframes, etc.) with proper brace matching
    result = []
    i = 0
    while i < len(css):
        if css[i] == '@':
            # Skip to opening brace
            j = css.find('{', i)
            if j == -1:
                break
            # Count braces to find matching close brace
            depth = 0
            k = j
            while k < len(css):
                if css[k] == '{':
                    depth += 1
                elif css[k] == '}':
                    depth -= 1
                    if depth == 0:
                        i = k + 1
                        break
                k += 1
            else:
                break
        else:
            result.append(css[i])
            i += 1
    return ''.join(result)


def _iter_rules(css: str):
    """Yield (selector_text, declarations) pairs from a CSS string."""
    # Match selector { declarations } blocks
    for m in re.finditer(r'([^{]+)\{([^}]*)\}', css):
        yield m.group(1).strip(), m.group(2).strip()


def _split_selectors(selector_text: str) -> list[str]:
    """Split a comma-separated selector list into individual selectors."""
    return [s.strip() for s in selector_text.split(",")]


def _parse_declarations(declarations: str) -> tuple[dict[str, str], set[str]]:
    """Parse a CSS declaration block.

    Returns:
        (properties, important_set) where important_set holds property names
        that had ``!important``.
    """
    props: dict[str, str] = {}
    important: set[str] = set()
    for decl in declarations.split(";"):
        decl = decl.strip()
        if not decl or ":" not in decl:
            continue
        prop, _, val = decl.partition(":")
        prop = prop.strip().lower()
        val = val.strip()
        if not prop or not val:
            continue
        if "!important" in val:
            val = val.replace("!important", "").strip()
            important.add(prop)
        props[prop] = val
    return props, important


def _is_unsupported_selector(selector: str) -> bool:
    """Return True if the selector contains constructs we don't support."""
    # Pseudo-classes/elements, attribute selectors, complex combinators
    return bool(re.search(r':|[\[\]>+~]', selector))


def _specificity(selector: str) -> int:
    """Calculate the numeric specificity of a simple selector."""
    score = 0
    # ID selectors
    score += len(re.findall(r'#[\w-]+', selector)) * 100
    # Class selectors
    score += len(re.findall(r'\.[\w-]+', selector)) * 10
    # Element selectors (strip IDs and classes first to avoid false matches)
    element_part = re.sub(r'[#.][\w-]+', '', selector).strip()
    if element_part and element_part != '*':
        # Count space-separated tokens (descendant selectors)
        score += len(element_part.split()) * 1
    return score


def _matches(element, selector: str) -> bool:
    """Return True if *element* matches *selector*.

    Handles: element, .class, #id, element.class, descendant (space-separated).
    """
    # Descendant selector: "div p" → split on spaces
    parts = selector.strip().split()
    if len(parts) > 1:
        # The last part must match this element; the rest must match ancestors
        if not _matches_simple(element, parts[-1]):
            return False
        # Walk up the ancestor chain looking for the preceding parts
        remaining = parts[:-1]
        ancestor = element.getparent()
        while ancestor is not None and remaining:
            if _matches_simple(ancestor, remaining[-1]):
                remaining = remaining[:-1]
            ancestor = ancestor.getparent()
        return len(remaining) == 0

    return _matches_simple(element, selector)


def _matches_simple(element, selector: str) -> bool:
    """Match a simple (non-descendant) selector against an element."""
    if selector == '*':
        return True

    # Parse: optional element name + optional .classes + optional #id
    m = re.match(
        r'^(?P<tag>[a-zA-Z][a-zA-Z0-9]*)?'
        r'(?P<classes>(?:\.[a-zA-Z_][\w-]*)*)?'
        r'(?P<id>#[a-zA-Z_][\w-]*)?$',
        selector,
    )
    if not m:
        return False

    tag = m.group("tag")
    classes_str = m.group("classes") or ""
    id_part = m.group("id")

    # Must have at least one constraint
    if not tag and not classes_str and not id_part:
        return False

    if tag and element.tag != tag:
        return False

    if classes_str:
        el_classes = set((element.get("class") or "").split())
        for cls in re.findall(r'\.([a-zA-Z_][\w-]*)', classes_str):
            if cls not in el_classes:
                return False

    if id_part:
        required_id = id_part.lstrip("#")
        if element.get("id") != required_id:
            return False

    return True
