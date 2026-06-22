"""Processed-match state tracker (JSON file)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class StateStore:
    """Tracks which Play Cricket match IDs have already been processed."""

    def __init__(self, path: Path, processed: dict[str, Any]) -> None:
        self._path = path
        self._processed = processed

    @classmethod
    def load(cls, path: Path) -> StateStore:
        """Load state from *path*, or start empty if the file doesn't exist."""
        path = Path(path)
        processed: dict[str, Any] = {}
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            processed = data.get("processed", {})
        return cls(path, processed)

    def is_processed(self, match_id: str) -> bool:
        return match_id in self._processed

    def mark_processed(self, match_id: str, metadata: dict[str, Any] | None = None) -> None:
        self._processed[match_id] = metadata or {}

    def save(self) -> None:
        """Write state to disk atomically (temp file + rename)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"processed": self._processed}, indent=2, default=str)

        fd, tmp_name = tempfile.mkstemp(dir=self._path.parent, prefix=".state-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
            os.replace(tmp_name, self._path)
        except Exception:
            os.unlink(tmp_name)
            raise
