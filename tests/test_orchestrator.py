"""End-to-end test for the pipeline orchestrator (Phase 10)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cricksocials.config import Config
from cricksocials.orchestrator import run_pipeline
from cricksocials.state import StateStore

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_HTML = (REPO_ROOT / "tests" / "fixtures" / "match_7303496.html").read_text(
    encoding="utf-8"
)


@pytest.fixture(autouse=True)
def _stub_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never hit the real Play Cricket site in this test module."""
    monkeypatch.setattr(
        "cricksocials.orchestrator.fetch_match_page",
        lambda subdomain, match_id, config: FIXTURE_HTML,
    )
    monkeypatch.setattr(
        "cricksocials.orchestrator.list_recent_results",
        lambda subdomain, config, limit=20: [],
    )


@pytest.fixture
def config(tmp_path: Path) -> Config:
    win_dir = tmp_path / "photos" / "win"
    loss_dir = tmp_path / "photos" / "loss"
    win_dir.mkdir(parents=True)
    loss_dir.mkdir(parents=True)
    (win_dir / "sample.jpg").write_bytes(_sample_jpeg_bytes())
    (loss_dir / "sample.jpg").write_bytes(_sample_jpeg_bytes())

    return Config.model_validate(
        {
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
    )


def _sample_jpeg_bytes() -> bytes:
    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (640, 480), (10, 20, 30))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestRunPipeline:
    def test_force_processes_match_and_writes_draft(self, config: Config) -> None:
        result = run_pipeline(config, dry_run=False, match_id="7303496")

        assert len(result.processed) == 1
        processed = result.processed[0]
        assert processed.match_id == "7303496"
        assert processed.team == "1st XI"
        assert Path(processed.location).is_dir()

        png_files = list(Path(processed.location).glob("*.png"))
        txt_files = list(Path(processed.location).glob("*.txt"))
        assert len(png_files) == 1
        assert len(txt_files) == 1
        assert txt_files[0].read_text(encoding="utf-8").strip() != ""

        state = StateStore.load(Path(config.state.path))
        assert state.is_processed("7303496") is True

    def test_dry_run_does_not_write_or_mark_processed(self, config: Config) -> None:
        result = run_pipeline(config, dry_run=True, match_id="7303496")

        assert len(result.processed) == 1
        assert result.processed[0].location == ""
        assert not Path(config.output.local.drafts_dir).exists()

        state = StateStore.load(Path(config.state.path))
        assert state.is_processed("7303496") is False

    def test_forced_reprocess_ignores_existing_state(self, config: Config) -> None:
        run_pipeline(config, dry_run=False, match_id="7303496")
        result = run_pipeline(config, dry_run=False, match_id="7303496")

        assert len(result.processed) == 1
        assert result.skipped_match_ids == []

    def test_no_photos_available_records_error_not_exception(
        self, config: Config, tmp_path: Path
    ) -> None:
        empty_dir = tmp_path / "empty_win"
        empty_dir.mkdir()
        config.photos.local.win_dir = empty_dir

        result = run_pipeline(config, dry_run=False, match_id="7303496")

        assert result.processed == []
        assert len(result.errors) == 1
        assert result.errors[0][0] == "7303496"
