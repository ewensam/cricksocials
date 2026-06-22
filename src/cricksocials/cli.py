"""CrickSocials CLI — entry point for all commands."""

from __future__ import annotations

from pathlib import Path

import click

from cricksocials.adapters.photo_source import LocalFolderPhotoSource
from cricksocials.config import Config, load_config
from cricksocials.image_gen import compose_preview_image
from cricksocials.orchestrator import run_pipeline
from cricksocials.scraper import list_recent_results
from cricksocials.state import StateStore


def _load_config_or_exit(ctx: click.Context) -> Config:
    config_path = ctx.obj["config"]
    try:
        return load_config(config_path)
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc


@click.group()
@click.version_option(package_name="cricksocials")
@click.option(
    "--config",
    default="config.yaml",
    show_default=True,
    metavar="PATH",
    help="Path to club config YAML file.",
)
@click.pass_context
def cli(ctx: click.Context, config: str) -> None:
    """CrickSocials — automated match result posts for village cricket clubs.

    Run 'cricksocials COMMAND --help' for details on each command.
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--dry-run", is_flag=True, help="Process matches but don't write any output.")
@click.option("--match-id", default=None, metavar="ID", help="Force-process a single match by ID.")
@click.pass_context
def run(ctx: click.Context, dry_run: bool, match_id: str | None) -> None:
    """Process new matches and write social media drafts.

    Fetches recent matches from Play Cricket, generates graphics and captions
    for any that haven't been processed yet, and writes output via the
    configured OutputSink adapter.

    Use --dry-run to see what would be processed without writing anything.
    Use --match-id to force-process a specific match regardless of state.
    """
    config = _load_config_or_exit(ctx)
    result = run_pipeline(config, dry_run=dry_run, match_id=match_id)

    for processed in result.processed:
        where = processed.location or "(dry run, not written)"
        click.echo(f"Processed match {processed.match_id} ({processed.team}) -> {where}")
    for skipped_id in result.skipped_match_ids:
        click.echo(f"Skipped already-processed match {skipped_id}")
    for failed_id, message in result.errors:
        click.echo(f"Error processing match {failed_id}: {message}", err=True)

    click.echo(
        f"Done: {len(result.processed)} processed, "
        f"{len(result.skipped_match_ids)} skipped, {len(result.errors)} errors."
    )
    if result.errors:
        ctx.exit(1)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@cli.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Check config, paths, and assets.

    Validates the config file structure, verifies that logo and font files
    exist, and checks that photo directories are populated.

    Use this after editing config.yaml to confirm everything is wired up
    before your first real run.
    """
    config = _load_config_or_exit(ctx)

    photo_source = LocalFolderPhotoSource(config.photos.local)
    win_count = len(photo_source.list_photos("win"))
    loss_count = len(photo_source.list_photos("loss"))

    checks = [
        ("Logo file exists", config.branding.logo_path.is_file(), str(config.branding.logo_path)),
        ("Bold font exists", config.branding.fonts.bold.is_file(), str(config.branding.fonts.bold)),
        (
            "Regular font exists",
            config.branding.fonts.regular.is_file(),
            str(config.branding.fonts.regular),
        ),
        (
            f"Win photos present ({win_count} found)",
            win_count > 0,
            str(config.photos.local.win_dir),
        ),
        (
            f"Loss photos present ({loss_count} found)",
            loss_count > 0,
            str(config.photos.local.loss_dir),
        ),
    ]

    all_ok = True
    for label, ok, detail in checks:
        click.echo(f"[{'OK' if ok else 'FAIL'}] {label} ({detail})")
        all_ok = all_ok and ok

    if not all_ok:
        raise click.ClickException("One or more checks failed — see above.")
    click.echo("All checks passed.")


# ---------------------------------------------------------------------------
# preview
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--output",
    default="preview.png",
    show_default=True,
    metavar="PATH",
    help="Where to write the preview image.",
)
@click.pass_context
def preview(ctx: click.Context, output: str) -> None:
    """Generate a sample post image using dummy match data.

    Renders the full image template with placeholder statistics so you can
    check branding, fonts, and layout before a real match result is available.

    The output image is written to --output (default: preview.png).
    """
    config = _load_config_or_exit(ctx)
    png_bytes = compose_preview_image(config)
    Path(output).write_bytes(png_bytes)
    click.echo(f"Wrote preview image to {output}")


# ---------------------------------------------------------------------------
# list-recent
# ---------------------------------------------------------------------------


@cli.command("list-recent")
@click.option(
    "--limit",
    default=10,
    show_default=True,
    metavar="N",
    help="Maximum number of matches to show.",
)
@click.pass_context
def list_recent(ctx: click.Context, limit: int) -> None:
    """Show recent matches from Play Cricket.

    Lists the most recent matches across all configured teams, indicating
    which ones have already been processed and which are pending.

    Useful for auditing state or deciding which match to force-process
    with 'cricksocials run --match-id ID'.
    """
    config = _load_config_or_exit(ctx)
    state = StateStore.load(config.state.path)
    refs = list_recent_results(config.club.play_cricket_subdomain, config.scraping, limit=limit)

    if not refs:
        click.echo("No recent matches found.")
        return

    for ref in refs:
        status = "processed" if state.is_processed(ref.match_id) else "pending"
        date_str = ref.match_date.isoformat() if ref.match_date else "unknown date"
        click.echo(f"{ref.match_id}  {date_str}  [{status}]  {ref.result_summary or ''}")
