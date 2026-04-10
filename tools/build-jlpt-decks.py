#!/usr/bin/env python3
"""Build JLPT N5-N1 vocabulary decks and kanji-by-grade decks from JMdict, KANJIDIC2, and JLPT word lists.

Sources:
  - JMdict (CC-BY-SA 4.0, EDRDG/Jim Breen) via scriptin/jmdict-simplified
  - KANJIDIC2 (CC-BY-SA 4.0, EDRDG/Jim Breen) via scriptin/jmdict-simplified
  - JLPT word lists (MIT, derived from Jonathan Waller CC-BY) via jamsinclair/open-anki-jlpt-decks

Usage:
  python3 build-jlpt-decks.py <jmdict.json> <kanjidic2.json> <jlpt-csv-dir> <output-dir>
"""

import csv
import json
import sys
from pathlib import Path


def load_jlpt_words(csv_dir):
    """Load JLPT word lists, return dict: expression -> {level, reading, meaning}."""
    jlpt = {}
    for level in ["n5", "n4", "n3", "n2", "n1"]:
        csv_path = Path(csv_dir) / f"{level}.csv"
        if not csv_path.exists():
            print(f"Warning: {csv_path} not found", file=sys.stderr)
            continue
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                expr = row["expression"].strip()
                # Only store if not already seen at a lower (easier) level.
                if expr not in jlpt:
                    jlpt[expr] = {
                        "level": level.upper(),
                        "reading": row["reading"].strip(),
                        "meaning": row["meaning"].strip(),
                    }
    return jlpt


def build_jlpt_vocab_decks(jlpt_words, output_dir):
    """Build one wrenshoe deck per JLPT level."""
    levels = {"N5": [], "N4": [], "N3": [], "N2": [], "N1": []}

    for expr, info in jlpt_words.items():
        level = info["level"]
        card = {
            "field_values": [
                {"field": "word", "value": expr},
                {"field": "reading", "value": info["reading"]},
                {"field": "meaning", "value": info["meaning"]},
            ]
        }
        if level in levels:
            levels[level].append(card)

    counts = {}
    for level, cards in levels.items():
        deck = {
            "id": f"jlpt_{level.lower()}",
            "name": f"JLPT {level} Vocabulary",
            "description": (
                f"Japanese vocabulary for JLPT {level}. "
                f"Sources: JLPT word lists (Jonathan Waller, CC-BY) via jamsinclair/open-anki-jlpt-decks (MIT), "
                f"cross-referenced with JMdict (EDRDG, CC-BY-SA 4.0)."
            ),
            "source_language": "ja",
            "field_definitions": [
                {
                    "name": "word",
                    "label": "Word",
                    "language": "ja",
                    "field_type": "representation",
                    "default_face": "front",
                },
                {
                    "name": "reading",
                    "label": "Reading",
                    "language": "ja-Hira",
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
                "front": ["word"],
                "back": ["reading", "meaning"],
            },
            "cards": cards,
        }

        out_path = Path(output_dir) / f"jlpt_{level.lower()}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
            f.write("\n")

        counts[level] = len(cards)
        print(f"  JLPT {level}: {len(cards)} cards -> {out_path}")

    return counts


def build_kanji_decks(kanjidic_path, output_dir):
    """Build kanji-by-grade decks from KANJIDIC2."""
    with open(kanjidic_path, encoding="utf-8") as f:
        data = json.load(f)

    grade_map = {
        1: ("grade_1", "Grade 1 Kanji (Kanken 10)"),
        2: ("grade_2", "Grade 2 Kanji (Kanken 9)"),
        3: ("grade_3", "Grade 3 Kanji (Kanken 8)"),
        4: ("grade_4", "Grade 4 Kanji (Kanken 7)"),
        5: ("grade_5", "Grade 5 Kanji (Kanken 6)"),
        6: ("grade_6", "Grade 6 Kanji (Kanken 5)"),
        8: ("jouyou_secondary", "Jouyou Kanji (Secondary School)"),
    }

    grades = {g: [] for g in grade_map}

    for char in data["characters"]:
        grade = char["misc"].get("grade")
        if grade not in grade_map:
            continue

        rm = char.get("readingMeaning", {})
        on_readings = []
        kun_readings = []
        meanings = []

        for group in rm.get("groups", []):
            for r in group.get("readings", []):
                if r["type"] == "ja_on":
                    on_readings.append(r["value"])
                elif r["type"] == "ja_kun":
                    kun_readings.append(r["value"])
            for m in group.get("meanings", []):
                meanings.append(m["value"])

        card = {
            "field_values": [
                {"field": "kanji", "value": char["literal"]},
                {"field": "on_reading", "value": "、".join(on_readings) if on_readings else "n/a"},
                {"field": "kun_reading", "value": "、".join(kun_readings) if kun_readings else "n/a"},
                {"field": "meaning", "value": "; ".join(meanings) if meanings else "n/a"},
            ]
        }

        jlpt = char["misc"].get("jlptLevel")
        if jlpt:
            card["tags"] = [f"JLPT-old-{jlpt}"]

        freq = char["misc"].get("frequency")
        if freq:
            card["tags"] = card.get("tags", []) + [f"freq-{freq}"]

        grades[grade].append(card)

    counts = {}
    for grade, (deck_id, deck_name) in grade_map.items():
        cards = grades[grade]
        if not cards:
            continue

        deck = {
            "id": deck_id,
            "name": deck_name,
            "description": (
                f"Kanji taught in Japanese schools at grade level {grade}. "
                f"Source: KANJIDIC2 (EDRDG/Jim Breen, CC-BY-SA 4.0) via scriptin/jmdict-simplified."
            ),
            "source_language": "ja",
            "field_definitions": [
                {
                    "name": "kanji",
                    "label": "Kanji",
                    "language": "ja",
                    "field_type": "representation",
                    "default_face": "front",
                },
                {
                    "name": "on_reading",
                    "label": "On'yomi",
                    "language": "ja-Kana",
                    "field_type": "representation",
                    "default_face": "back",
                },
                {
                    "name": "kun_reading",
                    "label": "Kun'yomi",
                    "language": "ja-Hira",
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
                "front": ["kanji"],
                "back": ["on_reading", "kun_reading", "meaning"],
            },
            "cards": cards,
        }

        out_path = Path(output_dir) / f"kanji_{deck_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
            f.write("\n")

        counts[deck_name] = len(cards)
        print(f"  {deck_name}: {len(cards)} kanji -> {out_path}")

    return counts


def main():
    if len(sys.argv) != 5:
        print("Usage: build-jlpt-decks.py <jmdict.json> <kanjidic2.json> <jlpt-csv-dir> <output-dir>",
              file=sys.stderr)
        sys.exit(1)

    jmdict_path, kanjidic_path, jlpt_csv_dir, output_dir = sys.argv[1:5]
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("Loading JLPT word lists...")
    jlpt_words = load_jlpt_words(jlpt_csv_dir)
    print(f"  Loaded {len(jlpt_words)} unique JLPT words")

    print("\nBuilding JLPT vocabulary decks...")
    vocab_counts = build_jlpt_vocab_decks(jlpt_words, output_dir)

    print("\nBuilding kanji-by-grade decks...")
    kanji_counts = build_kanji_decks(kanjidic_path, output_dir)

    print("\nDone.")


if __name__ == "__main__":
    main()
