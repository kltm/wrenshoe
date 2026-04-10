# Wrenshoe

Ambient, passive flashcard system for language learning. Cards cycle automatically in your peripheral vision — no interaction required.

## Frontends

- **Claude Code status line** — cards cycle in the status bar while you work. Configurable timing, field assignment, and cycle modes.
- **iPhone PWA** (planned) — portrait-oriented web app for iOS StandBy mode.

Both frontends share a common data model.

## Data Model

Deck schemas are defined in [LinkML](https://linkml.io/) (`schema/wrenshoe.yaml`), grounded in [OntoLex-Lemon](https://www.w3.org/2016/05/ontolex/) and [SKOS](https://www.w3.org/TR/skos-reference/). Language tags follow [BCP 47](https://www.rfc-editor.org/info/bcp47).

Each deck defines **field definitions** (with language, semantic type, and display defaults) and **cards** (with field values and optional tags/weights).

## Included Decks

| Deck | Cards | Language |
|------|-------|----------|
| Kansaiben vocabulary | 279 | Japanese (Kansai dialect) |
| Hiragana | 73 | Japanese |
| Katakana | 76 | Japanese |
| Mandarin vocabulary | 393 | Chinese (Simplified) |

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

## Tools

- `tools/convert-legacy.py` — converts legacy Wrenshoe `.meta`/`.data` deck pairs to the new JSON format.

## License

BSD-3-Clause. See [LICENSE](LICENSE).
