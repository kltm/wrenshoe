---
name: wrenshoe
description: Ambient passive flashcard system — install, configure, or manage the status line flashcard cycler
disable-model-invocation: true
argument-hint: "[install|configure|pause|resume|status]"
---

# Wrenshoe — Ambient Flashcard Manager

You are managing the Wrenshoe ambient flashcard system. This system cycles language flashcards passively in the Claude Code status line.

The subcommand is: **$ARGUMENTS**

If no subcommand is given, treat it as **status**.

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

Read the deck JSON file from `~/local/src/git/wrenshoe/data/<deck>.json`. Show the user the **field definitions** — for each displayable field, show its label, language, and field type.

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

## Important rendering notes

- The status line shows ONE line per card phase. Never multi-line per phase.
- Front fields render in bold cyan, back fields in yellow. Color is the only differentiator.
- Do NOT use typographic separators like em dashes between fields — they collide with CJK vowel extension marks (ー). Use spacing only.
- Default timing should be slow (30s per side) for passive ambient viewing.
