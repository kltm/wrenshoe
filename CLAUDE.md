# Wrenshoe - Claude Code Guide

## What This Is

Wrenshoe is an ambient, passive flashcard system for language learning. It is NOT an active quiz/recall system — cards cycle automatically in the user's peripheral vision without requiring interaction.

Two frontends, one shared data model:
1. **Claude Code status line** — implemented, cycles cards in the terminal status bar
2. **iPhone PWA for StandBy mode** — planned, portrait orientation

## Data Model

- Schema: `schema/wrenshoe.yaml` (LinkML)
- Generated JSON Schema: `schema/wrenshoe.schema.json`
- Deck data: `data/*.json`
- Validate decks: `linkml-validate -s schema/wrenshoe.yaml data/<deck>.json`

The schema is grounded in OntoLex-Lemon (lexical entries, forms, senses) and SKOS (labels, definitions). Language tags use BCP 47.

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
