"""Tests for scraper.py — Phase 3.

Unit tests cover URL construction and the date-extraction helper.

Integration tests (marked with @pytest.mark.integration) actually hit the
Play Cricket website — skipped by default in CI, run manually with:

    pytest -m integration

To add an integration marker to pytest, ensure conftest.py is in place (see
tests/conftest.py).
"""

from __future__ import annotations

import pytest

from cricksocials.scraper import match_url, matches_list_url

# ---------------------------------------------------------------------------
# URL construction (no network)
# ---------------------------------------------------------------------------


class TestUrlHelpers:
    def test_match_url(self) -> None:
        url = match_url("bridestoweandbelstone", "7303496")
        assert url == "https://bridestoweandbelstone.play-cricket.com/website/results/7303496"

    def test_match_url_different_club(self) -> None:
        url = match_url("stithians", "9999999")
        assert url == "https://stithians.play-cricket.com/website/results/9999999"

    def test_matches_list_url(self) -> None:
        url = matches_list_url("bridestoweandbelstone")
        assert url == "https://bridestoweandbelstone.play-cricket.com/Matches"


# ---------------------------------------------------------------------------
# Integration tests — require network access, skipped in CI
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFetchMatchPageLive:
    """Hits the real Play Cricket website.  Run with: pytest -m integration"""

    def test_fetch_known_match(self) -> None:
        from cricksocials.config import ScrapingConfig
        from cricksocials.scraper import fetch_match_page

        config = ScrapingConfig(request_delay_seconds=0)
        html = fetch_match_page("bridestoweandbelstone", "7303496", config)

        assert "Bridestowe" in html
        assert "Ivybridge" in html
        assert "7303496" in html

    def test_parsed_live_match_matches_fixture(self) -> None:
        """Verify the live page still parses to the same result as the fixture."""
        from datetime import date

        from cricksocials.config import ScrapingConfig
        from cricksocials.parser import parse_match_page
        from cricksocials.scraper import fetch_match_page

        config = ScrapingConfig(request_delay_seconds=0)
        html = fetch_match_page("bridestoweandbelstone", "7303496", config)
        result = parse_match_page(html)

        assert result.match_id == "7303496"
        assert result.date == date(2026, 5, 9)
        assert result.result_for_home_club == "win"
