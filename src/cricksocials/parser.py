"""HTML → MatchResult dataclass parser.

Phase 2 will implement parsing against real Play Cricket HTML.
"""

from __future__ import annotations

# TODO (Phase 2): Define MatchResult dataclass (or Pydantic model) with:
#   match_id, date, home_team, away_team, result (win/loss/draw/abandoned),
#   home_score, away_score, batting_performances, bowling_performances, etc.
#
# TODO (Phase 2): Implement parse_match_page(html: str) -> MatchResult
#   Tested against tests/fixtures/match_7069988.html
