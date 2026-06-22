"""Caption template renderer (Phase 7)."""

from __future__ import annotations

import random
from pathlib import Path

from cricksocials.config import Config
from cricksocials.parser import MatchResult
from cricksocials.stats import (
    find_our_innings,
    format_batting,
    format_bowling,
    format_score_line,
    select_batting_highlight,
    select_bowling_highlight,
)


def generate_caption(match: MatchResult, team_name: str, config: Config) -> str:
    """Render a social media caption for *match* using a random template line.

    Wins use `win_captions.txt`; every other outcome (loss, draw, tie,
    abandoned, unknown) uses `loss_captions.txt`.
    """
    is_win = match.result_for_home_club == "win"
    template_file = "win_captions.txt" if is_win else "loss_captions.txt"
    template_path = Path(config.captions.template_dir) / template_file
    template = random.choice(_load_templates(template_path))

    our_innings = find_our_innings(match.innings, match.home_club)
    batting = select_batting_highlight(our_innings.batting, config.stats) if our_innings else None
    bowling = select_bowling_highlight(our_innings.bowling, config.stats) if our_innings else None

    values = {
        "club": config.club.short_name,
        "team": team_name,
        "score_line": format_score_line(match, match.home_club, config.club.short_name),
        "batting_highlight": format_batting(batting) if batting else "",
        "bowling_highlight": format_bowling(bowling) if bowling else "",
        "hashtags": " ".join(config.captions.hashtags),
    }
    return template.format(**values)


def _load_templates(path: Path) -> list[str]:
    """Return non-empty, non-comment lines from a caption template file."""
    lines = [
        stripped
        for raw_line in path.read_text(encoding="utf-8").splitlines()
        if (stripped := raw_line.strip()) and not stripped.startswith("#")
    ]
    if not lines:
        raise ValueError(f"No usable caption templates found in {path}")
    return lines
