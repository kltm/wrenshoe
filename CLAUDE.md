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

## Legacy Data

Original Wrenshoe data lives in `~/local/src/bazaar/home/trunk/wrenshoe/`. The conversion tool `tools/convert-legacy.py` transforms `.meta`/`.data` pairs to the new JSON format.
