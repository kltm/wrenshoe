# Wrenshoe

Ambient, passive flashcard system for language learning. Cards cycle automatically in your peripheral vision — no interaction required.

## Frontends

- **Web app** ([wrenshoe.org](https://wrenshoe.org)) — ambient mode (passive cycling) and flashcard mode (space = know, any key = don't know, score at end). PWA-installable for iOS StandBy / Android home screen. Dark, portrait-optimized.
- **Claude Code status line** — cards cycle in the status bar while you work. Configurable timing, field assignment, and cycle modes.

Both frontends share a common data model and deck format.

## Data Model

Deck schemas are defined in [LinkML](https://linkml.io/) (`schema/wrenshoe.yaml`), grounded in [OntoLex-Lemon](https://www.w3.org/2016/05/ontolex/) and [SKOS](https://www.w3.org/TR/skos-reference/). Language tags follow [BCP 47](https://www.rfc-editor.org/info/bcp47).

Each deck defines **field definitions** (with language, semantic type, and display defaults) and **cards** (with field values and optional tags/weights). Each deck carries its own `license` (SPDX identifier) and `sources` (attribution for upstream data).

## Included Decks

### Japanese

| Deck | Cards | License (SPDX) |
|------|-------|----------------|
| JLPT N5 | 710 | `CC-BY-SA-4.0 AND CC-BY-4.0` |
| JLPT N4 | 663 | `CC-BY-SA-4.0 AND CC-BY-4.0` |
| JLPT N3 | 2,078 | `CC-BY-SA-4.0 AND CC-BY-4.0` |
| JLPT N2 | 1,790 | `CC-BY-SA-4.0 AND CC-BY-4.0` |
| JLPT N1 | 2,655 | `CC-BY-SA-4.0 AND CC-BY-4.0` |
| Grade 1 Kanji (Kanken 10) | 80 | `CC-BY-SA-4.0` |
| Grade 2 Kanji (Kanken 9) | 160 | `CC-BY-SA-4.0` |
| Grade 3 Kanji (Kanken 8) | 200 | `CC-BY-SA-4.0` |
| Grade 4 Kanji (Kanken 7) | 202 | `CC-BY-SA-4.0` |
| Grade 5 Kanji (Kanken 6) | 193 | `CC-BY-SA-4.0` |
| Grade 6 Kanji (Kanken 5) | 191 | `CC-BY-SA-4.0` |
| Jouyou Secondary School | 1,110 | `CC-BY-SA-4.0` |
| Kansaiben vocabulary | 279 | `CC-BY-SA-3.0` |
| Hiragana | 73 | `CC-BY-4.0` |
| Katakana | 76 | `CC-BY-4.0` |

### Chinese

| Deck | Cards | License (SPDX) |
|------|-------|----------------|
| HSK 1 | 150 | `CC-BY-SA-4.0` |
| HSK 2 | 150 | `CC-BY-SA-4.0` |
| HSK 3 | 299 | `CC-BY-SA-4.0` |
| HSK 4 | 601 | `CC-BY-SA-4.0` |
| HSK 5 | 1,298 | `CC-BY-SA-4.0` |
| HSK 6 | 2,500 | `CC-BY-SA-4.0` |
| Chit-Chat Chinese | 391 | `CC-BY-4.0` |
| Boya Chinese Elementary Starter II | 718 | `CC-BY-4.0` |
| Short-term Spoken Chinese: Threshold | 1,136 | `CC-BY-4.0` |
| Pinyin Reference | 61 | `CC-BY-4.0` |

### Korean

| Deck | Cards | License (SPDX) |
|------|-------|----------------|
| Hangul Reading Practice | 157 | `CC-BY-4.0` |
| Korean Jamo | 67 | `CC-BY-4.0` |

### Other

| Deck | Cards | License (SPDX) |
|------|-------|----------------|
| Morse Code | 36 | `CC-BY-4.0` |

Full source attribution for each deck is in the deck JSON itself (`sources` field) and in [`data/ATTRIBUTION.md`](data/ATTRIBUTION.md).

## Web App

### Using wrenshoe.org

Visit [wrenshoe.org](https://wrenshoe.org), pick a deck, and choose **Ambient** (passive cycling) or **Flashcard** (space = know, other key = don't know, score at end) mode.

In the mode screen you can:
- **Reassign fields** to front, back, or hidden on a per-deck basis.
- **Pick an ambient speed**: Fast (5s), Normal (15s), Slow (30s, default), or Very Slow (60s).

### Nightstand / StandBy-style use on iPhone

iOS doesn't let Safari go true full-screen for regular browsing, and Apple's real StandBy mode is reserved for native WidgetKit widgets. But the installed PWA gets close:

1. In Safari, open [wrenshoe.org](https://wrenshoe.org).
2. Tap **Share** (the square with the up-arrow) > **Add to Home Screen** > **Add**.
3. Launch Wrenshoe from the new home-screen icon — iOS opens it in **standalone mode**, with no URL bar or toolbar. The status bar blends into the black background.
4. Pick a deck, enter **Ambient** mode, and rotate the phone to landscape — the layout grows to fill the screen.
5. Dock the phone on a charger. The app requests a **wake lock**, so the screen stays on while Wrenshoe is in the foreground.

This isn't technically "StandBy mode" (Apple reserves that name), but it's functionally the same experience without the Apple Developer commitment.

### Running your own instance

Clone the repo, generate the deck manifest, and serve locally:

```bash
git clone https://github.com/kltm/wrenshoe.git
cd wrenshoe
python3 tools/build-manifest.py    # generates docs/deck-manifest.json
ln -s ../data docs/data             # make deck data available to the app
cd docs && python3 -m http.server   # open http://localhost:8000
```

Add your own decks to `data/` (following the schema in `schema/wrenshoe.yaml`), re-run `build-manifest.py`, and refresh.

### Deploying to GitHub Pages

If you fork this repo and want your own hosted instance:

1. Go to your fork's **Settings > Pages**.
2. Under **Build and deployment > Source**, select **GitHub Actions**.
3. Push to `main` — the included workflow (`.github/workflows/pages.yml`) will build the site and deploy it automatically.
4. (Optional) Under **Settings > Pages > Custom domain**, add your domain and configure DNS per [GitHub's docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-github-pages).

The workflow runs `tools/build-manifest.py` to generate the deck index, then combines `docs/` (the app) and `data/` (the decks) into the deployed site. The reference deployment is at [wrenshoe.org](https://wrenshoe.org).

## Claude Code Status Line Setup

1. Ensure `wrenshoe.py` and deck data are in place.
2. Configure a session:
   ```
   python3 terminal/wrenshoe.py --configure
   ```
3. Add wrenshoe to your status line script (see `terminal/wrenshoe.py`).
4. Set `refreshInterval` in your Claude Code `settings.json`:
   ```json
   "statusLine": {
     "type": "command",
     "command": "bash ~/.claude/statusline-command.sh",
     "refreshInterval": 5
   }
   ```

Or use the `/wrenshoe install` skill to do all of the above automatically.

## Tools

- `tools/build-manifest.py` — generates `docs/deck-manifest.json` from `data/*.json` for the web app.
- `tools/convert-legacy.py` — converts legacy Wrenshoe `.meta`/`.data` deck pairs to the new JSON format.
- `tools/build-jlpt-decks.py` — builds JLPT and kanji decks from JMdict/KANJIDIC2.
- `tools/build-hsk-decks.py` — builds HSK decks from complete-hsk-vocabulary.
- `tools/build-korean-decks.py` — builds Korean hangul deck (historical; current deck is hand-curated).

## How to Cite

If you use wrenshoe decks in your work, please cite the upstream data sources listed in each deck's `sources` field. For the wrenshoe project itself:

> Wrenshoe: Ambient passive flashcard system. https://github.com/kltm/wrenshoe

## License

**Code** (`terminal/`, `tools/`, `schema/`): BSD-3-Clause (SPDX: `BSD-3-Clause`). See [LICENSE](LICENSE).

**Data** (`data/`): Each deck carries its own license in the `license` field of the deck JSON. Most derived decks are `CC-BY-SA-4.0`; original decks are `CC-BY-4.0`. See each deck file and [`data/ATTRIBUTION.md`](data/ATTRIBUTION.md) for details.

Code and data are licensed separately.
