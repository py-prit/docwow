"""Tests for docwow.models.lists — ListLevel, NumberingDefinition, ListInfo."""

import pytest
from dataclasses import FrozenInstanceError

from docwow.models.lists import ListInfo, ListLevel, NumberingDefinition
from docwow.models.styles import RunFormatting


# ---------------------------------------------------------------------------
# ListLevel
# ---------------------------------------------------------------------------

class TestListLevelDefaults:
    def test_start_value_is_one(self):
        ll = ListLevel(level=0, num_fmt="decimal")
        assert ll.start_value == 1

    def test_text_template_default(self):
        ll = ListLevel(level=0, num_fmt="decimal")
        assert ll.text_template == "%1."

    def test_indent_pt_zero(self):
        ll = ListLevel(level=0, num_fmt="decimal")
        assert ll.indent_pt == 0.0

    def test_hanging_pt_zero(self):
        ll = ListLevel(level=0, num_fmt="decimal")
        assert ll.hanging_pt == 0.0

    def test_run_fmt_none(self):
        ll = ListLevel(level=0, num_fmt="decimal")
        assert ll.run_fmt is None


class TestListLevelRequiredFields:
    def test_missing_level_raises(self):
        with pytest.raises(TypeError):
            ListLevel(num_fmt="decimal")  # type: ignore[call-arg]

    def test_missing_num_fmt_raises(self):
        with pytest.raises(TypeError):
            ListLevel(level=0)  # type: ignore[call-arg]


@pytest.mark.parametrize("num_fmt", [
    "bullet",
    "decimal",
    "lowerLetter",
    "upperLetter",
    "lowerRoman",
    "upperRoman",
    "none",
])
class TestListLevelNumFmtValues:
    def test_num_fmt_stored(self, num_fmt):
        ll = ListLevel(level=0, num_fmt=num_fmt)
        assert ll.num_fmt == num_fmt


class TestListLevelCustomValues:
    def test_level_stored(self):
        for lvl in range(9):  # Word supports levels 0–8
            assert ListLevel(level=lvl, num_fmt="decimal").level == lvl

    def test_start_value(self):
        ll = ListLevel(level=0, num_fmt="decimal", start_value=5)
        assert ll.start_value == 5

    def test_text_template_nested(self):
        ll = ListLevel(level=1, num_fmt="decimal", text_template="%1.%2.")
        assert ll.text_template == "%1.%2."

    def test_indent_pt(self):
        ll = ListLevel(level=0, num_fmt="decimal", indent_pt=36.0)
        assert ll.indent_pt == 36.0

    def test_hanging_pt(self):
        ll = ListLevel(level=0, num_fmt="decimal", hanging_pt=18.0)
        assert ll.hanging_pt == 18.0

    def test_run_fmt_set(self):
        fmt = RunFormatting(bold=True)
        ll = ListLevel(level=0, num_fmt="decimal", run_fmt=fmt)
        assert ll.run_fmt == fmt


class TestListLevelImmutability:
    def test_cannot_set_level(self):
        ll = ListLevel(level=0, num_fmt="decimal")
        with pytest.raises(FrozenInstanceError):
            ll.level = 1  # type: ignore[misc]

    def test_cannot_set_num_fmt(self):
        ll = ListLevel(level=0, num_fmt="decimal")
        with pytest.raises(FrozenInstanceError):
            ll.num_fmt = "bullet"  # type: ignore[misc]


class TestListLevelEquality:
    def test_equal(self):
        assert ListLevel(level=0, num_fmt="decimal") == ListLevel(level=0, num_fmt="decimal")

    def test_not_equal_different_level(self):
        assert ListLevel(level=0, num_fmt="decimal") != ListLevel(level=1, num_fmt="decimal")

    def test_not_equal_different_fmt(self):
        assert ListLevel(level=0, num_fmt="decimal") != ListLevel(level=0, num_fmt="bullet")


# ---------------------------------------------------------------------------
# NumberingDefinition
# ---------------------------------------------------------------------------

