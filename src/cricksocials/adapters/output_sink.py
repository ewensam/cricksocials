"""OutputSink protocol and built-in implementations.

Phase 13 will implement GoogleDriveOutputSink.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date
from pathlib import Path
from typing import Protocol

from cricksocials.config import LocalOutputConfig


@dataclass(frozen=True)
class PostDraft:
    """A composed post ready to be written out by an OutputSink."""

    image_bytes: bytes
    caption: str
    match_id: str
    date: Date
    team: str


class OutputSink(Protocol):
    def write_post(self, draft: PostDraft) -> str: ...  # returns location string


class LocalFolderOutputSink:
    """Writes image + caption to drafts_dir/YYYY-MM-DD/<team>/."""

    def __init__(self, config: LocalOutputConfig) -> None:
        self._config = config

    def write_post(self, draft: PostDraft) -> str:
        drafts_dir = Path(self._config.drafts_dir)
        team_dir = drafts_dir / draft.date.isoformat() / _safe_dirname(draft.team)
        team_dir.mkdir(parents=True, exist_ok=True)

        (team_dir / f"{draft.match_id}.png").write_bytes(draft.image_bytes)
        (team_dir / f"{draft.match_id}.txt").write_text(draft.caption, encoding="utf-8")

        return str(team_dir)


def _safe_dirname(name: str) -> str:
    """Replace filesystem-unsafe characters in *name* for use as a directory name."""
    return "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name).strip()
