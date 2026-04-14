# Wrenshoe - Claude Code Guide

## What This Is

Wrenshoe is an ambient, passive flashcard system for language learning. It is NOT an active quiz/recall system — cards cycle automatically in the user's peripheral vision without requiring interaction.

Two frontends, one shared data model:
1. **Claude Code status line** — cycles cards in the terminal status bar
2. **Web app / PWA** — hosted at wrenshoe.org via GitHub Pages, installable as a PWA for nightstand / StandBy-style use on iOS (landscape, docked, wake-locked)

## Data Model

- Schema: `schema/wrenshoe.yaml` (LinkML)
- Generated JSON Schema: `schema/wrenshoe.schema.json`
- Deck data: `data/*.json`
- Validate decks: `linkml-validate -s schema/wrenshoe.yaml data/<deck>.json`

The schema is grounded in OntoLex-Lemon (lexical entries, forms, senses) and SKOS (labels, definitions). Language tags use BCP 47.

Both `source_language` (on Deck) and `language` (on FieldDefinition) may use BCP 47 private-use subtags for dialects (e.g., `ja-x-kansai` for Kansai dialect Japanese). Any code that groups or filters by language must use prefix matching, not exact equality — `ja-x-kansai` is Japanese, not a separate language.

Key classes:
- **Deck** — contains field_definitions, default_display, and cards
- **FieldDefinition** — defines a named field with language tag, semantic type (representation/sense/reference), and display defaults
- **Card** — has field_values (list of field/value pairs), tags, weight
- **DisplayConfig** — which fields on front/back/both, timing, cycle_mode, tag_filter

## Card Display Cycle

Cards cycle through phases: front -> back (or front -> back -> both if cycle_mode is "front_back_both"). Each phase shows configured fields rendered on a single status line with color differentiation:
- Front fields: bold cyan
- Back fields: yellow
- No typographic separators between fields (just spacing) — em dashes and similar characters conflict with CJK vowel extension marks

## Terminal Cycler

- Script: `terminal/wrenshoe.py`
- Session config: `~/.config/wrenshoe/session.json`
- Runtime state: `~/.config/wrenshoe/state.json`
- Integrated into status line via `~/.claude/statusline-command.sh`
- `refreshInterval: 5` in Claude Code settings.json drives the cycle

Modes: `--render` (default, for status line), `--configure` (interactive setup), `--list-decks`, `--status`

### Concurrent writes — IMPORTANT

The user may have up to ~12 Claude Code terminals open at once, each invoking `--render` every 5 seconds. Any code that writes `session.json` or `state.json` must go through `_atomic_write()` (temp file + `os.replace`, which is POSIX-atomic on the same filesystem). Never call `open(path, "w")` on these files directly — concurrent direct writes interleave and corrupt the file, which previously surfaced as a `JSONDecodeError: Extra data` that killed the status line across every terminal.

Reads go through `_safe_load()`, which returns `None` on corrupt or missing files so a single bad state can't brick the cycler. If you add a new persisted file, reuse these helpers.

## Web App (PWA)

