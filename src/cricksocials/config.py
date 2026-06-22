"""Pydantic config models and YAML loader (Phase 1)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class ColourConfig(BaseModel):
    primary: str = "#1B2A4A"
    accent: str = "#2D7F4E"
    text: str = "#FFFFFF"


class FontConfig(BaseModel):
    bold: Path
    regular: Path


class BrandingConfig(BaseModel):
    logo_path: Path
    colours: ColourConfig = Field(default_factory=ColourConfig)
    overlay_opacity: float = Field(default=0.70, ge=0.0, le=1.0)
    fonts: FontConfig


class ClubConfig(BaseModel):
    name: str
    short_name: str
    play_cricket_subdomain: str


class TeamConfig(BaseModel):
    name: str
    identifier: str


class StatsConfig(BaseModel):
    batting_threshold_runs: int = Field(default=30, ge=0)
    bowling_threshold_wickets: int = Field(default=2, ge=0)
    fallback_to_top_performer: bool = True


class LocalPhotosConfig(BaseModel):
    win_dir: Path = Path("./photos/win")
    loss_dir: Path = Path("./photos/loss")


class PhotosConfig(BaseModel):
    adapter: Literal["local", "google_drive"] = "local"
    local: LocalPhotosConfig = Field(default_factory=LocalPhotosConfig)


class LocalOutputConfig(BaseModel):
    drafts_dir: Path = Path("./drafts")


class OutputConfig(BaseModel):
    adapter: Literal["local", "google_drive"] = "local"
    local: LocalOutputConfig = Field(default_factory=LocalOutputConfig)


class CaptionsConfig(BaseModel):
    template_dir: Path = Path("./templates")
    hashtags: list[str] = Field(default_factory=list)


class ScrapingConfig(BaseModel):
    request_delay_seconds: float = Field(default=3.0, ge=0.0)
    use_cloudscraper_fallback: bool = True
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )


class StateConfig(BaseModel):
    path: Path = Path("./state/processed_matches.json")


class Config(BaseModel):
    club: ClubConfig
    teams: list[TeamConfig]
    branding: BrandingConfig
    stats: StatsConfig = Field(default_factory=StatsConfig)
    photos: PhotosConfig = Field(default_factory=PhotosConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    captions: CaptionsConfig = Field(default_factory=CaptionsConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    state: StateConfig = Field(default_factory=StateConfig)

    @model_validator(mode="after")
    def _at_least_one_team(self) -> Config:
        if not self.teams:
            raise ValueError("At least one team must be configured under 'teams:'")
        return self


def load_config(path: str | Path) -> Config:
    """Load and validate a club config YAML file.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if the file is not valid YAML or fails Pydantic validation.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Config file must be a YAML mapping, got {type(raw).__name__}: {path}")

    try:
        return Config.model_validate(raw)
    except Exception as exc:
        raise ValueError(f"Invalid config in {path}:\n{exc}") from exc
