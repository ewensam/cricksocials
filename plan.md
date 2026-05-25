# CrickSocials — Open Source Cricket Social Media Automation

## v4 Architecture Plan — Multi-tenant, Self-hosted

---

## Project Summary

An open-source tool that village cricket clubs can self-deploy to automatically generate Instagram-ready match result graphics and captions after every game. Clubs supply their own config, logo, photos, and choose where to run it. Bridestowe & Belstone CC is the pilot deployment.

**Project name:** `cricksocials`

**License:** MIT (most permissive, encourages adoption)

**Repo location:** Public GitHub repository

---

## Design Principles

1. **Config over code.** Anything that varies between clubs lives in a YAML file. No code changes needed to onboard a new club.
2. **Adapters for everything that varies in the wild.** Photo sources, output destinations, and notification channels are pluggable. Local folder is the default everywhere — it just works.
3. **Sensible defaults.** A club should be able to fork the repo, drop a logo in `assets/`, edit ~15 lines of YAML, and have a working pipeline.
4. **Run anywhere.** The same package runs from a laptop, a Raspberry Pi, GitHub Actions, a Cloud Function, or a Docker container.
5. **Idempotent.** Safe to run multiple times. Won't re-generate posts for matches it's already processed.
6. **No service dependencies by default.** No databases, no message queues, no auth flows. State is a JSON file. Photos are files. Output is files. Clubs can layer on cloud storage if they want.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    cricket-match-day                            │
│                                                                 │
│   ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│   │   Scraper   │───▶│    Parser    │───▶│  Stats Engine   │    │
│   │ (Play-      │    │ (HTML →      │    │ (thresholds,    │    │
│   │  Cricket)   │    │  dataclass)  │    │  formatting)    │    │
│   └─────────────┘    └──────────────┘    └────────┬────────┘    │
│                                                   │             │
│                                                   ▼             │
│   ┌─────────────┐                       ┌──────────────────┐    │
│   │   Photo     │──────────────────────▶│  Image Composer  │    │
│   │   Source    │  (random win/loss)    │  (Pillow)        │    │
│   │  ADAPTER    │                       └────────┬─────────┘    │
│   └─────────────┘                                │              │
│                                                  ▼              │
│   ┌─────────────┐                       ┌──────────────────┐    │
│   │  Caption    │──────────────────────▶│  Output Sink     │    │
│   │  Generator  │                       │  ADAPTER         │    │
│   └─────────────┘                       └──────────────────┘    │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │   State (processed match IDs) — JSON file                │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        │                                                 │
        │ Driven by:                            Configured by:
        ▼                                                 ▼
┌──────────────────┐                         ┌──────────────────────┐
│  Cron / Actions  │                         │   club-config.yaml   │
│  Task Scheduler  │                         │   + assets/logo.png  │
│  Manual run      │                         │   + photos/          │
└──────────────────┘                         └──────────────────────┘
```

---

## Adapter Pattern

Two interfaces clubs can choose from — both ship with a `LocalFolder` implementation that needs zero credentials.

### `PhotoSource` interface

```python
class PhotoSource(Protocol):
    def list_photos(self, category: Literal["win", "loss"]) -> list[PhotoRef]: ...
    def fetch_photo(self, ref: PhotoRef) -> bytes: ...
```

**Built-in implementations:**
- `LocalFolderPhotoSource` — reads from `./photos/win/`, `./photos/loss/`
- `GoogleDrivePhotoSource` — reads from configured Drive folders

**Future (community contributions):**
- `DropboxPhotoSource`, `OneDrivePhotoSource`, `S3PhotoSource`

### `OutputSink` interface

```python
class OutputSink(Protocol):
    def write_post(self, draft: PostDraft) -> str: ...  # returns location
```

**Built-in implementations:**
- `LocalFolderOutputSink` — writes to `./drafts/YYYY-MM-DD/`
- `GoogleDriveOutputSink` — uploads to configured Drive folder

Selected via config:
```yaml
photos:
  adapter: local            # or "google_drive"
  local:
    win_dir: ./photos/win
    loss_dir: ./photos/loss

output:
  adapter: local            # or "google_drive"
  local:
    drafts_dir: ./drafts
```

---

## Configuration Model

A single `config.yaml` per club. Example for B&B:

```yaml
club:
  name: "Bridestowe and Belstone CC"
  short_name: "B&B"
  play_cricket_subdomain: "bridestoweandbelstone"
  # Resulting URL: https://bridestoweandbelstone.play-cricket.com

teams:
  - name: "1st XI"
    identifier: "1st"
  - name: "2nd XI"
    identifier: "2nd"
  - name: "3rd XI"
    identifier: "3rd"
  - name: "Sunday XI"
    identifier: "Sunday"

branding:
  logo_path: ./assets/logo.png
  colours:
    primary: "#1B2A4A"       # navy
    accent: "#2D7F4E"        # green
    text: "#FFFFFF"
  overlay_opacity: 0.70      # 0.0-1.0
  fonts:
    bold: ./assets/fonts/Montserrat-Bold.ttf
    regular: ./assets/fonts/Montserrat-Regular.ttf

