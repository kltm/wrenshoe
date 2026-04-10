#!/usr/bin/env python3
"""Build Korean hangul reading practice decks from cc-kedict.

Source: mhagiwara/cc-kedict (CC-BY-SA 3.0).

Usage:
  python3 build-korean-decks.py <kedict.yml> <output-dir>
"""

import json
import sys
from pathlib import Path

import yaml


def build_korean_deck(kedict_path, output_dir):
    with open(kedict_path, encoding="utf-8") as f:
        entries = yaml.safe_load(f)

    cards = []
    seen = set()

    for entry in entries:
        word = str(entry.get("word", "")).strip()
        romaja = str(entry.get("romaja") or "").strip()
        if not word or not romaja:
            continue

        # Skip pure punctuation or single-character particles that
        # aren't useful for sight-reading practice.
        if len(word) < 2 and not any('\uAC00' <= c <= '\uD7A3' for c in word):
            continue

        # Deduplicate by word form.
        if word in seen:
            continue
        seen.add(word)

        defs = entry.get("defs") or []
        meanings = []
        for d in defs:
            defn = d.get("def", "").strip()
            if defn:
                # Clean up leading colons from some entries.
                defn = defn.lstrip("':").strip()
                if defn:
                    meanings.append(defn)

        if not meanings:
            continue

        meaning = "; ".join(meanings[:3])  # Cap at 3 senses for readability.

        card = {
            "field_values": [
                {"field": "hangul", "value": word},
                {"field": "romanization", "value": romaja},
                {"field": "meaning", "value": meaning},
            ]
        }

        pos = entry.get("pos", "")
        if pos:
            card["tags"] = [pos]

        cards.append(card)

    deck = {
        "id": "korean_hangul",
        "name": "Korean Hangul Reading Practice (한글)",
        "description": (
            "Korean vocabulary for hangul sight-reading practice. "
            "Source: mhagiwara/cc-kedict (CC-BY-SA 3.0)."
        ),
        "source_language": "ko",
        "field_definitions": [
            {
                "name": "hangul",
                "label": "Hangul",
                "language": "ko",
                "field_type": "representation",
                "default_face": "front",
            },
            {
                "name": "romanization",
                "label": "Romanization",
                "language": "ko-Latn",
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
            "front": ["hangul"],
            "back": ["romanization", "meaning"],
        },
        "cards": cards,
    }

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(output_dir) / "korean_hangul.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"  Korean Hangul: {len(cards)} cards -> {out_path}")


def main():
    if len(sys.argv) != 3:
        print("Usage: build-korean-decks.py <kedict.yml> <output-dir>", file=sys.stderr)
        sys.exit(1)

    build_korean_deck(sys.argv[1], sys.argv[2])
    print("\nDone.")


if __name__ == "__main__":
    main()
