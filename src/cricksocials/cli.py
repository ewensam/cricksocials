"""CrickSocials CLI — entry point for all commands."""

from __future__ import annotations

import click


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
    config_path = ctx.obj["config"]
    click.echo(f"[stub] run  config={config_path}  dry_run={dry_run}  match_id={match_id}")
    click.echo("Not implemented yet — coming in Phase 10.")


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@cli.command()
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Check config, paths, and connectivity.

    Validates the config file structure, verifies that logo and font files
    exist, checks that photo directories are populated, and (optionally) does
    a connectivity probe to Play Cricket.

    Use this after editing config.yaml to confirm everything is wired up
    before your first real run.
    """
    config_path = ctx.obj["config"]
    click.echo(f"[stub] validate  config={config_path}")
    click.echo("Not implemented yet — coming in Phase 11.")


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
    config_path = ctx.obj["config"]
    click.echo(f"[stub] preview  config={config_path}  output={output}")
    click.echo("Not implemented yet — coming in Phase 11.")


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
    config_path = ctx.obj["config"]
    click.echo(f"[stub] list-recent  config={config_path}  limit={limit}")
    click.echo("Not implemented yet — coming in Phase 3+.")
