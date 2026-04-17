"""Tests for tab stop support via the mutable API."""

from __future__ import annotations

from pathlib import Path

import docwow
from docwow.api.paragraph import MutableParagraph
from docwow.api.run import MutableRun
from docwow.models.styles import ParagraphFormatting, TabStop

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestTabStopModel:
    def test_default_empty(self):
        assert ParagraphFormatting().tab_stops == ()

    def test_explicit_stops(self):
        stops = (TabStop(36.0, "left"), TabStop(144.0, "center"))
        fmt = ParagraphFormatting(tab_stops=stops)
        assert len(fmt.tab_stops) == 2

    def test_tab_stop_fields(self):
        stop = TabStop(position_pt=72.0, alignment="right", leader="dot")
        assert stop.position_pt == 72.0
        assert stop.alignment == "right"
        assert stop.leader == "dot"

    def test_tab_stop_no_leader_default(self):
        stop = TabStop(position_pt=36.0, alignment="left")
        assert stop.leader is None


class TestMutableParagraphTabStops:
    def test_default_empty(self):
        para = MutableParagraph()
        assert para.tab_stops == ()

    def test_set_tab_stops(self):
        para = MutableParagraph()
        stops = (TabStop(36.0, "left"), TabStop(144.0, "right"))
        result = para.set_tab_stops(stops)
        assert len(para.tab_stops) == 2
        assert result is para  # chainable

    def test_clear_tab_stops(self):
        para = MutableParagraph()
        para.set_tab_stops((TabStop(36.0, "left"),))
        para.set_tab_stops(())
        assert para.tab_stops == ()

    def test_set_tab_stops_preserves_other_formatting(self):
        para = MutableParagraph()
        para.set_alignment("center")
        para.set_tab_stops((TabStop(36.0, "left"),))
        assert para.alignment == "center"

    def test_other_setters_preserve_tab_stops(self):
        para = MutableParagraph()
        stops = (TabStop(36.0, "left"),)
        para.set_tab_stops(stops)
        para.set_alignment("right")
        assert len(para.tab_stops) == 1

    def test_to_frozen_carries_tab_stops(self):
        para = MutableParagraph()
        stops = (TabStop(36.0, "left"),)
        para.set_tab_stops(stops)
        frozen = para._to_frozen()
        assert len(frozen.formatting.tab_stops) == 1
        assert frozen.formatting.tab_stops[0].alignment == "left"


class TestTabStopsRoundTrip:
    def test_tab_stops_survive_docx_round_trip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        stops = (
            TabStop(position_pt=72.0, alignment="left"),
            TabStop(position_pt=216.0, alignment="right", leader="dot"),
        )
        para.set_tab_stops(stops)

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        assert len(para2.tab_stops) == 2
        assert para2.tab_stops[0].alignment == "left"
        assert para2.tab_stops[0].position_pt == 72.0
        assert para2.tab_stops[1].alignment == "right"
        assert para2.tab_stops[1].leader == "dot"

    def test_tab_character_survives_round_trip(self):
        doc = docwow.open(FIXTURES / "paragraphs.docx")
        para = next(p for p in doc.paragraphs if isinstance(p, MutableParagraph))
        para.runs.clear()
        para.runs.add_text("before\tafter")

        data = doc.to_bytes()
        doc2 = docwow.open(data)
        para2 = next(p for p in doc2.paragraphs if isinstance(p, MutableParagraph))
        text = "".join(r.get_text() for r in para2.runs if isinstance(r, MutableRun))
        assert "\t" in text
