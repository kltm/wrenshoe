#!/usr/bin/env python3
"""Convert legacy Wrenshoe .meta/.data deck pairs to the new JSON format."""

import json
import sys
from pathlib import Path

# Deck-specific configuration: maps old column names to new field definitions.
# Each entry: (name, label, language, field_type, displayable, default_face)
DECK_FIELD_MAPS = {
    "kb_net_vocab": {
        "columns": {
            "word":      ("word",      "Word (かな)",        "ja-x-kansai",      "representation", True,  "front"),
            "meaning":   ("meaning",   "Meaning",            "en",               "sense",          True,  "back"),
            "kanji":     ("kanji",     "Kanji",              "ja-x-kansai",      "representation", True,  "front"),
            "std. word": ("std_word",  "Std. Word (かな)",   "ja",               "representation", True,  None),
            "std. kanji":("std_kanji", "Std. Kanji",         "ja",               "representation", True,  None),
            "link":      ("link",      "Reference",          "en",               "reference",      False, None),
        },
        "source_language": "ja-x-kansai",
    },
    "q_hiragana": {
        "columns": {
            "Glyph": ("glyph", "Glyph",         "ja-Hira", "representation", True,  "front"),
            "Gloss": ("gloss", "Romanization",   "ja-Latn", "representation", True,  "back"),
        },
        "tag_columns": ["Level"],
        "source_language": "ja",
    },
    "q_katakana": {
        "columns": {
            "Glyph": ("glyph", "Glyph",         "ja-Kana", "representation", True,  "front"),
            "Gloss": ("gloss", "Romanization",   "ja-Latn", "representation", True,  "back"),
        },
        "tag_columns": ["Level"],
        "source_language": "ja",
    },
    "v_k_ccc": {
        "columns": {
            "Pinyin":     ("pinyin",     "Pinyin",     "zh-Latn", "representation", True,  "back"),
            "English":    ("english",    "English",    "en",      "sense",          True,  "back"),
            "Characters": ("characters", "Characters", "zh-Hans", "representation", True,  "front"),
        },
        "tag_columns": ["Tags"],
        "source_language": "zh",
    },
}


def convert_deck(meta_path: Path, data_path: Path) -> dict:
    """Convert a legacy .meta/.data pair to new format."""

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    deck_id = meta["id"]
    if deck_id not in DECK_FIELD_MAPS:
        print(f"Error: no field map configured for deck '{deck_id}'", file=sys.stderr)
        sys.exit(1)

    config = DECK_FIELD_MAPS[deck_id]
    col_map = config["columns"]
    tag_col_names = config.get("tag_columns", [])

    # Build ordered list of old column names from meta.
    old_columns = [(c["name"], c["type"]) for c in meta["columns"]]

    # Build field definitions for the new deck.
    field_defs = []
    for old_name, old_type in old_columns:
        if old_type == "tag":
            continue  # tags handled separately
        if old_name not in col_map:
            print(f"Warning: unmapped column '{old_name}' in {deck_id}", file=sys.stderr)
            continue
        name, label, lang, ftype, displayable, default_face = col_map[old_name]
        fd = {
            "name": name,
            "label": label,
            "language": lang,
            "field_type": ftype,
        }
        if not displayable:
            fd["displayable"] = False
        if default_face is not None:
            fd["default_face"] = default_face
        field_defs.append(fd)

    # Build default display from field definitions.
    front_fields = [fd["name"] for fd in field_defs if fd.get("default_face") == "front"]
    back_fields = [fd["name"] for fd in field_defs if fd.get("default_face") == "back"]
    suppress_fields = [fd["name"] for fd in field_defs
                       if fd.get("displayable") is False or fd.get("default_face") is None]

    default_display = {
        "front": front_fields,
        "back": back_fields,
    }
    if suppress_fields:
        default_display["suppress"] = suppress_fields

    # Parse data file (tab-separated).
    cards = []
    with open(data_path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.rstrip("\n\r")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != len(old_columns):
                print(f"Warning: line {line_no} has {len(parts)} cols, "
                      f"expected {len(old_columns)}", file=sys.stderr)
                continue

            field_values = []
            tags = []

            for i, (old_name, old_type) in enumerate(old_columns):
                val = parts[i].strip()
                if old_type == "tag":
                    # Split comma-separated tags.
                    for t in val.split(","):
                        t = t.strip()
                        if t:
                            tags.append(t)
                elif old_name in col_map:
                    new_name = col_map[old_name][0]
                    field_values.append({"field": new_name, "value": val})

            card = {"field_values": field_values}
            if tags:
                card["tags"] = tags
            cards.append(card)

    deck = {
        "id": deck_id,
        "name": meta["name"],
        "source_language": config["source_language"],
        "field_definitions": field_defs,
        "default_display": default_display,
        "cards": cards,
    }
    if meta.get("description"):
        deck["description"] = meta["description"]

    return deck


def main():
    if len(sys.argv) < 2:
        print("Usage: convert-legacy.py <path/to/deckname.meta> [...]", file=sys.stderr)
        sys.exit(1)

    for meta_path_str in sys.argv[1:]:
        meta_path = Path(meta_path_str)
        data_path = meta_path.with_suffix(".data")

        if not meta_path.exists():
            print(f"Error: {meta_path} not found", file=sys.stderr)
            continue
        if not data_path.exists():
            print(f"Error: {data_path} not found", file=sys.stderr)
            continue

        deck = convert_deck(meta_path, data_path)
        out_name = meta_path.stem + ".json"
        out_path = Path("data") / out_name

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
            f.write("\n")

        print(f"Converted {meta_path.stem}: {len(deck['cards'])} cards -> {out_path}")


if __name__ == "__main__":
    main()
