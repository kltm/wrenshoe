#!/usr/bin/env python3
"""Wrenshoe ambient flashcard cycler for Claude Code status line.

Modes:
  --render       Output current card face for status line (default).
  --configure    Interactive session setup (deck, field assignment).
  --list-decks   List available decks.
  --status       Show current session state.
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "wrenshoe"
SESSION_FILE = CONFIG_DIR / "session.json"
STATE_FILE = CONFIG_DIR / "state.json"

# Where deck JSON files live (next to this script's repo).
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"

# ANSI color helpers.
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


def find_decks():
    """Find all deck JSON files."""
    decks = {}
    if DATA_DIR.is_dir():
        for f in sorted(DATA_DIR.glob("*.json")):
            try:
                with open(f, encoding="utf-8") as fh:
                    d = json.load(fh)
                    decks[d["id"]] = {"path": str(f), "name": d["name"]}
            except (json.JSONDecodeError, KeyError):
                pass
    return decks


def load_session():
    """Load session config, or None."""
    if SESSION_FILE.exists():
        with open(SESSION_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_session(session):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_state(state):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def load_deck(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_display_config(deck, session):
    """Resolve effective display config: session overrides deck defaults."""
    base = deck.get("default_display") or {}
    override = (session or {}).get("display") or {}

    return {
        "front": override.get("front") or base.get("front", []),
        "back": override.get("back") or base.get("back", []),
        "both": override.get("both") or base.get("both"),
        "suppress": override.get("suppress") or base.get("suppress", []),
        "timing_front_s": override.get("timing_front_s") or base.get("timing_front_s", 10),
        "timing_back_s": override.get("timing_back_s") or base.get("timing_back_s", 10),
        "timing_both_s": override.get("timing_both_s") or base.get("timing_both_s", 5),
        "cycle_mode": override.get("cycle_mode") or base.get("cycle_mode", "front_back"),
        "tag_filter": override.get("tag_filter") or base.get("tag_filter"),
        "card_order": override.get("card_order") or base.get("card_order", "weighted_random"),
    }


def make_card_order(deck, display):
    """Build a shuffled list of card indices, respecting tag filters and weights."""
    cards = deck.get("cards", [])
    tag_filter = display.get("tag_filter")

    eligible = []
    weights = []
    for i, card in enumerate(cards):
        if tag_filter:
            card_tags = set(card.get("tags", []))
            if not card_tags.intersection(tag_filter):
                continue
        eligible.append(i)
        weights.append(card.get("weight", 1.0))

    if not eligible:
        return list(range(len(cards)))

    order = display.get("card_order", "weighted_random")
    if order == "sequential":
        return eligible
    elif order == "random":
        random.shuffle(eligible)
        return eligible
    else:  # weighted_random
        result = []
        pool = list(zip(eligible, weights))
        while pool:
            indices, ws = zip(*pool)
            chosen = random.choices(range(len(pool)), weights=ws, k=1)[0]
            result.append(pool[chosen][0])
            pool.pop(chosen)
        return result


def get_card_field_value(card, field_name):
    """Get a field value from a card by field name."""
    for fv in card.get("field_values", []):
        if fv["field"] == field_name:
            return fv["value"]
    return None


def render_face(card, field_names, field_defs_map):
    """Render a list of field values for display."""
    lines = []
    for fname in field_names:
        val = get_card_field_value(card, fname)
        if val and val != "n/a":
            lines.append(val)
    return lines


def get_phase_order(display):
    """Return phase sequence based on cycle_mode."""
    mode = display.get("cycle_mode", "front_back")
    if mode == "front_back_both":
        return ["front", "back", "both"]
    return ["front", "back"]


def advance_state(state, deck, display):
    """Check timing and advance phase/card if needed."""
    now = time.time()
    elapsed = now - state["phase_started_at"]
    phase_order = get_phase_order(display)

    phase = state["phase"]
    if phase not in phase_order:
        phase = phase_order[0]
        state["phase"] = phase

    if phase == "front":
        limit = display["timing_front_s"]
    elif phase == "back":
        limit = display["timing_back_s"]
    else:
        limit = display["timing_both_s"]

    if elapsed < limit:
        return state  # no change

    # Advance phase.
    phase_idx = phase_order.index(phase)
    if phase_idx < len(phase_order) - 1:
        state["phase"] = phase_order[phase_idx + 1]
        state["phase_started_at"] = now
    else:
        # Advance card.
        state["card_position"] += 1
        if state["card_position"] >= len(state["card_order"]):
            state["card_order"] = make_card_order(deck, display)
            state["card_position"] = 0
        state["phase"] = phase_order[0]
        state["phase_started_at"] = now

    return state


def init_state(deck, display):
    """Create fresh state for a new session."""
    order = make_card_order(deck, display)
    return {
        "deck_id": deck["id"],
        "card_order": order,
        "card_position": 0,
        "phase": "front",
        "phase_started_at": time.time(),
    }


def render(args):
    """Output current card face for status line."""
    session = load_session()
    if not session:
        return  # no session configured, output nothing

    deck_path = session.get("deck_path")
    if not deck_path or not Path(deck_path).exists():
        return

    deck = load_deck(deck_path)
    if not deck.get("cards"):
        return

    display = get_display_config(deck, session)

    # Load or init state.
    state = load_state()
    if not state or state.get("deck_id") != deck["id"]:
        state = init_state(deck, display)
    else:
        # Validate card_order is still valid.
        if state["card_position"] >= len(state.get("card_order", [])):
            state = init_state(deck, display)

    # Advance if timing requires it.
    state = advance_state(state, deck, display)
    save_state(state)

    # Get current card.
    card_idx = state["card_order"][state["card_position"]]
    card = deck["cards"][card_idx]
    phase = state["phase"]

    # Build field definitions lookup.
    fd_map = {fd["name"]: fd for fd in deck.get("field_definitions", [])}

    # Determine which fields to show.
    if phase == "both":
        field_names = display.get("both")
        if not field_names:
            # Default: front + back, deduplicated, order preserved.
            seen = set()
            field_names = []
            for fn in display["front"] + display["back"]:
                if fn not in seen:
                    field_names.append(fn)
                    seen.add(fn)
    else:
        field_names = display.get(phase, [])

    # Gather values, split into front-sourced and back-sourced for coloring.
    front_set = set(display.get("front", []))
    back_set = set(display.get("back", []))

    parts = []
    for fname in field_names:
        val = get_card_field_value(card, fname)
        if not val or val == "n/a":
            continue
        if fname in front_set:
            parts.append(f"{BOLD}{CYAN}{val}{RESET}")
        elif fname in back_set:
            parts.append(f"{YELLOW}{val}{RESET}")
        else:
            parts.append(f"{MAGENTA}{val}{RESET}")

    if not parts:
        return

    indicators = {"front": "▸", "back": "◂", "both": "◆"}
    indicator = indicators.get(phase, " ")

    print(f"{DIM}{indicator}{RESET} {'   '.join(parts)}")


def configure(args):
    """Interactive session setup."""
    decks = find_decks()
    if not decks:
        print(f"No decks found in {DATA_DIR}", file=sys.stderr)
        sys.exit(1)

    # Deck selection.
    print("Available decks:")
    deck_ids = list(decks.keys())
    for i, did in enumerate(deck_ids, 1):
        print(f"  {i}. {decks[did]['name']}")

    while True:
        choice = input(f"\nSelect deck [1-{len(deck_ids)}]: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(deck_ids):
                break
        except ValueError:
            pass
        print("Invalid choice.")

    deck_id = deck_ids[idx]
    deck_info = decks[deck_id]
    deck = load_deck(deck_info["path"])
    fd_map = {fd["name"]: fd for fd in deck["field_definitions"]}

    # Show displayable fields.
    displayable = [fd for fd in deck["field_definitions"]
                   if fd.get("displayable", True)]
    defaults = deck.get("default_display", {})

    print(f"\nDeck: {deck['name']}")
    print(f"Fields:")
    for i, fd in enumerate(displayable, 1):
        lang = fd.get("language", "?")
        label = fd.get("label", fd["name"])
        default = ""
        if fd["name"] in defaults.get("front", []):
            default = " [default: front]"
        elif fd["name"] in defaults.get("back", []):
            default = " [default: back]"
        print(f"  {i}. {label} ({lang}){default}")

    # Field assignment.
    print(f"\nAssign fields to faces (comma-separated numbers, or Enter for defaults):")

    def parse_field_input(prompt, default_names):
        default_str = ",".join(str(i + 1) for i, fd in enumerate(displayable)
                               if fd["name"] in default_names) or "none"
        raw = input(f"  {prompt} [{default_str}]: ").strip()
        if not raw:
            return default_names
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            return [displayable[i]["name"] for i in indices if 0 <= i < len(displayable)]
        except (ValueError, IndexError):
            print("  Invalid input, using defaults.")
            return default_names

    front = parse_field_input("Front", defaults.get("front", []))
    back = parse_field_input("Back", defaults.get("back", []))

    both_default = list(dict.fromkeys(front + back))
    both = parse_field_input("Both", both_default)

    # Timing.
    print(f"\nTiming (seconds per phase, or Enter for defaults):")
    def parse_int_input(prompt, default):
        raw = input(f"  {prompt} [{default}]: ").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    t_front = parse_int_input("Front", defaults.get("timing_front_s", 10))
    t_back = parse_int_input("Back", defaults.get("timing_back_s", 10))
    t_both = parse_int_input("Both", defaults.get("timing_both_s", 5))

    # Cycle mode.
    print(f"\nCycle mode:")
    print(f"  1. front/back (two phases per card)")
    print(f"  2. front/back/both (three phases per card)")
    mode_raw = input(f"  Select [1]: ").strip()
    cycle_mode = "front_back_both" if mode_raw == "2" else "front_back"

    session = {
        "deck_id": deck_id,
        "deck_path": deck_info["path"],
        "display": {
            "front": front,
            "back": back,
            "both": both,
            "timing_front_s": t_front,
            "timing_back_s": t_back,
            "timing_both_s": t_both,
            "cycle_mode": cycle_mode,
        },
    }
    save_session(session)

    # Clear any existing state so it starts fresh.
    if STATE_FILE.exists():
        STATE_FILE.unlink()

    print(f"\nSession saved. Deck: {deck['name']}")
    print(f"  Front: {', '.join(front)}")
    print(f"  Back:  {', '.join(back)}")
    print(f"  Both:  {', '.join(both)}")
    print(f"  Timing: {t_front}s / {t_back}s / {t_both}s")
    print(f"  Cycle: {cycle_mode}")
    print(f"\nAdd refreshInterval to your Claude Code statusLine config to enable cycling.")


def list_decks(args):
    """List available decks."""
    decks = find_decks()
    if not decks:
        print(f"No decks found in {DATA_DIR}")
        return
    for did, info in decks.items():
        print(f"  {did}: {info['name']}")


def status(args):
    """Show current session state."""
    session = load_session()
    if not session:
        print("No session configured. Run with --configure first.")
        return

    print(f"Deck: {session['deck_id']}")
    print(f"Path: {session.get('deck_path')}")
    disp = session.get("display", {})
    print(f"Front: {disp.get('front')}")
    print(f"Back:  {disp.get('back')}")
    print(f"Both:  {disp.get('both')}")
    print(f"Timing: {disp.get('timing_front_s')}s / {disp.get('timing_back_s')}s / {disp.get('timing_both_s')}s")

    state = load_state()
    if state:
        print(f"\nState:")
        print(f"  Card position: {state.get('card_position')} / {len(state.get('card_order', []))}")
        print(f"  Phase: {state.get('phase')}")
        elapsed = time.time() - state.get("phase_started_at", 0)
        print(f"  Phase elapsed: {elapsed:.0f}s")


def main():
    parser = argparse.ArgumentParser(description="Wrenshoe ambient flashcard cycler")
    parser.add_argument("--render", action="store_true", default=True,
                        help="Render current card face (default)")
    parser.add_argument("--configure", action="store_true",
                        help="Interactive session setup")
    parser.add_argument("--list-decks", action="store_true",
                        help="List available decks")
    parser.add_argument("--status", action="store_true",
                        help="Show current session state")
    args = parser.parse_args()

    if args.configure:
        configure(args)
    elif args.list_decks:
        list_decks(args)
    elif args.status:
        status(args)
    else:
        render(args)


if __name__ == "__main__":
    main()
