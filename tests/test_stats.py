"""Tests for stats.py — Phase 4.

Uses synthetic BattingPerformance / BowlingPerformance objects so tests
remain fast and fixture-independent.  Parser integration is covered by
test_parser.py.
"""

from __future__ import annotations

from datetime import date

import pytest

from cricksocials.config import StatsConfig
from cricksocials.parser import (
    BattingPerformance,
    BowlingPerformance,
    InningsData,
    MatchResult,
)
from cricksocials.stats import (
    format_batting,
    format_bowling,
    format_score_line,
    select_batting_highlight,
    select_bowling_highlight,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def make_bat(name: str, runs: int, balls: int = 30, not_out: bool = False) -> BattingPerformance:
    return BattingPerformance(
        name=name, runs=runs, balls=balls, fours=0, sixes=0,
        not_out=not_out, how_out="not out" if not_out else "b Bowler"
    )


def make_bowl(name: str, wickets: int, runs: int, overs: str = "10") -> BowlingPerformance:
    return BowlingPerformance(
        name=name, overs=overs, maidens=0, runs=runs, wickets=wickets, wides=0, no_balls=0
    )


def make_innings(team: str, runs: int, batting=None, bowling=None) -> InningsData:
    return InningsData(
        team_name=team,
        total_runs=runs,
        wickets_down=10,
        overs="40.0",
        all_out=True,
        extras=5,
        batting=batting or [],
        bowling=bowling or [],
    )


DEFAULT_STATS = StatsConfig(
    batting_threshold_runs=30,
    bowling_threshold_wickets=2,
    fallback_to_top_performer=True,
)

NO_FALLBACK_STATS = StatsConfig(
    batting_threshold_runs=30,
    bowling_threshold_wickets=2,
    fallback_to_top_performer=False,
)


# ---------------------------------------------------------------------------
# select_batting_highlight
# ---------------------------------------------------------------------------


class TestSelectBattingHighlight:
    def test_picks_player_above_threshold(self) -> None:
        batting = [make_bat("A. Smith", 45), make_bat("B. Jones", 10)]
        result = select_batting_highlight(batting, DEFAULT_STATS)
        assert result is not None
        assert result.name == "A. Smith"

    def test_picks_highest_when_multiple_above(self) -> None:
        batting = [make_bat("A. Smith", 45), make_bat("B. Jones", 60), make_bat("C. Lee", 32)]
        result = select_batting_highlight(batting, DEFAULT_STATS)
        assert result is not None
        assert result.name == "B. Jones"

    def test_tiebreak_by_fewer_balls(self) -> None:
        # Two players with 40 runs — fewer balls = better SR → preferred
        batting = [make_bat("A. Slow", 40, balls=80), make_bat("B. Quick", 40, balls=30)]
        result = select_batting_highlight(batting, DEFAULT_STATS)
        assert result is not None
        assert result.name == "B. Quick"

    def test_fallback_when_nobody_above_threshold(self) -> None:
        batting = [make_bat("A. Smith", 25), make_bat("B. Jones", 18)]
        result = select_batting_highlight(batting, DEFAULT_STATS)
        assert result is not None
        assert result.name == "A. Smith"  # top scorer

    def test_no_fallback_returns_none(self) -> None:
        batting = [make_bat("A. Smith", 25), make_bat("B. Jones", 18)]
        result = select_batting_highlight(batting, NO_FALLBACK_STATS)
        assert result is None

    def test_all_zeros_no_fallback_returns_none(self) -> None:
        batting = [make_bat("A. Smith", 0), make_bat("B. Jones", 0)]
        result = select_batting_highlight(batting, DEFAULT_STATS)
        assert result is None

    def test_empty_list_returns_none(self) -> None:
        assert select_batting_highlight([], DEFAULT_STATS) is None


# ---------------------------------------------------------------------------
# select_bowling_highlight
# ---------------------------------------------------------------------------


class TestSelectBowlingHighlight:
    def test_picks_player_above_threshold(self) -> None:
        bowling = [make_bowl("C. Penberthy", wickets=5, runs=14), make_bowl("S. Gillespie", wickets=1, runs=20)]
        result = select_bowling_highlight(bowling, DEFAULT_STATS)
        assert result is not None
        assert result.name == "C. Penberthy"

    def test_picks_most_wickets_when_multiple_above(self) -> None:
        bowling = [make_bowl("A", wickets=3, runs=30), make_bowl("B", wickets=4, runs=25)]
        result = select_bowling_highlight(bowling, DEFAULT_STATS)
        assert result is not None
        assert result.name == "B"

    def test_tiebreak_by_fewer_runs(self) -> None:
        bowling = [make_bowl("A", wickets=3, runs=40), make_bowl("B", wickets=3, runs=20)]
        result = select_bowling_highlight(bowling, DEFAULT_STATS)
        assert result is not None
        assert result.name == "B"

    def test_fallback_when_nobody_above_threshold(self) -> None:
        bowling = [make_bowl("A", wickets=1, runs=20), make_bowl("B", wickets=0, runs=30)]
        result = select_bowling_highlight(bowling, DEFAULT_STATS)
        assert result is not None
        assert result.name == "A"

    def test_no_fallback_returns_none(self) -> None:
        bowling = [make_bowl("A", wickets=1, runs=20)]
        result = select_bowling_highlight(bowling, NO_FALLBACK_STATS)
        assert result is None

    def test_all_zero_wickets_returns_none(self) -> None:
        bowling = [make_bowl("A", wickets=0, runs=30), make_bowl("B", wickets=0, runs=25)]
        result = select_bowling_highlight(bowling, DEFAULT_STATS)
        assert result is None

    def test_empty_list_returns_none(self) -> None:
        assert select_bowling_highlight([], DEFAULT_STATS) is None


# ---------------------------------------------------------------------------
# format_batting
# ---------------------------------------------------------------------------


class TestFormatBatting:
    def test_basic_format(self) -> None:
        perf = make_bat("Shaquan Glasgow", runs=47, balls=94)
        assert format_batting(perf) == "S. Glasgow 47 (94b)"

    def test_not_out_marker(self) -> None:
        perf = make_bat("Noah Metherell", runs=9, balls=32, not_out=True)
        assert format_batting(perf) == "N. Metherell 9* (32b)"

    def test_zero_runs(self) -> None:
        perf = make_bat("Pat Ewen", runs=0, balls=5)
        assert format_batting(perf) == "P. Ewen 0 (5b)"

    def test_single_name(self) -> None:
        perf = make_bat("Pelham", runs=50, balls=40)
        assert format_batting(perf) == "Pelham 50 (40b)"


# ---------------------------------------------------------------------------
# format_bowling
# ---------------------------------------------------------------------------


class TestFormatBowling:
    def test_basic_format(self) -> None:
        perf = make_bowl("Craig Penberthy", wickets=5, runs=14, overs="6")
        assert format_bowling(perf) == "C. Penberthy 5/14 (6 ovs)"

    def test_partial_over(self) -> None:
        perf = make_bowl("Simon Gillespie", wickets=2, runs=12, overs="8")
        assert format_bowling(perf) == "S. Gillespie 2/12 (8 ovs)"

    def test_zero_wickets(self) -> None:
        perf = make_bowl("Ryan Dennis", wickets=0, runs=32, overs="6")
        assert format_bowling(perf) == "R. Dennis 0/32 (6 ovs)"


# ---------------------------------------------------------------------------
# format_score_line
# ---------------------------------------------------------------------------


def _make_match(
    result: str,
    our_runs: int,
    our_ao: bool,
    their_runs: int,
    their_ao: bool,
    their_name: str = "Ivybridge CC",
) -> MatchResult:
    our_inn = InningsData(
        team_name="Bridestowe and Belstone CC",
        total_runs=our_runs,
        wickets_down=10 if our_ao else 4,
        overs="40.0",
        all_out=our_ao,
        extras=5,
    )
    their_inn = InningsData(
        team_name=their_name,
        total_runs=their_runs,
        wickets_down=10 if their_ao else 6,
        overs="38.0",
        all_out=their_ao,
        extras=8,
    )
    return MatchResult(
        match_id="test",
        date=date(2026, 5, 9),
        home_club="Bridestowe and Belstone CC",
        ground="Test Ground",
        result_text="WON BY 15 RUNS",
        result_for_home_club=result,  # type: ignore[arg-type]
        innings=[our_inn, their_inn],
    )


class TestFormatScoreLine:
    def test_win_both_all_out(self) -> None:
        match = _make_match("win", our_runs=146, our_ao=True, their_runs=131, their_ao=True)
        line = format_score_line(match, "Bridestowe and Belstone CC", "B&B")
        assert line == "B&B 146ao beat Ivybridge CC 131ao"

    def test_loss_line(self) -> None:
        match = _make_match("loss", our_runs=131, our_ao=True, their_runs=146, their_ao=True)
        line = format_score_line(match, "Bridestowe and Belstone CC", "B&B")
        assert line == "B&B 131ao lost to Ivybridge CC 146ao"

    def test_draw_with_wickets_in_hand(self) -> None:
        match = _make_match("draw", our_runs=187, our_ao=False, their_runs=165, their_ao=False)
        line = format_score_line(match, "Bridestowe and Belstone CC", "B&B")
        assert "drew with" in line
        assert "187/4" in line  # not all out
        assert "165/6" in line

    def test_abandoned(self) -> None:
        match = _make_match("abandoned", our_runs=0, our_ao=False, their_runs=0, their_ao=False)
        line = format_score_line(match, "Bridestowe and Belstone CC", "B&B")
        assert "abandoned" in line.lower()
        assert "B&B" in line
        assert "Ivybridge" in line
