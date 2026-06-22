"""Tests for the processed-match state tracker (Phase 9)."""

from __future__ import annotations

from pathlib import Path

from cricksocials.state import StateStore


class TestStateStore:
    def test_load_missing_file_starts_empty(self, tmp_path: Path) -> None:
        store = StateStore.load(tmp_path / "processed_matches.json")
        assert store.is_processed("123") is False

    def test_mark_processed_then_check(self, tmp_path: Path) -> None:
        store = StateStore.load(tmp_path / "processed_matches.json")
        store.mark_processed("123")
        assert store.is_processed("123") is True
        assert store.is_processed("456") is False

    def test_save_then_reload_persists_state(self, tmp_path: Path) -> None:
        path = tmp_path / "state" / "processed_matches.json"
        store = StateStore.load(path)
        store.mark_processed("123", metadata={"team": "1st XI"})
        store.save()

        reloaded = StateStore.load(path)
        assert reloaded.is_processed("123") is True
        assert reloaded.is_processed("999") is False

    def test_save_creates_parent_directory(self, tmp_path: Path) -> None:
        path = tmp_path / "nested" / "dir" / "processed_matches.json"
        store = StateStore.load(path)
        store.mark_processed("1")
        store.save()
        assert path.is_file()

    def test_save_does_not_leave_temp_files_behind(self, tmp_path: Path) -> None:
        path = tmp_path / "processed_matches.json"
        store = StateStore.load(path)
        store.mark_processed("1")
        store.save()

        leftover = [p for p in tmp_path.iterdir() if p.name != "processed_matches.json"]
        assert leftover == []

    def test_save_overwrites_existing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "processed_matches.json"
        store = StateStore.load(path)
        store.mark_processed("1")
        store.save()

        store2 = StateStore.load(path)
        store2.mark_processed("2")
        store2.save()

        reloaded = StateStore.load(path)
        assert reloaded.is_processed("1") is True
        assert reloaded.is_processed("2") is True