stats:
  batting_threshold_runs: 30
  bowling_threshold_wickets: 2
  fallback_to_top_performer: true   # if nobody hits threshold

photos:
  adapter: local
  local:
    win_dir: ./photos/win
    loss_dir: ./photos/loss

output:
  adapter: local
  local:
    drafts_dir: ./drafts

captions:
  template_dir: ./templates
  hashtags:
    - "#DevonCricket"
    - "#VillageCricket"

scraping:
  request_delay_seconds: 3
  use_cloudscraper_fallback: true
  user_agent: >-
    Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
    (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

state:
  path: ./state/processed_matches.json
```

Validation via Pydantic — clubs get clear errors if config is missing fields or has typos.

---

## CLI Interface

A single entry point with subcommands. Clubs run these directly or wrap them in their scheduler of choice.

```bash
cricksocials run               # Process new matches and write drafts
cricksocials run --dry-run     # Process but don't write outputs
cricksocials run --match-id 7069988    # Force-process one specific match
cricksocials validate          # Check config + paths + connectivity
cricksocials preview           # Generate sample image with dummy data
cricksocials list-recent       # Show recent matches that would be processed
```

`validate` is critical for self-serve onboarding — clubs run it once after editing config and get a checklist of what's working and what isn't.

---

## Deployment

**v1 ships with GitHub Actions as the only fully-supported deployment path.** Other options (local cron, Docker, serverless) are documented in the README for clubs that want them, but no scripts or workflows are maintained for them in v1. This keeps the surface area small.

### GitHub Actions (the v1 path)

Fork the repo, commit your config and assets, enable Actions. A scheduled workflow runs the tool twice a week. Output is committed back to a `drafts/` folder in the fork, or uploaded to Drive if the club configured that adapter.

**Pros:** Free, no machine to maintain, no installs. Reliable. Public Actions log gives visibility into what happened.
**Cons:** Photos must live in the repo (private fork acceptable) or in Drive. Acceptable trade-off for most clubs.

Ships with `.github/workflows/match-day.yml` ready to use — clubs may need to adjust the cron schedule and that's it.

### Documented in README only (not maintained in v1)

- **Local cron / Windows Task Scheduler** — for clubs that want full control
- **Docker container** — for the docker-savvy
- **Cloud Function / Lambda** — for the cloud-savvy

These are sketches in the README pointing at the same CLI entry point. Clubs can self-implement and contribute back if they want.

---

## Onboarding a New Club (target experience)

1. Fork the repo on GitHub
2. Copy `config.example.yaml` → `config.yaml`, edit ~15 fields
3. Drop logo PNG into `assets/`
4. Drop 5+ photos each into `photos/win/` and `photos/loss/`
5. Optionally tweak caption templates in `templates/`
6. Run `cricksocials validate` to confirm everything is wired up
7. Run `cricksocials preview` to see a sample post
8. Enable GitHub Actions (or follow the README sketches for other deployment paths)

End-to-end onboarding time: 30-60 minutes for someone moderately technical.

---

## Repo Structure

```
cricksocials/
├── README.md                       # Main docs, with quickstart
├── LICENSE                         # MIT
├── pyproject.toml                  # Modern Python packaging
├── config.example.yaml             # Annotated example config
├── .github/
│   ├── workflows/
│   │   ├── match-day.yml           # The scheduled workflow (template)
│   │   └── ci.yml                  # Tests on PR
│   └── ISSUE_TEMPLATE/
├── docs/
│   ├── quickstart.md
│   ├── deployment-github-actions.md
│   ├── deployment-other.md         # Sketches for cron/Docker/serverless
│   ├── adapters.md                 # How to use / write photo & output adapters
│   ├── caption-templates.md
│   ├── troubleshooting.md
│   └── contributing.md
├── src/
│   └── cricksocials/
│       ├── __init__.py
│       ├── cli.py                  # Click-based CLI entry point
│       ├── config.py               # Pydantic config models + validation
│       ├── scraper.py              # HTTP fetching (requests + cloudscraper fallback)
│       ├── parser.py               # HTML → MatchResult dataclasses
│       ├── stats.py                # Thresholds + performer formatting
│       ├── image_gen.py            # Pillow compositing
│       ├── captions.py             # Template rendering + random selection
│       ├── state.py                # JSON state file (processed match IDs)
│       ├── orchestrator.py         # Wires the pipeline together
│       └── adapters/
│           ├── __init__.py
│           ├── photo_source.py     # Protocol + LocalFolder + GoogleDrive
│           └── output_sink.py      # Protocol + LocalFolder + GoogleDrive
├── templates/
│   ├── win_captions.txt            # Default templates (clubs override)
│   └── loss_captions.txt
├── assets/
│   ├── logo.png                    # Placeholder, clubs replace
│   └── fonts/
│       ├── Montserrat-Bold.ttf
│       └── Montserrat-Regular.ttf
├── tests/
│   ├── test_parser.py
│   ├── test_stats.py
│   ├── test_image_gen.py
│   ├── test_config.py
│   ├── test_adapters_local.py
│   └── fixtures/
│       ├── match_7069988.html      # B&B vs Stithians, real saved HTML
│       └── match_abandoned.html    # Edge case
├── examples/
│   └── bridestowe-and-belstone/
│       ├── config.yaml
│       ├── logo.png
│       └── README.md               # B&B's specific setup as a reference
└── photos/                         # Empty in repo, clubs fill in
    ├── win/.gitkeep
    └── loss/.gitkeep
```

---

## Dependencies

```toml
[project]
dependencies = [
  "requests>=2.31",
  "cloudscraper>=1.2",
  "beautifulsoup4>=4.12",
  "lxml>=5.0",
  "Pillow>=10.0",
  "pydantic>=2.0",
  "pyyaml>=6.0",
  "click>=8.1",
]

[project.optional-dependencies]
gdrive = [
  "google-api-python-client>=2.0",
  "google-auth>=2.0",
]
dev = [
  "pytest>=7.0",
  "pytest-cov",
  "ruff",
  "mypy",
]
```

Google Drive is opt-in via extras — clubs not using it don't get those deps.

---

## Pilot Plan (B&B)

The B&B-specific config and assets live in `examples/bridestowe-and-belstone/` in the main repo. This serves two purposes:

1. **Working reference deployment** — proves the tool works end-to-end with real data
2. **Template for other clubs** — they can copy the directory structure and adapt

The pilot also drives the docs. Once B&B is running cleanly, write `quickstart.md` based on what was actually involved.

---

## Build Phases (for Claude Code)

| Phase | What                                              | Test                                   |
|-------|---------------------------------------------------|----------------------------------------|
| 0     | Repo scaffolding, pyproject.toml, CLI skeleton    | `cricksocials --help` works             |
| 1     | `config.py` — Pydantic models + validation        | Round-trip example config              |
| 2     | `parser.py` — HTML → MatchResult                  | Against saved match_7069988.html       |
| 3     | `scraper.py` — fetch + cloudscraper fallback      | Live integration test                   |
| 4     | `stats.py` — thresholds + formatters              | Unit tests with edge cases             |
| 5     | `adapters/photo_source.py` LocalFolder            | Unit tests                              |
| 6     | `image_gen.py` — Pillow compositing               | Generate sample images                  |
| 7     | `captions.py` — templates + random selection      | Print samples                           |
| 8     | `adapters/output_sink.py` LocalFolder             | Unit tests                              |
| 9     | `state.py` — processed match tracking             | Unit tests                              |
| 10    | `orchestrator.py` — wire it all together          | End-to-end with fixture                 |
| 11    | `validate` and `preview` CLI commands             | Manual test                             |
| 12    | GitHub Actions workflow template                  | Trigger on schedule, check artifacts    |
| 13    | Google Drive adapters (both)                      | Manual test with real Drive             |
| 14    | Docs (README, quickstart, deployment guides)      | Walk a friend through it                |
| 15    | B&B pilot deployment in `examples/`               | Real match day end-to-end               |

Phases 0-10 are the core. Everything after is polish, multi-tenancy enablement, and the actual pilot. The build can pause and ship at the end of phase 11 if you want to validate with B&B first.

---

## Open Questions to Decide During Build

These don't need answering now — they can be resolved as the project takes shape:

1. **Project name** — `cricket-match-day` works but isn't loved. Worth bikeshedding once.
2. **PyPI publishing** — once stable, push to PyPI so `pip install cricksocials` works without cloning. Lowers barrier further.
3. **Web UI?** — A future-future option: a tiny Flask/FastAPI app that wraps the CLI for clubs that *really* don't want a terminal. Out of scope for v1.
4. **Match report scraping** — Play Cricket also has match reports. Could extract those for richer captions. Stretch goal.
5. **Multiple post variants per match** — generate 2-3 image variants and let the social media manager pick. Easy to add.

---

## Trade-offs Worth Naming

- **No web UI** means clubs need someone who can edit YAML. Confirmed acceptable based on technical floor.
- **GitHub Actions only in v1** means clubs without GitHub access need to follow sketch docs and self-implement. Acceptable for a self-serve OSS project.
- **Open source means support is community-driven.** GitHub Issues + clear docs do most of the heavy lifting. You're not on the hook for 2am pages.
- **Adapter pattern adds complexity** vs. hardcoded Google Drive. Worth it because (a) local folder default lowers the barrier hugely, and (b) it makes contributions easier.
- **Per-club config in YAML** means a typo can break the pipeline. `validate` command mitigates this.

---

## What's Different vs v3

- **Multi-tenant by design** — no B&B-specific code anywhere
- **Local folder as default** for photos and output — no cloud auth needed to get started
- **CLI entry point** — replaces direct Cloud Function deployment
- **GitHub Actions as primary deployment** — replaces Cloud Functions/Cloud Run
- **Adapters layer** — clean extension point for future contributions
- **Real documentation as a first-class deliverable** — not an afterthought
- **B&B becomes an `examples/` directory** — reference deployment, not the product

The actual parsing/image/caption logic from v3 carries straight over. The plumbing around it is what changes.
