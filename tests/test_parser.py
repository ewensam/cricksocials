"""Tests for parser.py — Phase 2.

Exercises parse_match_page() against the real saved Play Cricket HTML
in tests/fixtures/match_7303496.html.

Match: Bridestowe and Belstone CC vs Ivybridge CC
Date:  09 May 2026
Result: B&B WON BY 15 RUNS
B&B: 146ao (48.1 ovs)   Ivybridge: 131ao (36.2 ovs)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from cricksocials.parser import parse_match_page

FIXTURE = Path(__file__).parent / "fixtures" / "match_7303496.html"


@pytest.fixture(scope="module")
def result():  # type: ignore[return]
    html = FIXTURE.read_text(encoding="utf-8", errors="replace")
    return parse_match_page(html)


# ---------------------------------------------------------------------------
# Top-level match metadata
# ---------------------------------------------------------------------------


class TestMatchMetadata:
    def test_match_id(self, result) -> None:  # type: ignore[no-untyped-def]
        assert result.match_id == "7303496"

    def test_date(self, result) -> None:  # type: ignore[no-untyped-def]
        assert result.date == date(2026, 5, 9)

    def test_home_club(self, result) -> None:  # type: ignore[no-untyped-def]
        assert "Bridestowe" in result.home_club or "BRIDESTOWE" in result.home_club

    def test_ground(self, result) -> None:  # type: ignore[no-untyped-def]
        assert result.ground == "Filham Park"

    def test_result_text(self, result) -> None:  # type: ignore[no-untyped-def]
        assert "15" in result.result_text
        assert "RUNS" in result.result_text.upper() or "runs" in result.result_text.lower()

    def test_result_for_home_club_is_win(self, result) -> None:  # type: ignore[no-untyped-def]
        assert result.result_for_home_club == "win"

    def test_two_innings_parsed(self, result) -> None:  # type: ignore[no-untyped-def]
        assert len(result.innings) == 2


# ---------------------------------------------------------------------------
# First innings — B&B batting
# ---------------------------------------------------------------------------


class TestBBInnings:
    @pytest.fixture(autouse=True)
    def _setup(self, result) -> None:  # type: ignore[no-untyped-def]
        self.inn = next(i for i in result.innings if "Bridestowe" in i.team_name)

    def test_team_name(self) -> None:
        assert "Bridestowe" in self.inn.team_name

    def test_total_runs(self) -> None:
        assert self.inn.total_runs == 146

    def test_wickets_all_out(self) -> None:
        assert self.inn.all_out is True
        assert self.inn.wickets_down == 10

    def test_overs(self) -> None:
        assert self.inn.overs == "48.1"

    def test_extras(self) -> None:
        assert self.inn.extras == 12

    def test_batting_count(self) -> None:
        assert len(self.inn.batting) == 11

    def test_shaquan_glasgow(self) -> None:
        glasgow = next(b for b in self.inn.batting if "Glasgow" in b.name)
        assert glasgow.runs == 47
        assert glasgow.balls == 94
        assert glasgow.fours == 5
        assert glasgow.sixes == 0
        assert glasgow.not_out is False

    def test_brandon_horn(self) -> None:
        horn = next(b for b in self.inn.batting if "Horn" in b.name)
        assert horn.runs == 31
        assert horn.balls == 35

    def test_noah_metherell_not_out(self) -> None:
        metherell = next(b for b in self.inn.batting if "Metherell" in b.name)
        assert metherell.not_out is True
        assert metherell.runs == 9

    def test_bowling_by_ivybridge_bowlers(self) -> None:
        bowler_names = [b.name for b in self.inn.bowling]
        assert any("Worth" in n for n in bowler_names)
        assert any("Huxtable" in n for n in bowler_names)
        assert any("Coker" in n for n in bowler_names)

    def test_tom_worth_bowling(self) -> None:
        worth = next(b for b in self.inn.bowling if "Worth" in b.name)
        assert worth.wickets == 2
        assert worth.runs == 36
        assert worth.overs == "10"


# ---------------------------------------------------------------------------
# Second innings — Ivybridge batting / B&B bowling
# ---------------------------------------------------------------------------


class TestIvybridgeInnings:
    @pytest.fixture(autouse=True)
    def _setup(self, result) -> None:  # type: ignore[no-untyped-def]
        self.inn = next(i for i in result.innings if "Ivybridge" in i.team_name)

    def test_team_name(self) -> None:
        assert "Ivybridge" in self.inn.team_name

    def test_total_runs(self) -> None:
        assert self.inn.total_runs == 131

    def test_wickets_all_out(self) -> None:
        assert self.inn.all_out is True
        assert self.inn.wickets_down == 10

    def test_overs(self) -> None:
        assert self.inn.overs == "36.2"

    def test_michael_copeland_top_scorer(self) -> None:
        copeland = next(b for b in self.inn.batting if "Copeland" in b.name)
        assert copeland.runs == 61
        assert copeland.balls == 63
        assert copeland.fours == 7
        assert copeland.sixes == 1

    def test_craig_penberthy_5_wickets(self) -> None:
        penberthy = next(b for b in self.inn.bowling if "Penberthy" in b.name)
        assert penberthy.wickets == 5
        assert penberthy.runs == 14
        assert penberthy.overs == "6"

    def test_simon_gillespie_bowling(self) -> None:
        gillespie = next(b for b in self.inn.bowling if "Gillespie" in b.name)
        assert gillespie.wickets == 2
        assert gillespie.runs == 12
        assert gillespie.maidens == 5
