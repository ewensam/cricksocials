"""Smoke tests for the CLI skeleton (Phase 0)."""

from click.testing import CliRunner

from cricksocials.cli import cli


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.output
    assert "validate" in result.output
    assert "preview" in result.output
    assert "list-recent" in result.output


def test_run_stub() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0
    assert "stub" in result.output


def test_run_dry_run_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--dry-run"])
    assert result.exit_code == 0
    assert "dry_run=True" in result.output


def test_run_match_id_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--match-id", "7069988"])
    assert result.exit_code == 0
    assert "7069988" in result.output


def test_validate_stub() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["validate"])
    assert result.exit_code == 0
    assert "stub" in result.output


def test_preview_stub() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["preview"])
    assert result.exit_code == 0
    assert "stub" in result.output


def test_list_recent_stub() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["list-recent"])
    assert result.exit_code == 0
    assert "stub" in result.output


def test_list_recent_limit_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["list-recent", "--limit", "5"])
    assert result.exit_code == 0
    assert "limit=5" in result.output


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
