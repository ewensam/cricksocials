"""Pillow-based image compositor.

Phase 6 will implement the full image generation logic.
"""

from __future__ import annotations

# TODO (Phase 6): Implement compose_post_image(match_result, photo_bytes, config) -> bytes
#   - Load background photo
#   - Apply semi-transparent overlay (colour from config, opacity from config)
#   - Composite logo (top-left or configured position)
#   - Render result text, score line, and performer highlights
#   - Return PNG bytes
#
# TODO (Phase 6): Implement compose_preview_image(config) -> bytes
#   Same pipeline with dummy/placeholder data for the `preview` CLI command.
