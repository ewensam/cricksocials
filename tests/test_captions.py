"""Tests for the caption template renderer (Phase 7)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from cricksocials.captions import generate_caption
from cricksocials.config import Config
from cricksocials.parser import BattingPerformance, BowlingPerformance, InningsData, MatchResult

REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_match(outcome: str) -> MatchResult:
    return MatchResult(
        match_id="1",
        date=date(2026, 5, 25),
        home_club="Bridestowe and Belstone CC",
        ground="Home Ground",
        result_text="WON BY 15 RUNS",
        result_for_home_club=outcome,  # type: ignore[arg-type]
        innings=[
            InningsData(
                team_name="Bridestowe and Belstone CC",
                total_runs=187,
                wickets_down=6,
                overs="40.0",
                all_out=False,
                extras=12,
                batting=[
                    BattingPerformance(
                        name="Jordan Smith", runs=67, balls=58, fours=8, sixes=2,
                        not_out=True, how_out="",
                    ),
                ],
                bowling=[
                    BowlingPerformance(
                        name="Casey Jones", overs="8", maidens=1, runs=24,
                        wickets=3, wides=0, no_balls=0,
                    ),
                ],
            ),
            InningsData(
                team_name="Opposition CC",
                total_runs=172,
                wickets_down=10,
                overs="38.2",
                all_out=True,
                extras=9,
                batting=[],
                bowling=[],
            ),
        ],
    )


@pytest.fixture
def config(tmp_path: Path) -> Config:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "win_captions.txt").write_text(
        "# comment line, ignored\n"
        "\n"
        "Win! {club} {team} {score_line} {batting_highlight} {bowling_highlight} {hashtags}\n"
    )
    (templates_dir / "loss_captions.txt").write_text(
        "Tough one, {club} {team}. {score_line} {hashtags}\n"
    )

    return Config.model_validate(
        {
            "club": {
                "name": "Bridestowe and Belstone CC",
                "short_name": "B&B",
                "play_cricket_subdomain": "bridestoweandbelstone",
            },
            "teams": [{"name": "1st XI", "identifier": "1st"}],
            "branding": {
                "logo_path": str(REPO_ROOT / "assets" / "logo.png"),
                "fonts": {
                    "bold": str(REPO_ROOT / "assets" / "fonts" / "Montserrat-Bold.ttf"),
                    "regular": str(REPO_ROOT / "assets" / "fonts" / "Montserrat-Regular.ttf"),
                },
            },
            "captions": {
                "template_dir": str(templates_dir),
                "hashtags": ["#DevonCricket", "#VillageCricket"],
            },
        }
    )


class TestGenerateCaption:
    def test_win_uses_win_template_and_substitutes_placeholders(self, config: Config) -> None:
        caption = generate_caption(_make_match("win"), "1st XI", config)
        assert caption.startswith("Win! B&B 1st XI")
        assert "B&B 187/6 beat Opposition CC 172ao" in caption
        assert "J. Smith 67* (58b)" in caption
        assert "C. Jones 3/24 (8 ovs)" in caption
        assert "#DevonCricket #VillageCricket" in caption

    def test_loss_uses_loss_template(self, config: Config) -> None:
        caption = generate_caption(_make_match("loss"), "1st XI", config)
        assert caption.startswith("Tough one, B&B 1st XI")

    @pytest.mark.parametrize("outcome", ["draw", "tie", "abandoned", "unknown"])
    def test_non_win_outcomes_fall_back_to_loss_template(
        self, config: Config, outcome: str
    ) -> None:
        caption = generate_caption(_make_match(outcome), "1st XI", config)
        assert caption.startswith("Tough one, B&B 1st XI")

    def test_missing_template_dir_raises(self, config: Config, tmp_path: Path) -> None:
        config.captions.template_dir = tmp_path / "does-not-exist"
        with pytest.raises(FileNotFoundError):
            generate_caption(_make_match("win"), "1st XI", config)

    def test_empty_template_file_raises_value_error(self, config: Config) -> None:
        (Path(config.captions.template_dir) / "win_captions.txt").write_text("# only a comment\n")
        with pytest.raises(ValueError, match="No usable caption templates"):
            generate_caption(_make_match("win"), "1st XI", config)
