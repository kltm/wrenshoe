#!/usr/bin/env python3
"""Build HSK vocabulary decks from drkameleon/complete-hsk-vocabulary.

Source: drkameleon/complete-hsk-vocabulary (MIT license).
Underlying dictionary data from CC-CEDICT (CC-BY-SA 4.0).

Usage:
  python3 build-hsk-decks.py <complete.json> <output-dir>
"""

import json
import sys
from pathlib import Path


def build_hsk_decks(data_path, output_dir):
    with open(data_path, encoding="utf-8") as f:
        entries = json.load(f)

    # Build decks for old HSK 1-6 (widely used).
    level_prefix = "old-"
    level_names = {
        "old-1": ("hsk_1", "HSK 1"),
        "old-2": ("hsk_2", "HSK 2"),
        "old-3": ("hsk_3", "HSK 3"),
        "old-4": ("hsk_4", "HSK 4"),
        "old-5": ("hsk_5", "HSK 5"),
        "old-6": ("hsk_6", "HSK 6"),
    }

    decks = {lv: [] for lv in level_names}

    for entry in entries:
        levels = entry.get("level", [])
        # Find which old-HSK levels this word belongs to.
        for lv in levels:
            if lv not in level_names:
                continue

            simplified = entry["simplified"]
            forms = entry.get("forms", [])
            if not forms:
                continue

            # Use first form for pinyin and meaning.
            form = forms[0]
            pinyin = form.get("transcriptions", {}).get("pinyin", "")
            meanings_list = form.get("meanings", [])
            meaning = "; ".join(meanings_list) if meanings_list else "n/a"

            card = {
                "field_values": [
                    {"field": "characters", "value": simplified},
                    {"field": "pinyin", "value": pinyin},
                    {"field": "meaning", "value": meaning},
                ]
            }

            pos = entry.get("pos", [])
            if pos:
                card["tags"] = pos

            decks[lv].append(card)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for lv, (deck_id, deck_name) in level_names.items():
        cards = decks[lv]
        if not cards:
            continue

        deck = {
            "id": deck_id,
            "name": f"{deck_name} Vocabulary (汉语水平考试)",
            "description": (
                f"Mandarin Chinese vocabulary for {deck_name}. "
                f"Source: drkameleon/complete-hsk-vocabulary (MIT), "
                f"derived from CC-CEDICT (CC-BY-SA 4.0)."
            ),
            "source_language": "zh",
            "field_definitions": [
                {
                    "name": "characters",
                    "label": "Characters",
                    "language": "zh-Hans",
                    "field_type": "representation",
                    "default_face": "front",
                },
                {
                    "name": "pinyin",
                    "label": "Pinyin",
                    "language": "zh-Latn",
                    "field_type": "representation",
                    "default_face": "back",
                },
                {
                    "name": "meaning",
                    "label": "Meaning",
                    "language": "en",
                    "field_type": "sense",
                    "default_face": "back",
                },
            ],
            "default_display": {
                "front": ["characters"],
                "back": ["pinyin", "meaning"],
            },
            "cards": cards,
        }

        out_path = Path(output_dir) / f"{deck_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
            f.write("\n")

        print(f"  {deck_name}: {len(cards)} cards -> {out_path}")


def main():
    if len(sys.argv) != 3:
        print("Usage: build-hsk-decks.py <complete.json> <output-dir>", file=sys.stderr)
        sys.exit(1)

    build_hsk_decks(sys.argv[1], sys.argv[2])
    print("\nDone.")


if __name__ == "__main__":
    main()
