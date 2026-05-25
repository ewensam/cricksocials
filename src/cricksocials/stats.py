"""Stats thresholds, performer selection, and formatting (Phase 4).

All functions accept the raw data types from parser.py and config.py.
They are pure functions with no side effects — easy to unit-test and
to call from the orchestrator or the preview command.
"""

from __future__ import annotations

from cricksocials.config import StatsConfig
from cricksocials.parser import BattingPerformance, BowlingPerformance, InningsData, MatchResult


# ---------------------------------------------------------------------------
# Highlight selection
# ---------------------------------------------------------------------------


def select_batting_highlight(
    batting: list[BattingPerformance],
    config: StatsConfig,
) -> BattingPerformance | None:
    """Return the most notable batting performance, or None.

    Algorithm:
      1. Collect all performances at or above `batting_threshold_runs`.
      2. If any qualify, return the one with the highest runs (ties broken by
         fewest balls — better strike rate).
      3. If none qualify and `fallback_to_top_performer` is True, return the
         top scorer regardless of threshold.
      4. Otherwise return None.
    """
    if not batting:
        return None

    above = [b for b in batting if b.runs >= config.batting_threshold_runs]

    if above:
        return max(above, key=lambda b: (b.runs, -b.balls if b.balls else 0))

    if config.fallback_to_top_performer:
        top = max(batting, key=lambda b: b.runs)
        return top if top.runs > 0 else None

    return None


def select_bowling_highlight(
    bowling: list[BowlingPerformance],
    config: StatsConfig,
) -> BowlingPerformance | None:
    """Return the most notable bowling performance, or None.

    Algorithm:
      1. Collect all performances at or above `bowling_threshold_wickets`.
      2. If any qualify, return the one with the most wickets (ties broken by
         fewest runs).
      3. If none qualify and `fallback_to_top_performer` is True, return the
         bowler with the most wickets regardless of threshold (skip 0-wicket
         bowlers unless they're all 0-wicket).
      4. Otherwise return None.
    """
    if not bowling:
        return None

    above = [b for b in bowling if b.wickets >= config.bowling_threshold_wickets]

    if above:
        return max(above, key=lambda b: (b.wickets, -b.runs))

    if config.fallback_to_top_performer:
        best = max(bowling, key=lambda b: (b.wickets, -b.runs))
        return best if best.wickets > 0 else None

    return None


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _abbreviate_name(full_name: str) -> str:
    """'Shaquan Glasgow' → 'S. Glasgow'."""
    parts = full_name.strip().split()
    if len(parts) < 2:
        return full_name
    return f"{parts[0][0]}. {' '.join(parts[1:])}"


def format_batting(perf: BattingPerformance) -> str:
    """Format a batting performance for use in captions / image overlays.

    Example outputs:
      "S. Glasgow 47 (94b)"
      "B. Horn 31* (35b)"    ← not out
    """
    name = _abbreviate_name(perf.name)
    not_out_marker = "*" if perf.not_out else ""
    if perf.balls:
        return f"{name} {perf.runs}{not_out_marker} ({perf.balls}b)"
    return f"{name} {perf.runs}{not_out_marker}"


def format_bowling(perf: BowlingPerformance) -> str:
    """Format a bowling performance for use in captions / image overlays.

    Example output:
      "C. Penberthy 5/14 (6 ovs)"
    """
    name = _abbreviate_name(perf.name)
    return f"{name} {perf.wickets}/{perf.runs} ({perf.overs} ovs)"


def format_score_line(
    match: MatchResult,
    our_team_name: str,
    our_short_name: str,
) -> str:
    """Build a concise score-line for a social media caption.

    Examples:
      "B&B 146ao beat Ivybridge CC 131ao"
      "B&B 131/4 lost to Ivybridge CC 145ao"
      "B&B 160/6 drew with Stithians CC 158/8"
      "Match abandoned (B&B vs Ivybridge CC)"

    Args:
        match:          Parsed match result.
        our_team_name:  Club name as it appears in Play Cricket HTML.
        our_short_name: Abbreviation used in output (e.g. "B&B").

    Returns:
        Formatted score-line string.
    """
    if match.result_for_home_club == "abandoned":
        opposition = _find_opposition_name(match.innings, our_team_name)
        return f"Match abandoned ({our_short_name} vs {opposition})"

    our_innings = _find_our_innings(match.innings, our_team_name)
    their_innings = _find_opposition_innings(match.innings, our_team_name)

    our_score = _score_str(our_innings) if our_innings else "?"
    their_score = _score_str(their_innings) if their_innings else "?"
    their_name = their_innings.team_name if their_innings else "Opposition"

    if match.result_for_home_club == "win":
        return f"{our_short_name} {our_score} beat {their_name} {their_score}"
    if match.result_for_home_club == "loss":
        return f"{our_short_name} {our_score} lost to {their_name} {their_score}"
    if match.result_for_home_club == "draw":
        return f"{our_short_name} {our_score} drew with {their_name} {their_score}"
    if match.result_for_home_club == "tie":
        return f"{our_short_name} {our_score} tied with {their_name} {their_score}"
    # unknown
    return f"{our_short_name} {our_score} vs {their_name} {their_score}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _score_str(innings: InningsData) -> str:
    """Format an innings total: '146ao' or '146/4'."""
    if innings.all_out:
        return f"{innings.total_runs}ao"
    return f"{innings.total_runs}/{innings.wickets_down}"


def _find_our_innings(innings: list[InningsData], our_team_name: str) -> InningsData | None:
    our_lower = our_team_name.lower()
    for i in innings:
        if our_lower in i.team_name.lower():
            return i
    return None


def _find_opposition_innings(innings: list[InningsData], our_team_name: str) -> InningsData | None:
    our_lower = our_team_name.lower()
    for i in innings:
        if our_lower not in i.team_name.lower():
            return i
    return None


def _find_opposition_name(innings: list[InningsData], our_team_name: str) -> str:
    opp = _find_opposition_innings(innings, our_team_name)
    return opp.team_name if opp else "Opposition"
