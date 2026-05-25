"""HTTP fetcher for Play Cricket match pages.

Phase 3 will implement the full scraping logic, including a cloudscraper
fallback for bot-detection avoidance.
"""

from __future__ import annotations

# TODO (Phase 3): Implement fetch_match_page(subdomain, match_id, config) -> str
#   - Primary: requests with configured User-Agent and rate limiting
#   - Fallback: cloudscraper if primary returns a 403/captcha response
#
# TODO (Phase 3): Implement list_recent_matches(subdomain, team_id, config) -> list[MatchRef]
