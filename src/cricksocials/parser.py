"""HTML → MatchResult parser for Play Cricket match pages (Phase 2).

Parses the HTML saved from URLs like:
  https://{subdomain}.play-cricket.com/website/results/{match_id}

Key structural landmarks in the HTML:
  - `.leaguedetail-right`       → date and time
  - `.main-header-lg`           → desktop header (team names, scores, result)
  - `.match-ttl`                → home club name + result class (win-cb-name etc.)
  - `div.info.mdont`            → result text ("WON BY 15 RUNS")
  - `nvplay[match-id]`          → authoritative match ID
  - `ul.nav-tabs a[href^=#innings]` → innings tab labels (= batting team names)
  - `div#innings{id}`           → per-innings scorecard
  - `table.standm`              → batting table inside innings div
  - `table.bowler-detail`       → bowling table inside innings div
  - `div.alert-info-1`          → extras and total line
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

from bs4 import BeautifulSoup, Tag


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class BattingPerformance:
    name: str
    runs: int
    balls: int
    fours: int
    sixes: int
    not_out: bool
    how_out: str  # normalised text, e.g. "c Zimmerman b Worth"


@dataclass
class BowlingPerformance:
    name: str
    overs: str   # cricket notation: "7" or "7.2" (7 overs 2 balls)
    maidens: int
    runs: int
    wickets: int
    wides: int
    no_balls: int


@dataclass
class InningsData:
    team_name: str
    total_runs: int
    wickets_down: int   # wickets that fell; 10 = all out
    overs: str          # cricket notation string, e.g. "48.1"
    all_out: bool
    extras: int
    batting: list[BattingPerformance] = field(default_factory=list)
    bowling: list[BowlingPerformance] = field(default_factory=list)


ResultOutcome = Literal["win", "loss", "draw", "tie", "abandoned", "unknown"]


@dataclass
class MatchResult:
    match_id: str
    date: date
    home_club: str          # Club whose Play Cricket page this is
    ground: str | None
    result_text: str        # Raw text: "WON BY 15 RUNS"
    result_for_home_club: ResultOutcome
    innings: list[InningsData]  # ordered by batting order (index 0 = first innings)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_match_page(html: str) -> MatchResult:
    """Parse a Play Cricket match result page.

    Args:
        html: Raw HTML from a Play Cricket match result URL.

    Returns:
        MatchResult populated from the page.

    Raises:
        ValueError: if critical sections of the page cannot be found.
    """
    soup = BeautifulSoup(html, "lxml")

    match_id = _parse_match_id(soup)
    match_date = _parse_date(soup)
    ground = _parse_ground(soup)
    home_club, result_text, result_outcome = _parse_result(soup)
    innings = _parse_innings(soup)

    return MatchResult(
        match_id=match_id,
        date=match_date,
        home_club=home_club,
        ground=ground,
        result_text=result_text,
        result_for_home_club=result_outcome,
        innings=innings,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_match_id(soup: BeautifulSoup) -> str:
    """Extract match ID from the nvplay widget or the print link."""
    nvplay = soup.find("nvplay", attrs={"match-id": True})
    if nvplay:
        return str(nvplay["match-id"])  # type: ignore[index]

    # Fallback: parse from /website/results/{id}/print
    print_link = soup.find("a", href=re.compile(r"/website/results/(\d+)/print"))
    if print_link:
        m = re.search(r"/website/results/(\d+)/print", str(print_link["href"]))
        if m:
            return m.group(1)

    raise ValueError("Could not extract match ID from page")


def _parse_date(soup: BeautifulSoup) -> date:
    """Extract match date from the leaguedetail-right div."""
    detail_div = soup.find(class_="leaguedetail-right")
    if not detail_div:
        raise ValueError("Could not find leaguedetail-right div for date parsing")

    raw = detail_div.get_text(separator=" ", strip=True)
    # Div text is like "09 MAY 2026 @ 12:30 | Filham Park | ..."
    date_part = raw.split("@")[0].strip()  # "09 MAY 2026"
    # Normalise month capitalisation for strptime
    tokens = date_part.split()
    if len(tokens) >= 3:
        tokens[1] = tokens[1].capitalize()  # "MAY" → "May"
        date_part = " ".join(tokens[:3])
    try:
        return datetime.strptime(date_part, "%d %b %Y").date()
    except ValueError as exc:
        raise ValueError(f"Could not parse date from '{date_part}'") from exc


def _parse_ground(soup: BeautifulSoup) -> str | None:
    """Extract ground name from the location span."""
    loc_span = soup.find("span", class_="location")
    if loc_span:
        a_tag = loc_span.find("a")
        if a_tag:
            return a_tag.get_text(strip=True)
    return None


def _parse_result(soup: BeautifulSoup) -> tuple[str, str, ResultOutcome]:
    """Return (home_club_name, result_text, outcome)."""
    # The match-ttl paragraph contains the home club name and a class that
    # indicates the result outcome from the home club's perspective.
    match_ttl = soup.find(class_="match-ttl")
    if not match_ttl:
        raise ValueError("Could not find .match-ttl element")

    home_club = match_ttl.get_text(strip=True)
    classes = match_ttl.get("class", [])
    class_str = " ".join(classes)

    # Determine outcome from CSS class (most reliable)
    if "win-cb-name" in class_str:
        outcome: ResultOutcome = "win"
    elif "loss-cb-name" in class_str:
        outcome = "loss"
    elif "draw-cb-name" in class_str:
        outcome = "draw"
    elif "tie-cb-name" in class_str:
        outcome = "tie"
    elif "abandoned-cb-name" in class_str:
        outcome = "abandoned"
    else:
        outcome = "unknown"

    # Get result text from the first info/mdont div
    info_div = soup.find("div", class_="info")
    if info_div:
        result_text = info_div.get_text(separator=" ", strip=True)
        result_text = " ".join(result_text.split())  # collapse whitespace
    else:
        result_text = ""

    # Fallback outcome detection from result text
    if outcome == "unknown" and result_text:
        upper = result_text.upper()
        if upper.startswith("WON"):
            outcome = "win"
        elif upper.startswith("LOST"):
            outcome = "loss"
        elif "DRAWN" in upper or "DRAW" in upper:
            outcome = "draw"
        elif "ABANDONED" in upper:
            outcome = "abandoned"
        elif "TIE" in upper:
            outcome = "tie"

    return home_club, result_text, outcome


def _parse_innings(soup: BeautifulSoup) -> list[InningsData]:
    """Parse all innings tabs in order."""
    # There can be multiple ul.nav-tabs on the page (scorecard tabs, innings tabs).
    # Find the one whose anchors link to #innings... divs.
    tab_nav = None
    for ul in soup.find_all("ul", class_="nav-tabs"):
        if ul.find("a", href=re.compile(r"^#innings")):
            tab_nav = ul
            break
    if not tab_nav:
        return []

    innings_list: list[InningsData] = []

    for tab_a in tab_nav.find_all("a", href=re.compile(r"^#innings")):
        innings_id = tab_a["href"].lstrip("#")  # e.g. "innings8398833"
        team_name = tab_a.get_text(strip=True)

        pane = soup.find(id=innings_id)
        if not pane:
            continue

        batting = _parse_batting_table(pane)
        bowling = _parse_bowling_table(pane)
        total_runs, wickets_down, overs, all_out, extras = _parse_innings_totals(pane)

        innings_list.append(InningsData(
            team_name=team_name,
            total_runs=total_runs,
            wickets_down=wickets_down,
            overs=overs,
            all_out=all_out,
            extras=extras,
            batting=batting,
            bowling=bowling,
        ))

    return innings_list


def _parse_batting_table(pane: Tag) -> list[BattingPerformance]:
    """Parse the batting scorecard table from an innings pane."""
    table = pane.find("table", class_="standm")
    if not table:
        return []

    performances: list[BattingPerformance] = []
    tbody = table.find("tbody")
    if not tbody:
        return []

    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        # Player name: in the .bts div inside the first cell
        bts_div = cells[0].find("div", class_="bts")
        if not bts_div:
            continue
        name_a = bts_div.find("a")
        if not name_a:
            continue
        name = name_a.get_text(strip=True)

        # How out: from the .m-player div
        m_player = cells[0].find("div", class_="m-player")
        if m_player:
            raw_how = m_player.get_text(separator=" ")
            how_out = " ".join(raw_how.replace("\xa0", " ").split()).strip()
        else:
            how_out = ""

        # Not-out marker: either "not out" in how_out or a .howout span
        not_out = bool(cells[1].find("span", class_="howout")) if len(cells) > 1 else False
        if not not_out and "not out" in how_out.lower():
            not_out = True

        # Stats: runs (bold in 4th sTD cell), balls, 4s, 6s
        stds = [c for c in cells if "sTD" in (c.get("class") or [])]
        if len(stds) < 4:
            continue

        try:
            runs_strong = stds[0].find("strong")
            runs = int(runs_strong.get_text(strip=True) if runs_strong else stds[0].get_text(strip=True))
            balls = int(stds[1].get_text(strip=True) or 0)
            fours = int(stds[2].get_text(strip=True) or 0)
            sixes = int(stds[3].get_text(strip=True) or 0)
        except (ValueError, AttributeError):
            continue

        performances.append(BattingPerformance(
            name=name,
            runs=runs,
            balls=balls,
            fours=fours,
            sixes=sixes,
            not_out=not_out,
            how_out=how_out,
        ))

    return performances


def _parse_bowling_table(pane: Tag) -> list[BowlingPerformance]:
    """Parse the bowling scorecard table from an innings pane."""
    table = pane.find("table", class_="bowler-detail")
    if not table:
        return []

    performances: list[BowlingPerformance] = []
    tbody = table.find("tbody")
    if not tbody:
        return []

    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 7:
            continue

        name_a = cells[0].find("a")
        name = name_a.get_text(strip=True) if name_a else cells[0].get_text(strip=True)

        try:
            overs = cells[1].get_text(strip=True)
            maidens = int(cells[2].get_text(strip=True) or 0)
            runs = int(cells[3].get_text(strip=True) or 0)
            wickets = int(cells[4].get_text(strip=True) or 0)
            wides = int(cells[5].get_text(strip=True) or 0)
            no_balls = int(cells[6].get_text(strip=True) or 0)
        except (ValueError, IndexError):
            continue

        performances.append(BowlingPerformance(
            name=name,
            overs=overs,
            maidens=maidens,
            runs=runs,
            wickets=wickets,
            wides=wides,
            no_balls=no_balls,
        ))

    return performances


def _parse_innings_totals(pane: Tag) -> tuple[int, int, str, bool, int]:
    """Return (total_runs, wickets_down, overs, all_out, extras).

    Parses the alert-info div that contains lines like:
      EXTRAS: 12 (2lb, 10w)   Total: 146 ( 48.1 Overs, All Out )
    """
    alert = pane.find("div", class_="alert-info-1")
    if not alert:
        return 0, 0, "0", False, 0

    text = alert.get_text(separator=" ", strip=True)
    text = " ".join(text.split())  # normalise whitespace

    # Extract extras
    extras = 0
    extras_m = re.search(r"EXTRAS:\s*(\d+)", text, re.IGNORECASE)
    if extras_m:
        extras = int(extras_m.group(1))

    # Extract total: "Total: 146 ( 48.1 Overs, All Out )"
    # or "Total: 146 ( 48.1 Overs, 5 wickets )"
    total_runs = 0
    overs = "0"
    wickets_down = 0
    all_out = False

    total_m = re.search(
        r"Total:\s*(\d+)\s*\(\s*([\d.]+)\s*Overs[,\s]*([\w\s]+)\)",
        text,
        re.IGNORECASE,
    )
    if total_m:
        total_runs = int(total_m.group(1))
        overs = total_m.group(2)
        condition = total_m.group(3).strip().lower()
        if "all out" in condition:
            all_out = True
            wickets_down = 10
        else:
            # Try to extract wicket count from "5 wickets" or "wicket 5"
            wkt_m = re.search(r"(\d+)", condition)
            wickets_down = int(wkt_m.group(1)) if wkt_m else 0

    return total_runs, wickets_down, overs, all_out, extras
