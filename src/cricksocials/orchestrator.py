"""Pipeline orchestrator — wires all components together (Phase 10)."""

from __future__ import annotations

from dataclasses import dataclass, field

from cricksocials.adapters.output_sink import LocalFolderOutputSink, PostDraft
from cricksocials.adapters.photo_source import (
    LocalFolderPhotoSource,
    PhotoCategory,
    pick_random_photo,
)
from cricksocials.captions import generate_caption
from cricksocials.config import Config
from cricksocials.image_gen import compose_post_image
from cricksocials.parser import parse_match_page
from cricksocials.scraper import fetch_match_page, list_recent_results
from cricksocials.state import StateStore


@dataclass
class ProcessedMatch:
    match_id: str
    team: str
    location: str  # empty string when dry_run is True


@dataclass
class RunResult:
    processed: list[ProcessedMatch] = field(default_factory=list)
    skipped_match_ids: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)  # (match_id, message)


def run_pipeline(config: Config, dry_run: bool = False, match_id: str | None = None) -> RunResult:
    """Fetch new matches, render post images/captions, and write drafts.

    Note: Play Cricket's club-wide match listing doesn't expose which team
    played each match, so every match is currently attributed to the first
    configured team (`config.teams[0]`). Per-team attribution is future work.
    """
    state = StateStore.load(config.state.path)
    photo_source = LocalFolderPhotoSource(config.photos.local)
    output_sink = LocalFolderOutputSink(config.output.local)
    team_name = config.teams[0].name

    if match_id is not None:
        match_ids = [match_id]
    else:
        refs = list_recent_results(config.club.play_cricket_subdomain, config.scraping)
        match_ids = [ref.match_id for ref in refs]

    result = RunResult()

    for mid in match_ids:
        if match_id is None and state.is_processed(mid):
            result.skipped_match_ids.append(mid)
            continue

        try:
            _process_one_match(
                mid, team_name, config, state, output_sink, photo_source, dry_run, result
            )
        except Exception as exc:
            result.errors.append((mid, str(exc)))

    if not dry_run:
        state.save()

    return result


def _process_one_match(
    mid: str,
    team_name: str,
    config: Config,
    state: StateStore,
    output_sink: LocalFolderOutputSink,
    photo_source: LocalFolderPhotoSource,
    dry_run: bool,
    result: RunResult,
) -> None:
    html = fetch_match_page(config.club.play_cricket_subdomain, mid, config.scraping)
    match = parse_match_page(html)

    category: PhotoCategory = "win" if match.result_for_home_club == "win" else "loss"
    photo_ref = pick_random_photo(photo_source, category)
    if photo_ref is None:
        raise RuntimeError(f"No photos available for category '{category}'")
    photo_bytes = photo_source.fetch_photo(photo_ref)

    image_bytes = compose_post_image(match, photo_bytes, config)
    caption = generate_caption(match, team_name, config)

    location = ""
    if not dry_run:
        draft = PostDraft(
            image_bytes=image_bytes,
            caption=caption,
            match_id=match.match_id,
            date=match.date,
            team=team_name,
        )
        location = output_sink.write_post(draft)
        state.mark_processed(match.match_id, {"team": team_name, "date": str(match.date)})

    result.processed.append(
        ProcessedMatch(match_id=match.match_id, team=team_name, location=location)
    )
