"""Tests for the CLI commands (Phases 0 and 11)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from PIL import Image

from cricksocials.cli import cli

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_HTML = (REPO_ROOT / "tests" / "fixtures" / "match_7303496.html").read_text(
    encoding="utf-8"
)


def _sample_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (640, 480), (10, 20, 30))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    win_dir = tmp_path / "photos" / "win"
    loss_dir = tmp_path / "photos" / "loss"
    win_dir.mkdir(parents=True)
    loss_dir.mkdir(parents=True)
    (win_dir / "sample.jpg").write_bytes(_sample_jpeg_bytes())
    (loss_dir / "sample.jpg").write_bytes(_sample_jpeg_bytes())

    config_data = {
        "club": {
            "name": "Bridestowe and Belstone CC",
            "short_name": "B&B",
            "play_cricket_subdomain": "bridestoweandbelstone",
        },
        "teams": [{"name": "1st XI", "identifier": "1st"}],
        "branding": {
            "logo_path": str(REPO_ROOT / "assets" / "logo.png"),
            "fonts": {
                "bold": str(REPO_ROOT / "assets" / "fonts" / "Montserrat-Bold.ttf"),
                "regular": str(REPO_ROOT / "assets" / "fonts" / "Montserrat-Regular.ttf"),
            },
        },
        "photos": {
            "adapter": "local",
            "local": {"win_dir": str(win_dir), "loss_dir": str(loss_dir)},
        },
        "output": {
            "adapter": "local",
            "local": {"drafts_dir": str(tmp_path / "drafts")},
        },
        "captions": {"template_dir": str(REPO_ROOT / "templates")},
        "state": {"path": str(tmp_path / "state" / "processed_matches.json")},
    }

    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config_data), encoding="utf-8")
    return path


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.output
    assert "validate" in result.output
    assert "preview" in result.output
    assert "list-recent" in result.output


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_missing_config_file_fails_clearly() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--config", "does-not-exist.yaml", "validate"])
    assert result.exit_code != 0
    assert "does-not-exist.yaml" in result.output


class TestRun:
    def test_force_processes_match(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "cricksocials.orchestrator.fetch_match_page",
            lambda subdomain, match_id, config: FIXTURE_HTML,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--config", str(config_path), "run", "--match-id", "7303496"]
        )
        assert result.exit_code == 0
        assert "Processed match 7303496" in result.output
        assert "1 processed" in result.output

    def test_dry_run_flag(self, config_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "cricksocials.orchestrator.fetch_match_page",
            lambda subdomain, match_id, config: FIXTURE_HTML,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--config", str(config_path), "run", "--dry-run", "--match-id", "7303496"]
        )
        assert result.exit_code == 0
        assert "(dry run, not written)" in result.output


class TestValidate:
    def test_passes_with_complete_config(self, config_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--config", str(config_path), "validate"])
        assert result.exit_code == 0
        assert "All checks passed." in result.output
        assert "[OK]" in result.output
        assert "[FAIL]" not in result.output

    def test_fails_when_photos_missing(self, config_path: Path, tmp_path: Path) -> None:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        empty_dir = tmp_path / "no_photos"
        empty_dir.mkdir()
        data["photos"]["local"]["win_dir"] = str(empty_dir)
        config_path.write_text(yaml.safe_dump(data), encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(cli, ["--config", str(config_path), "validate"])
        assert result.exit_code != 0
        assert "[FAIL]" in result.output


class TestPreview:
    def test_writes_preview_image(self, config_path: Path, tmp_path: Path) -> None:
        output_path = tmp_path / "preview.png"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--config", str(config_path), "preview", "--output", str(output_path)]
        )
        assert result.exit_code == 0
        assert output_path.is_file()

        img = Image.open(output_path)
        assert img.format == "PNG"


class TestListRecent:
    def test_no_matches_found(self, config_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("cricksocials.cli.list_recent_results", lambda *a, **k: [])
        runner = CliRunner()
        result = runner.invoke(cli, ["--config", str(config_path), "list-recent"])
        assert result.exit_code == 0
        assert "No recent matches found." in result.output

    def test_shows_pending_and_processed_status(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from cricksocials.scraper import MatchRef
        from cricksocials.state import StateStore

        state = StateStore.load(_config_state_path(config_path))
        state.mark_processed("111")
        state.save()

        monkeypatch.setattr(
            "cricksocials.cli.list_recent_results",
            lambda *a, **k: [MatchRef(match_id="111"), MatchRef(match_id="222")],
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["--config", str(config_path), "list-recent"])
        assert result.exit_code == 0
        assert "111" in result.output and "[processed]" in result.output
        assert "222" in result.output and "[pending]" in result.output

    def test_limit_flag_is_passed_through(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict[str, int] = {}

        def fake_list_recent_results(subdomain: str, config: object, limit: int = 20) -> list:  # type: ignore[type-arg]
            captured["limit"] = limit
            return []

        monkeypatch.setattr("cricksocials.cli.list_recent_results", fake_list_recent_results)
        runner = CliRunner()
        runner.invoke(cli, ["--config", str(config_path), "list-recent", "--limit", "5"])
        assert captured["limit"] == 5


def _config_state_path(config_path: Path) -> Path:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return Path(data["state"]["path"])
