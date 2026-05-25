"""Caption template renderer.

Phase 7 will implement the full template + random selection logic.
"""

from __future__ import annotations

# TODO (Phase 7): Implement generate_caption(match_result, config) -> str
#   - Load win_captions.txt or loss_captions.txt from config.captions.template_dir
#   - Select a random template line
#   - Substitute placeholders: {team}, {score}, {batting_highlight}, {bowling_highlight}, etc.
#   - Append configured hashtags
