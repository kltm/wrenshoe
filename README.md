# Wrenshoe

Ambient, passive flashcard system for language learning. Cards cycle automatically in your peripheral vision — no interaction required.

## Frontends

- **Claude Code status line** — cards cycle in the status bar while you work. Configurable timing, field assignment, and cycle modes.
- **iPhone PWA** (planned) — portrait-oriented web app for iOS StandBy mode.

Both frontends share a common data model.

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