class TestNumberingDefinitionConstruction:
    def test_basic(self):
        level = ListLevel(level=0, num_fmt="decimal")
        nd = NumberingDefinition(abstract_num_id="0", levels=(level,))
        assert nd.abstract_num_id == "0"
        assert len(nd.levels) == 1
        assert nd.levels[0] == level

    def test_empty_levels(self):
        nd = NumberingDefinition(abstract_num_id="0", levels=())
        assert nd.levels == ()

    def test_nine_levels(self):
        # Word supports up to 9 levels (0–8)
        levels = tuple(ListLevel(level=i, num_fmt="decimal") for i in range(9))
        nd = NumberingDefinition(abstract_num_id="0", levels=levels)
        assert len(nd.levels) == 9

    def test_multiple_num_fmt(self):
        levels = (
            ListLevel(level=0, num_fmt="decimal"),
            ListLevel(level=1, num_fmt="lowerLetter"),
            ListLevel(level=2, num_fmt="lowerRoman"),
        )
        nd = NumberingDefinition(abstract_num_id="1", levels=levels)
        assert nd.levels[1].num_fmt == "lowerLetter"
        assert nd.levels[2].num_fmt == "lowerRoman"


class TestNumberingDefinitionImmutability:
    def test_cannot_set_abstract_num_id(self, sample_numbering):
        with pytest.raises(FrozenInstanceError):
            sample_numbering.abstract_num_id = "99"  # type: ignore[misc]

    def test_cannot_set_levels(self, sample_numbering):
        with pytest.raises(FrozenInstanceError):
            sample_numbering.levels = ()  # type: ignore[misc]


class TestNumberingDefinitionEquality:
    def test_equal(self):
        level = ListLevel(level=0, num_fmt="decimal")
        nd1 = NumberingDefinition(abstract_num_id="0", levels=(level,))
        nd2 = NumberingDefinition(abstract_num_id="0", levels=(level,))
        assert nd1 == nd2

    def test_not_equal_different_id(self):
        level = ListLevel(level=0, num_fmt="decimal")
        nd1 = NumberingDefinition(abstract_num_id="0", levels=(level,))
        nd2 = NumberingDefinition(abstract_num_id="1", levels=(level,))
        assert nd1 != nd2


# ---------------------------------------------------------------------------
# ListInfo
# ---------------------------------------------------------------------------

class TestListInfoConstruction:
    def test_basic(self):
        li = ListInfo(num_id="1", level=0)
        assert li.num_id == "1"
        assert li.level == 0

    def test_all_valid_levels(self):
        for lvl in range(9):
            li = ListInfo(num_id="1", level=lvl)
            assert li.level == lvl

    def test_num_id_as_string(self):
        li = ListInfo(num_id="42", level=3)
        assert li.num_id == "42"


class TestListInfoRequiredFields:
    def test_missing_num_id_raises(self):
        with pytest.raises(TypeError):
            ListInfo(level=0)  # type: ignore[call-arg]

    def test_missing_level_raises(self):
        with pytest.raises(TypeError):
            ListInfo(num_id="1")  # type: ignore[call-arg]


class TestListInfoImmutability:
    def test_cannot_set_num_id(self):
        li = ListInfo(num_id="1", level=0)
        with pytest.raises(FrozenInstanceError):
            li.num_id = "2"  # type: ignore[misc]

    def test_cannot_set_level(self):
        li = ListInfo(num_id="1", level=0)
        with pytest.raises(FrozenInstanceError):
            li.level = 1  # type: ignore[misc]


class TestListInfoEquality:
    def test_equal(self):
        assert ListInfo(num_id="1", level=0) == ListInfo(num_id="1", level=0)

    def test_not_equal_different_num_id(self):
        assert ListInfo(num_id="1", level=0) != ListInfo(num_id="2", level=0)

    def test_not_equal_different_level(self):
        assert ListInfo(num_id="1", level=0) != ListInfo(num_id="1", level=1)


class TestListInfoHashable:
    def test_can_be_used_in_set(self):
        li = ListInfo(num_id="1", level=0)
        s = {li, ListInfo(num_id="1", level=0), ListInfo(num_id="2", level=0)}
        assert len(s) == 2
