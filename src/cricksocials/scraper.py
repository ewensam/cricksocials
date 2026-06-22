"""HTTP fetcher for Play Cricket match pages (Phase 3).

Primary path: `requests` with the configured User-Agent and per-request
rate-limiting delay.

Fallback path: `cloudscraper`, activated automatically when the primary
request returns a 403 or 503 (Cloudflare bot-detection response).

Match page URL format:
  https://{subdomain}.play-cricket.com/website/results/{match_id}

Results listing URL format:
  https://{subdomain}.play-cricket.com/Matches
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import date, datetime

import requests

from cricksocials.config import ScrapingConfig

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class MatchRef:
    """Lightweight reference to a match found on the results listing page."""

    match_id: str
    match_date: date | None = None
    result_summary: str | None = None  # e.g. "WON BY 15 RUNS"


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def match_url(subdomain: str, match_id: str) -> str:
    """Build the URL for a single match result page."""
    return f"https://{subdomain}.play-cricket.com/website/results/{match_id}"


def matches_list_url(subdomain: str) -> str:
    """Build the URL for the club's fixtures-and-results listing page."""
    return f"https://{subdomain}.play-cricket.com/Matches"


# ---------------------------------------------------------------------------
# Core fetcher
# ---------------------------------------------------------------------------


def fetch_url(url: str, config: ScrapingConfig) -> str:
    """Fetch *url* and return the response body as a string.

    Uses `requests` as the primary client.  If the response status is 403 or
    503 and `config.use_cloudscraper_fallback` is True, retries with
    `cloudscraper` which handles Cloudflare JS-challenge pages.

    Raises:
        requests.HTTPError: on non-2xx after all retries.
    """
    headers = {"User-Agent": config.user_agent}

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code in (403, 503) and config.use_cloudscraper_fallback:
        import cloudscraper  # optional — only imported when needed

        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=30)

    response.raise_for_status()
    return response.text


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def fetch_match_page(subdomain: str, match_id: str, config: ScrapingConfig) -> str:
    """Fetch the HTML for a single match result page.

    Applies the configured rate-limiting delay before fetching.

    Args:
        subdomain: Play Cricket club subdomain, e.g. "bridestoweandbelstone".
        match_id:  Numeric match ID, e.g. "7303496".
        config:    Scraping configuration section from Config.

    Returns:
        HTML string of the match page.
    """
    time.sleep(config.request_delay_seconds)
    return fetch_url(match_url(subdomain, match_id), config)


def list_recent_results(
    subdomain: str,
    config: ScrapingConfig,
    limit: int = 20,
) -> list[MatchRef]:
    """Scrape the club's /Matches page and return recent result references.

    Looks for `<a href="/website/results/{id}">` links (excluding /print
    variants).  Returns up to *limit* matches, most recent first as they
    appear in the page.

    Returns an empty list (rather than raising) if the page structure is
    unexpected — the orchestrator handles missing data gracefully.

    Args:
        subdomain: Play Cricket club subdomain.
        config:    Scraping configuration section.
        limit:     Maximum number of matches to return.

    Returns:
        List of MatchRef ordered as they appear on the page.
    """
    time.sleep(config.request_delay_seconds)
    html = fetch_url(matches_list_url(subdomain), config)

    from bs4 import BeautifulSoup  # local import to avoid circular risk

    soup = BeautifulSoup(html, "lxml")

    seen: set[str] = set()
    refs: list[MatchRef] = []

    for a_tag in soup.find_all("a", href=re.compile(r"^/website/results/\d+$")):
        href = str(a_tag["href"])
        m = re.search(r"/website/results/(\d+)$", href)
        if not m:
            continue
        match_id = m.group(1)
        if match_id in seen:
            continue
        seen.add(match_id)

        # Try to extract a date from surrounding text
        match_date = _extract_nearby_date(a_tag)

        refs.append(MatchRef(match_id=match_id, match_date=match_date))
        if len(refs) >= limit:
            break

    return refs


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_nearby_date(tag: object) -> date | None:
    """Attempt to parse a date from the text content near *tag*."""
    # Walk up to the parent row/cell and look for a date pattern
    from bs4 import Tag

    node = tag
    for _ in range(4):  # look up to 4 levels of ancestor
        if not isinstance(node, Tag):
            break
        text = node.get_text(separator=" ", strip=True)
        # Look for patterns like "09 May 2026" or "09/05/2026"
        m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})\b", text)
        if m:
            try:
                raw = f"{m.group(1)} {m.group(2).capitalize()} {m.group(3)}"
                return datetime.strptime(raw, "%d %b %Y").date()
            except ValueError:
                pass
        m2 = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", text)
        if m2:
            try:
                return datetime(int(m2.group(3)), int(m2.group(2)), int(m2.group(1))).date()
            except ValueError:
                pass
        node = getattr(node, "parent", None)
    return None
