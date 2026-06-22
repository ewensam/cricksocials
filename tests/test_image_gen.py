"""Tests for the Pillow image compositor (Phase 6)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from cricksocials.config import Config
from cricksocials.image_gen import CANVAS_SIZE, compose_post_image, compose_preview_image
from cricksocials.parser import BattingPerformance, BowlingPerformance, InningsData, MatchResult

REPO_ROOT = Path(__file__).resolve().parent.parent


def _sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (640, 480), (10, 20, 30))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def config(tmp_path: Path) -> Config:
    win_dir = tmp_path / "win"
    loss_dir = tmp_path / "loss"
    win_dir.mkdir()
    loss_dir.mkdir()
    (win_dir / "sample.jpg").write_bytes(_sample_jpeg_bytes())

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
            "photos": {
                "adapter": "local",
                "local": {"win_dir": str(win_dir), "loss_dir": str(loss_dir)},
            },
        }
    )


@pytest.fixture
def match() -> MatchResult:
    from datetime import date

    return MatchResult(
        match_id="123",
        date=date(2026, 5, 25),
        home_club="Bridestowe and Belstone CC",
        ground="Home Ground",
        result_text="WON BY 15 RUNS",
        result_for_home_club="win",
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
                        name="Jordan Smith",
                        runs=67,
                        balls=58,
                        fours=8,
                        sixes=2,
                        not_out=True,
                        how_out="",
                    ),
                ],
                bowling=[
                    BowlingPerformance(
                        name="Casey Jones",
                        overs="8",
                        maidens=1,
                        runs=24,
                        wickets=3,
                        wides=0,
                        no_balls=0,
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


class TestComposePostImage:
    def test_returns_valid_png_of_expected_size(self, match: MatchResult, config: Config) -> None:
        png_bytes = compose_post_image(match, _sample_jpeg_bytes(), config)
        img = Image.open(BytesIO(png_bytes))
        assert img.format == "PNG"
        assert img.size == CANVAS_SIZE

    def test_handles_missing_logo_gracefully(
        self, match: MatchResult, config: Config, tmp_path: Path
    ) -> None:
        config.branding.logo_path = tmp_path / "missing-logo.png"
        png_bytes = compose_post_image(match, _sample_jpeg_bytes(), config)
        img = Image.open(BytesIO(png_bytes))
        assert img.size == CANVAS_SIZE


class TestComposePreviewImage:
    def test_returns_valid_png(self, config: Config) -> None:
        png_bytes = compose_preview_image(config)
        img = Image.open(BytesIO(png_bytes))
        assert img.format == "PNG"
        assert img.size == CANVAS_SIZE

    def test_falls_back_to_plain_background_with_no_photos(
        self, config: Config, tmp_path: Path
    ) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        config.photos.local.win_dir = empty_dir
        png_bytes = compose_preview_image(config)
        img = Image.open(BytesIO(png_bytes))
        assert img.size == CANVAS_SIZE
