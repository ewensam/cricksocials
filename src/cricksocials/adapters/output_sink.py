"""OutputSink protocol and built-in implementations.

Phase 8 will implement LocalFolderOutputSink.
Phase 13 will implement GoogleDriveOutputSink.
"""

from __future__ import annotations

# TODO (Phase 8): Define PostDraft dataclass (image_bytes, caption, match_id, date, team)
#
# TODO (Phase 8): Define OutputSink Protocol:
#   def write_post(self, draft: PostDraft) -> str: ...  # returns location string
#
# TODO (Phase 8): Implement LocalFolderOutputSink
#   Writes image + caption text to ./drafts/YYYY-MM-DD/<team>/ directory.
#
# TODO (Phase 13): Implement GoogleDriveOutputSink (optional dep: gdrive extra)
