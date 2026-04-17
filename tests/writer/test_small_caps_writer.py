"""Tests for w:smallCaps and w:caps being written into OOXML."""

from __future__ import annotations

from lxml import etree

from docwow.models.styles import RunFormatting
from docwow.writer.styles_writer import _write_run_fmt

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _qn(name: str) -> str:
    return f"{{{W}}}{name}"


def _rpr(fmt: RunFormatting) -> etree._Element:
    rpr = etree.Element(_qn("rPr"))
    _write_run_fmt(rpr, fmt)
    return rpr


class TestSmallCapsWriter:
    def test_small_caps_written(self):
        rpr = _rpr(RunFormatting(small_caps=True))
        assert rpr.find(_qn("smallCaps")) is not None

    def test_small_caps_omitted_when_false(self):
        rpr = _rpr(RunFormatting(small_caps=False))
        assert rpr.find(_qn("smallCaps")) is None


class TestAllCapsWriter:
    def test_caps_written(self):
        rpr = _rpr(RunFormatting(all_caps=True))
        assert rpr.find(_qn("caps")) is not None

    def test_caps_omitted_when_false(self):
        rpr = _rpr(RunFormatting(all_caps=False))
        assert rpr.find(_qn("caps")) is None