- Source: `docs/` (HTML, CSS, JS, manifest, service worker, SVG icon)
- Vanilla JS, no framework, no build step for the app itself
- Deck manifest: `docs/deck-manifest.json` is **generated** (gitignored) by `tools/build-manifest.py`, which scans `data/*.json` and writes a lightweight index
- Local dev: `ln -s ../data docs/data` makes deck data reachable to the app; this symlink is also gitignored
- Deployment: `.github/workflows/pages.yml` runs `build-manifest.py`, copies `docs/` + `data/` into `_site/`, and deploys via `actions/deploy-pages`
- Reference deployment: [wrenshoe.org](https://wrenshoe.org) (custom domain pointed at GitHub Pages via EasyDNS apex A records)

### Screen architecture

Single-page app with six screens toggled by JS: deck picker, mode select, ambient, flashcard, score, about. The `show(id)` helper flips the `.active` class. Global keydown routes input based on the active screen.

### Service worker caching

Strategy is **stale-while-revalidate** for everything. Cached response serves immediately, network fetch updates the cache in the background, next visit gets fresh content. A previous cache-first strategy meant deploys never reached installed PWAs — do not revert.

If the fetch strategy changes fundamentally (e.g. new cache buckets, new URL patterns needing different behavior), bump `CACHE_NAME` in `docs/sw.js` so the `activate` handler drops the old cache and forces a clean rebootstrap. Regular app-shell deploys do NOT require a bump — stale-while-revalidate handles them.

### Touch UX requirement

Every screen must have a visible, tappable exit. Keyboard-only escapes (Esc) trap phone users because phones have no Esc key. The `.back-btn` class (top-left arrow) is reused across mode, flashcard, and about screens. Score screen has "Decks" and "Play Again" buttons. Ambient is exited by tapping anywhere.

### Landscape layout

Ambient mode has an `@media (orientation: landscape) and (max-height: 600px)` block that grows the text on `22vh` for phone-in-landscape nightstand use. The `max-height` guard prevents desktop landscape browsers from inheriting phone sizing.

### Credits identity

In user-facing surfaces (PWA About screen, wrenshoe.org), credit the project author as **kltm** with a link to their GitHub. In developer-facing surfaces (README.md, data/ATTRIBUTION.md, deck JSON `sources` fields), **Seth Carbon** is fine — the real name is already established in those contexts.

## Important Design Decisions

- Single-line output only — multi-line causes visual jarring in the status bar
- Color, not typography, differentiates fields — many languages use characters that resemble Latin punctuation
- Timing is user-configurable and should default to slow (30s/30s for passive ambient viewing)
- cycle_mode "front_back" (2 phases) vs "front_back_both" (3 phases) is user-selectable
- Field assignment (which fields on which face) persists across sessions via session.json
- Cards with "n/a" field values are filtered from display

## Deck Management

- Starter decks: `data/` (shipped with repo, not user-editable)
- User decks: `~/.local/share/wrenshoe/decks/` (user-created, editable)
- The `/wrenshoe` skill handles deck creation (`add-deck`), card addition (`add-cards`), and file import (`import`)

**All deck writes MUST be validated against the LinkML schema before saving:**

```
linkml-validate -s schema/wrenshoe.yaml <deck_file>
```

Never save an invalid deck. If validation fails, fix the JSON and re-validate.

## Licensing

Code and data are licensed separately:
- **Code** (`terminal/`, `tools/`, `schema/`): BSD-3-Clause
- **Data** (`data/`): each deck carries its own SPDX license in the `license` field, plus `sources` for upstream attribution

Every deck JSON must have a `license` (SPDX identifier) and `sources` (list of SourceAttribution). When creating or modifying decks, always populate these fields.

### License compatibility — IMPORTANT

Not all open licenses are compatible when combining data into a single derivative work:
- **CC-BY-SA-3.0 and CC-BY-SA-4.0 are NOT automatically compatible** with each other. Content under one cannot simply be merged into a deck under the other.
- **CC-BY** is compatible with CC-BY-SA (it can be incorporated into SA-licensed works).
- **MIT** data is compatible with everything.
- Currently each starter deck is derived from a compatible source set, but **cross-deck merging** (e.g. combining kansaiben CC-BY-SA-3.0 with KANJIDIC2 CC-BY-SA-4.0 into one deck) requires a compatibility audit first.
- When adding new decks or importing data, always check that the source licenses are compatible before combining.
- Use SPDX compound expressions (`AND`) when a deck derives from multiple sources with different licenses.

### Source-specific notes

- **kansaibenkyou.net**: CC-BY-SA-3.0, by Keiko Yukawa
- **KANJIDIC2 / JMdict**: CC-BY-SA-4.0, EDRDG / Jim Breen (Monash)
- **CC-CEDICT**: CC-BY-SA-4.0
- **cc-kedict**: CC-BY-SA-3.0, Masato Hagiwara
- **JLPT word lists**: MIT (jamsinclair), underlying data CC-BY (Jonathan Waller)
- **HSK vocabulary**: MIT (drkameleon), underlying data from CC-CEDICT
- **Legacy decks** (hiragana, katakana, mandarin vocab): CC-BY-4.0, Seth Carbon
- **Chinese textbook decks** (Chit-Chat Chinese, Boya Chinese, Short-term Spoken Chinese): CC-BY-4.0, hand-entered by Seth Carbon
- **Korean hangul deck**: CC-BY-4.0, hand-curated by Seth Carbon (food/restaurant/elementary vocab for jamo coverage)
- **Jamo, Pinyin Reference, Morse Code**: CC-BY-4.0, Seth Carbon

## Legacy Data

Original Wrenshoe data lives in `~/local/src/bazaar/home/trunk/wrenshoe/`. The conversion tool `tools/convert-legacy.py` transforms `.meta`/`.data` pairs to the new JSON format.
