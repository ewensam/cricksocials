"""PhotoSource protocol and built-in implementations.

Phase 5 will implement LocalFolderPhotoSource.
Phase 13 will implement GoogleDrivePhotoSource.
"""

from __future__ import annotations


# TODO (Phase 5): Define PhotoRef dataclass (adapter, path/id, category)
#
# TODO (Phase 5): Define PhotoSource Protocol:
#   def list_photos(self, category: Literal["win", "loss"]) -> list[PhotoRef]: ...
#   def fetch_photo(self, ref: PhotoRef) -> bytes: ...
#
# TODO (Phase 5): Implement LocalFolderPhotoSource
#   Reads from configured win_dir / loss_dir, returns a random photo on fetch.
#
# TODO (Phase 13): Implement GoogleDrivePhotoSource (optional dep: gdrive extra)
