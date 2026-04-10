---
name: wrenshoe
description: Ambient passive flashcard system — install, configure, manage decks, or control the status line flashcard cycler
disable-model-invocation: true
argument-hint: "[install|configure|add-deck|add-cards|import|pause|resume|status]"
---

# Wrenshoe — Ambient Flashcard Manager

You are managing the Wrenshoe ambient flashcard system. This system cycles language flashcards passively in the Claude Code status line.

The subcommand is: **$ARGUMENTS**

If no subcommand is given, treat it as **status**.

## Key paths

- Wrenshoe repo: `~/local/src/git/wrenshoe/`
- LinkML schema: `~/local/src/git/wrenshoe/schema/wrenshoe.yaml`
- Starter decks: `~/local/src/git/wrenshoe/data/`
- User decks: `~/.local/share/wrenshoe/decks/`
- Session config: `~/.config/wrenshoe/session.json`
- Runtime state: `~/.config/wrenshoe/state.json`

---

## Subcommand: install

Perform a full installation. Follow these steps in order:

### 1. Clone the repo (if needed)

Check if `~/local/src/git/wrenshoe/` exists and contains `terminal/wrenshoe.py`. If not:

```
git clone https://github.com/kltm/wrenshoe.git ~/local/src/git/wrenshoe
```

### 2. Patch the status line script

Read `~/.claude/statusline-command.sh`. If it does NOT already contain `wrenshoe`, append this block at the end:

```bash
# --- Wrenshoe flashcard section ---
wrenshoe_script="$HOME/local/src/git/wrenshoe/terminal/wrenshoe.py"
if [ -f "$wrenshoe_script" ] && [ -f "$HOME/.config/wrenshoe/session.json" ]; then
  wrenshoe_output=$(python3 "$wrenshoe_script" 2>/dev/null)
  if [ -n "$wrenshoe_output" ]; then
    echo "$wrenshoe_output"
  fi
fi
```

If `~/.claude/statusline-command.sh` does not exist at all, inform the user they need a status line script first and point them to the Claude Code docs.

### 3. Add refreshInterval

Read `~/.claude/settings.json`. If the `statusLine` object does not have `"refreshInterval"`, add `"refreshInterval": 5` to it.

### 4. Install the skill globally

Ensure `~/.claude/skills/wrenshoe/` exists. If the `SKILL.md` there is missing or outdated, copy it from the repo:

```
mkdir -p ~/.claude/skills/wrenshoe
cp ~/local/src/git/wrenshoe/.claude/skills/wrenshoe/SKILL.md ~/.claude/skills/wrenshoe/SKILL.md
```

### 5. Configure a session

Now proceed to the **configure** subcommand below.

### 6. Done

Tell the user they need to restart Claude Code for `refreshInterval` to take effect (if it was newly added). After restart, cards will cycle in the status bar.

---

## Subcommand: configure

Walk the user through session configuration conversationally.

### 1. List available decks

Run: `python3 ~/local/src/git/wrenshoe/terminal/wrenshoe.py --list-decks`

Present the decks and ask the user which one they want.

### 2. Load the chosen deck

Read the deck JSON file (it may be in `~/local/src/git/wrenshoe/data/` for starter decks or `~/.local/share/wrenshoe/decks/` for user decks). Show the user the **field definitions** — for each displayable field, show its label, language, and field type.

### 3. Ask about field assignment

Ask the user which fields should appear on the **front** (the prompt/challenge side) and which on the **back** (the answer/reveal side). Show the deck's defaults and offer to keep them.

### 4. Ask about timing

Ask how many seconds each phase should display. Current defaults or the user's existing config values should be shown. Typical values: 15-60 seconds for passive ambient viewing.

### 5. Ask about cycle mode

Ask whether the user wants:
- **front_back** — two phases per card (front, then back, then next card)
- **front_back_both** — three phases (front, back, then both together, then next card)

### 6. Write the session config

Write `~/.config/wrenshoe/session.json` with the user's choices:

```json
{
  "deck_id": "<chosen deck id>",
  "deck_path": "<absolute path to deck json>",
  "display": {
    "front": ["<field1>", ...],
    "back": ["<field1>", ...],
    "both": ["<all front + back fields>"],
    "timing_front_s": <number>,
    "timing_back_s": <number>,
    "timing_both_s": <number>,
    "cycle_mode": "<front_back|front_back_both>"
  }
}
```

Also delete `~/.config/wrenshoe/state.json` if it exists, so the new config takes effect immediately.

### 7. Confirm

Tell the user the configuration is active. Cards will begin cycling on the next status line refresh.

---

## Subcommand: pause

Rename `~/.config/wrenshoe/session.json` to `~/.config/wrenshoe/session.json.paused`. This stops the flashcard display without losing the configuration. Confirm to the user.

---

## Subcommand: resume

Rename `~/.config/wrenshoe/session.json.paused` back to `~/.config/wrenshoe/session.json`. Delete `~/.config/wrenshoe/state.json` to start fresh. Confirm to the user.

---

## Subcommand: status

Run: `python3 ~/local/src/git/wrenshoe/terminal/wrenshoe.py --status`

Show the output to the user. If no session is configured, suggest they run `/wrenshoe configure`.

---

## Subcommand: add-deck

