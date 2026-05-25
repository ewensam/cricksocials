# CrickSocials

**Automated Instagram-ready match result graphics and captions for village cricket clubs.**

After every game, CrickSocials fetches your result from Play Cricket, picks a photo, composes a branded image, writes a caption, and drops a ready-to-post draft in a folder (or uploads it to Google Drive). No manual work, no design skills required.

> **Status:** Early development — Phase 0 scaffold complete. Core functionality coming soon.

---

## Quickstart

```bash
# 1. Fork this repo on GitHub and clone your fork
git clone https://github.com/YOUR-USERNAME/cricksocials
cd cricksocials

# 2. Install
pip install -e .

# 3. Copy the example config and edit it for your club
cp config.example.yaml config.yaml
# Edit config.yaml — ~15 fields to fill in

# 4. Add your logo
cp /path/to/your/logo.png assets/logo.png

# 5. Add some photos
cp /path/to/win/photos/*.jpg photos/win/
cp /path/to/loss/photos/*.jpg photos/loss/

# 6. Validate everything is wired up
cricksocials validate

# 7. Preview a sample post
cricksocials preview

# 8. Run it for real
cricksocials run
```

Full setup guide: [docs/quickstart.md](docs/quickstart.md)

---

## Commands

| Command | Description |
|---|---|
| `cricksocials run` | Process new matches and write drafts |
| `cricksocials run --dry-run` | Process but don't write output |
| `cricksocials run --match-id ID` | Force-process one specific match |
| `cricksocials validate` | Check config, paths, and connectivity |
| `cricksocials preview` | Generate sample image with dummy data |
| `cricksocials list-recent` | Show recent matches and their status |

---

## Deployment

**Recommended: GitHub Actions** — fork the repo, drop in your config and assets, enable Actions. A scheduled workflow runs the tool twice a week and commits drafts back to your fork. Free, no machine to maintain.

See [docs/deployment-github-actions.md](docs/deployment-github-actions.md).

Other options (local cron, Docker, serverless) are sketched in [docs/deployment-other.md](docs/deployment-other.md).

---

## Configuration

Copy `config.example.yaml` and edit it. The full reference is documented inline.

Key sections:

- `club` — your club name and Play Cricket subdomain
- `teams` — which teams to track
- `branding` — logo, colours, fonts, overlay opacity
- `stats` — batting/bowling highlight thresholds
- `photos` — where to find match photos (`local` or `google_drive`)
- `output` — where to write drafts (`local` or `google_drive`)

---

## Adding a New Club

1. Fork the repo
2. Edit `config.yaml`
3. Drop in `assets/logo.png` and photos
4. Run `cricksocials validate` then `cricksocials preview`
5. Enable GitHub Actions

Onboarding time: 30–60 minutes for someone moderately technical.

See [examples/bridestowe-and-belstone/](examples/bridestowe-and-belstone/) for a worked example.

---

## Contributing

Issues and pull requests welcome. See [docs/contributing.md](docs/contributing.md).

---

## License

[MIT](LICENSE) — do what you want, just keep the copyright notice.
