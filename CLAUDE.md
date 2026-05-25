# CLAUDE.md — CrickSocials project guidance

## Build workflow

- Follow the phases in `plan.md`. Complete one phase at a time.
- **After each phase: commit and push to `main` on `ewensam/cricksocials`.**
  - Commit message format: `feat: phase N — <short description>`
  - Example: `feat: phase 0 — project scaffold and CLI skeleton`
- Run `pytest` before every push; all tests must pass.

## Repo layout

```
src/cricksocials/    ← all source code (src layout, hatchling build)
tests/               ← pytest tests; fixtures go in tests/fixtures/
docs/                ← markdown documentation
templates/           ← caption templates (win_captions.txt, loss_captions.txt)
assets/              ← logo and fonts (clubs replace these)
photos/win|loss/     ← match photos (empty in repo, .gitkeep only)
examples/            ← reference deployments (B&B pilot goes here)
```

## Key files

- `plan.md` — full architecture and phase breakdown; refer to this
- `config.example.yaml` — annotated example config; keep in sync with Pydantic models
- `tests/fixtures/match_7303496.html` — real Play Cricket HTML for parser tests

## Conventions

- Python 3.11+, type-annotated, `from __future__ import annotations` at top of each module
- Pydantic v2 for all config/data models
- Click for CLI
- Adapters (PhotoSource, OutputSink) use `Protocol` — no inheritance required
- State is a plain JSON file — no databases
- All path handling via `pathlib.Path`
- Ruff for lint/format (`ruff check`, `ruff format`); mypy strict for type checking
- Test with `pytest`; use `click.testing.CliRunner` for CLI tests

## GitHub Actions

- `ci.yml` — runs on every push/PR: pytest + ruff + mypy on Python 3.11 & 3.12
- `match-day.yml` — scheduled workflow template for clubs to use

## Dependencies

Core deps in `pyproject.toml`. Google Drive is opt-in: `pip install -e ".[gdrive]"`.
Dev deps: `pip install -e ".[dev]"`.
