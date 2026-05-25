"""Pipeline orchestrator — wires all components together.

Phase 10 will implement the full end-to-end pipeline.
"""

from __future__ import annotations

# TODO (Phase 10): Implement run_pipeline(config, dry_run, match_id) -> RunResult
#   1. Load state
#   2. Fetch recent matches via scraper (or single match if match_id provided)
#   3. Skip already-processed matches (unless match_id forces reprocess)
#   4. For each new match:
#      a. Parse HTML → MatchResult
#      b. Select stats highlights
#      c. Fetch photo via PhotoSource adapter
#      d. Compose image
#      e. Generate caption
#      f. Write post via OutputSink adapter  (skipped if dry_run)
#      g. Mark as processed in state
#   5. Save state
#   6. Return summary
