"""Tests for config.py — Phase 1."""

from __future__ import annotations

from pathlib import Path

import pytest

from cricksocials.config import Config, StatsConfig, load_config

# Root of the repo (parent of the tests/ directory)
REPO_ROOT = Path(__file__).parent.parent


class TestLoadConfig:
    def test_load_example_config(self) -> None:
        """config.example.yaml should round-trip without errors."""
        cfg = load_config(REPO_ROOT / "config.example.yaml")

        assert cfg.club.name == "Bridestowe and Belstone CC"
        assert cfg.club.short_name == "B&B"
        assert cfg.club.play_cricket_subdomain == "bridestoweandbelstone"

    def test_example_config_teams(self) -> None:
        cfg = load_config(REPO_ROOT / "config.example.yaml")
        team_names = [t.name for t in cfg.teams]
        assert "1st XI" in team_names
        assert "2nd XI" in team_names

    def test_example_config_stats_defaults(self) -> None:
        cfg = load_config(REPO_ROOT / "config.example.yaml")
        assert cfg.stats.batting_threshold_runs == 30
        assert cfg.stats.bowling_threshold_wickets == 2
        assert cfg.stats.fallback_to_top_performer is True

    def test_example_config_adapters(self) -> None:
        cfg = load_config(REPO_ROOT / "config.example.yaml")
        assert cfg.photos.adapter == "local"
        assert cfg.output.adapter == "local"

    def test_example_config_hashtags(self) -> None:
        cfg = load_config(REPO_ROOT / "config.example.yaml")
        assert "#DevonCricket" in cfg.captions.hashtags

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_config("no_such_file.yaml")

    def test_empty_teams_raises(self) -> None:
        import yaml

        raw = yaml.safe_load((REPO_ROOT / "config.example.yaml").read_text())
        raw["teams"] = []
        with pytest.raises(ValueError, match="team"):
            Config.model_validate(raw)

    def test_invalid_overlay_opacity_raises(self) -> None:
        import yaml

        raw = yaml.safe_load((REPO_ROOT / "config.example.yaml").read_text())
        raw["branding"]["overlay_opacity"] = 1.5  # > 1.0
        with pytest.raises(Exception):
            Config.model_validate(raw)

    def test_missing_club_name_raises(self) -> None:
        import yaml

        raw = yaml.safe_load((REPO_ROOT / "config.example.yaml").read_text())
        del raw["club"]["name"]
        with pytest.raises(Exception):
            Config.model_validate(raw)

    def test_scraping_defaults(self) -> None:
        cfg = load_config(REPO_ROOT / "config.example.yaml")
        assert cfg.scraping.request_delay_seconds == 3
        assert cfg.scraping.use_cloudscraper_fallback is True


class TestStatsConfig:
    def test_defaults(self) -> None:
        s = StatsConfig()
        assert s.batting_threshold_runs == 30
        assert s.bowling_threshold_wickets == 2
        assert s.fallback_to_top_performer is True

    def test_negative_threshold_raises(self) -> None:
        with pytest.raises(Exception):
            StatsConfig(batting_threshold_runs=-1)
