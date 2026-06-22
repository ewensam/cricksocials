"""PhotoSource protocol and built-in implementations.

Phase 13 will implement GoogleDrivePhotoSource.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from cricksocials.config import LocalPhotosConfig

PhotoCategory = Literal["win", "loss"]

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class PhotoRef:
    """Lightweight reference to a photo, adapter-specific location."""

    adapter: str  # e.g. "local", "google_drive"
    location: str  # file path or Drive file ID, depending on adapter
    category: PhotoCategory


class PhotoSource(Protocol):
    def list_photos(self, category: PhotoCategory) -> list[PhotoRef]: ...
    def fetch_photo(self, ref: PhotoRef) -> bytes: ...


class LocalFolderPhotoSource:
    """Reads photos from configured local win_dir / loss_dir folders."""

    def __init__(self, config: LocalPhotosConfig) -> None:
        self._config = config

    def list_photos(self, category: PhotoCategory) -> list[PhotoRef]:
        directory = self._dir_for(category)
        if not directory.is_dir():
            return []
        paths = sorted(p for p in directory.iterdir() if p.suffix.lower() in _IMAGE_EXTENSIONS)
        return [PhotoRef(adapter="local", location=str(p), category=category) for p in paths]

    def fetch_photo(self, ref: PhotoRef) -> bytes:
        return Path(ref.location).read_bytes()

    def _dir_for(self, category: PhotoCategory) -> Path:
        return self._config.win_dir if category == "win" else self._config.loss_dir


def pick_random_photo(source: PhotoSource, category: PhotoCategory) -> PhotoRef | None:
    """Return a random photo reference for *category*, or None if empty."""
    refs = source.list_photos(category)
    return random.choice(refs) if refs else None