Create a new user deck from scratch, conversationally. All decks MUST be validated against the LinkML schema.

### 1. Ask about the deck

Ask the user:
- What language is this for?
- What should the deck be called?
- A short description.

### 2. Define fields

Ask the user what fields each card should have. Guide them with examples:

- For a Japanese vocabulary deck, typical fields are: kanji (representation, ja), reading (representation, ja-Hira), meaning (sense, en)
- For a Mandarin deck: characters (representation, zh-Hans), pinyin (representation, zh-Latn), english (sense, en)
- For a Spanish deck: word (representation, es), english (sense, en)

For each field, determine:
- **name**: machine-readable key (lowercase, underscores)
- **label**: human-readable display name
- **language**: BCP 47 tag (e.g., `ja`, `ja-Hira`, `en`, `es`, `zh-Hans`, `zh-Latn`)
- **field_type**: `representation` (a written form) or `sense` (a meaning/gloss)
- **default_face**: which face it belongs to by default (`front` or `back`)

### 3. Ask for initial cards

Ask the user to provide their word/phrase list. Accept any reasonable input format:
- Pasted text with one entry per line
- Tab-separated fields
- Comma-separated fields
- Freeform text that Claude structures

For each card, map the user's input to the defined fields. Create `field_values` entries for each field. If a value is not applicable, use `"n/a"`.

If the user provides tags (difficulty levels, categories, etc.), include them.

### 4. Generate a deck ID

Create a short, unique ID from the deck name (lowercase, underscores, e.g., `spanish_travel_phrases`).

### 5. Assemble the deck JSON

Build the complete deck JSON following the schema structure:

```json
{
  "id": "<deck_id>",
  "name": "<deck name>",
  "description": "<description>",
  "source_language": "<BCP 47 tag>",
  "field_definitions": [ ... ],
  "default_display": {
    "front": ["<fields with default_face=front>"],
    "back": ["<fields with default_face=back>"]
  },
  "cards": [ ... ]
}
```

### 6. Validate against LinkML schema

**This step is MANDATORY.** Write the deck JSON to a temporary file, then run:

```
linkml-validate -s ~/local/src/git/wrenshoe/schema/wrenshoe.yaml <temp_file>
```

If validation fails:
- Read the error messages carefully
- Fix the JSON to conform to the schema
- Re-validate until it passes
- Do NOT skip validation or save an invalid deck

### 7. Save the deck

Once validated, save to the user decks directory:

```
mkdir -p ~/.local/share/wrenshoe/decks
```

Write the validated JSON to `~/.local/share/wrenshoe/decks/<deck_id>.json`.

### 8. Offer to configure

Ask the user if they want to switch to this deck now. If yes, proceed to the **configure** subcommand.

---

## Subcommand: add-cards

Add cards to an existing user deck.

### 1. Identify the deck

If an argument is provided after `add-cards`, use it as the deck ID. Otherwise, list user decks from `~/.local/share/wrenshoe/decks/` and ask.

Only user decks (in `~/.local/share/wrenshoe/decks/`) can be modified. If the user wants to add cards to a starter deck, tell them to first copy it to the user directory, or create a new deck.

### 2. Show the deck's field structure

Read the deck JSON. Show the user the field definitions so they know what format to provide cards in.

### 3. Accept new cards

Accept card data from the user in any reasonable format. Map input to field_values.

### 4. Append and validate

Append the new cards to the deck's cards array. Then **validate the entire deck** against the LinkML schema:

```
linkml-validate -s ~/local/src/git/wrenshoe/schema/wrenshoe.yaml ~/.local/share/wrenshoe/decks/<deck_id>.json
```

If validation fails, fix the issues before saving. Never save an invalid deck.

### 5. Confirm

Tell the user how many cards were added and the new total. If this is the active deck, delete `~/.config/wrenshoe/state.json` so the new cards enter rotation.

---

## Subcommand: import

Import cards from a file (TSV, CSV, or text) into a new or existing deck.

### 1. Read the input file

The argument should be a file path: `/wrenshoe import path/to/file.tsv`

Read the file. Detect the format:
- **TSV**: tab-separated, one card per line
- **CSV**: comma-separated, one card per line
- **Header comments**: lines starting with `#` may define metadata (e.g., `# language: ja`, `# fields: kanji, reading, meaning`)

### 2. Determine deck structure

If the file has header comments with metadata, use them. Otherwise, ask the user:
- What language?
- What does each column represent?
- Which columns are front vs. back fields?
- Are there tag columns?

### 3. Build or extend a deck

If importing into a new deck, follow the add-deck flow (steps 4-8).
If importing into an existing deck, verify the field structure matches, then follow the add-cards flow (steps 4-5).

### 4. Validate

**MANDATORY**: validate the resulting deck against the LinkML schema before saving:

```
linkml-validate -s ~/local/src/git/wrenshoe/schema/wrenshoe.yaml <deck_file>
```

---

## Important rendering notes

- The status line shows ONE line per card phase. Never multi-line per phase.
- Front fields render in bold cyan, back fields in yellow. Color is the only differentiator.
- Do NOT use typographic separators like em dashes between fields — they collide with CJK vowel extension marks (ー). Use spacing only.
- Default timing should be slow (30s per side) for passive ambient viewing.
