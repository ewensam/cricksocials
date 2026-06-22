"""Tests for the local-folder photo source and output sink adapters (Phases 5+8)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from cricksocials.adapters.output_sink import LocalFolderOutputSink, PostDraft
from cricksocials.adapters.photo_source import (
    LocalFolderPhotoSource,
    PhotoRef,
    pick_random_photo,
)
from cricksocials.config import LocalOutputConfig, LocalPhotosConfig


@pytest.fixture
def photo_dirs(tmp_path: Path) -> LocalPhotosConfig:
    win_dir = tmp_path / "win"
    loss_dir = tmp_path / "loss"
    win_dir.mkdir()
    loss_dir.mkdir()

    (win_dir / "a.jpg").write_bytes(b"fake-jpg-a")
    (win_dir / "b.png").write_bytes(b"fake-png-b")
    (win_dir / "notes.txt").write_bytes(b"not a photo")
    (loss_dir / "c.jpeg").write_bytes(b"fake-jpeg-c")

    return LocalPhotosConfig(win_dir=win_dir, loss_dir=loss_dir)


class TestLocalFolderPhotoSource:
    def test_list_photos_filters_by_extension(self, photo_dirs: LocalPhotosConfig) -> None:
        source = LocalFolderPhotoSource(photo_dirs)
        refs = source.list_photos("win")
        names = sorted(Path(r.location).name for r in refs)
        assert names == ["a.jpg", "b.png"]
        assert all(r.category == "win" and r.adapter == "local" for r in refs)

    def test_list_photos_separates_categories(self, photo_dirs: LocalPhotosConfig) -> None:
        source = LocalFolderPhotoSource(photo_dirs)
        loss_refs = source.list_photos("loss")
        assert len(loss_refs) == 1
        assert Path(loss_refs[0].location).name == "c.jpeg"

    def test_list_photos_missing_dir_returns_empty(self, tmp_path: Path) -> None:
        config = LocalPhotosConfig(win_dir=tmp_path / "missing", loss_dir=tmp_path / "loss")
        source = LocalFolderPhotoSource(config)
        assert source.list_photos("win") == []

    def test_fetch_photo_reads_bytes(self, photo_dirs: LocalPhotosConfig) -> None:
        source = LocalFolderPhotoSource(photo_dirs)
        ref = PhotoRef(adapter="local", location=str(photo_dirs.win_dir / "a.jpg"), category="win")
        assert source.fetch_photo(ref) == b"fake-jpg-a"


class TestPickRandomPhoto:
    def test_returns_none_when_empty(self, tmp_path: Path) -> None:
        config = LocalPhotosConfig(win_dir=tmp_path / "missing", loss_dir=tmp_path / "loss")
        source = LocalFolderPhotoSource(config)
        assert pick_random_photo(source, "win") is None

    def test_returns_one_of_the_available_refs(self, photo_dirs: LocalPhotosConfig) -> None:
        source = LocalFolderPhotoSource(photo_dirs)
        ref = pick_random_photo(source, "win")
        assert ref is not None
        assert Path(ref.location).name in {"a.jpg", "b.png"}


class TestLocalFolderOutputSink:
    def test_write_post_creates_dated_team_dir_with_image_and_caption(
        self, tmp_path: Path
    ) -> None:
        config = LocalOutputConfig(drafts_dir=tmp_path / "drafts")
        sink = LocalFolderOutputSink(config)
        draft = PostDraft(
            image_bytes=b"fake-png-bytes",
            caption="Great win today!",
            match_id="7303496",
            date=date(2026, 5, 25),
            team="1st XI",
        )

        location = sink.write_post(draft)

        team_dir = tmp_path / "drafts" / "2026-05-25" / "1st XI"
        assert location == str(team_dir)
        assert (team_dir / "7303496.png").read_bytes() == b"fake-png-bytes"
        assert (team_dir / "7303496.txt").read_text(encoding="utf-8") == "Great win today!"

    def test_write_post_sanitises_unsafe_team_name(self, tmp_path: Path) -> None:
        config = LocalOutputConfig(drafts_dir=tmp_path / "drafts")
        sink = LocalFolderOutputSink(config)
        draft = PostDraft(
            image_bytes=b"x",
            caption="x",
            match_id="1",
            date=date(2026, 1, 1),
            team="Sunday XI / A",
        )

        location = sink.write_post(draft)

        assert Path(location).is_dir()
        assert "/" not in Path(location).name
