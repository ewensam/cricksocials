"""Pydantic config models and YAML loader.

Phase 1 will implement the full validation logic.
"""

from __future__ import annotations

# TODO (Phase 1): Implement Pydantic models for all config sections:
#   ClubConfig, TeamConfig, BrandingConfig, StatsConfig,
#   PhotosConfig, OutputConfig, CaptionsConfig, ScrapingConfig, StateConfig
#   and a top-level Config that wraps them all.
#
# TODO (Phase 1): Implement load_config(path) -> Config that reads YAML,
#   validates with Pydantic, and raises a user-friendly error on failure.
