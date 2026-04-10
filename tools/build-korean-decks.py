#!/usr/bin/env python3
"""Build a curated Korean hangul reading practice deck from cc-kedict.

Selects food and elementary vocabulary to maximize hangul jamo coverage
for sight-reading practice.

Source: mhagiwara/cc-kedict (CC-BY-SA 3.0).

Usage:
  python3 build-korean-decks.py <kedict.yml> <output-dir>
"""

import json
import re
import sys
from pathlib import Path

import yaml

# Hangul jamo decomposition tables.
CHOSEONG = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
JUNGSEONG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
JONGSEONG_LIST = [""] + list("ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ")


def decompose(char):
    """Decompose a hangul syllable into (choseong, jungseong, jongseong)."""
    code = ord(char) - 0xAC00
    if code < 0 or code > 11171:
        return None
    cho = code // (21 * 28)
    jung = (code % (21 * 28)) // 28
    jong = code % 28
    return (CHOSEONG[cho], JUNGSEONG[jung], JONGSEONG_LIST[jong])


def jamo_set(word):
    """Return set of (type, jamo) tuples for coverage tracking."""
    s = set()
    for ch in word:
        d = decompose(ch)
        if d:
            s.add(("cho", d[0]))
            s.add(("jung", d[1]))
            if d[2]:
                s.add(("jong", d[2]))
    return s


# Topic keywords for filtering.
FOOD_KW = [
    'food', 'eat', 'drink', 'rice', 'meat', 'fish', 'chicken', 'pork', 'beef',
    'vegetable', 'fruit', 'cook', 'restaurant', 'soup', 'noodle', 'kimchi',
    'bread', 'milk', 'water', 'tea', 'coffee', 'egg', 'salt', 'sugar',
    'pepper', 'oil', 'sauce', 'spicy', 'sweet', 'sour', 'bitter', 'delicious',
    'taste', 'hungry', 'meal', 'breakfast', 'lunch', 'dinner', 'snack',
    'dessert', 'cake', 'apple', 'banana', 'orange', 'grape', 'onion', 'garlic',
    'tofu', 'bean', 'mushroom', 'potato', 'carrot', 'tomato', 'cheese',
    'butter', 'wine', 'beer', 'juice', 'bowl', 'plate', 'chopstick', 'spoon',
    'knife', 'fork', 'glass', 'bottle', 'menu', 'order', 'boil', 'fry',
    'grill', 'bake', 'cut', 'slice', 'pour', 'mix', 'stir', 'flour', 'noodles',
    'seafood', 'shrimp', 'crab', 'seaweed', 'pickle', 'ferment', 'soy',
    'sesame', 'radish', 'cabbage', 'lettuce', 'cucumber', 'peach', 'pear',
    'melon', 'strawberry', 'cherry',
]
ELEM_KW = [
    'hello', 'goodbye', 'thank', 'please', 'sorry', 'yes', 'no', 'good',
    'bad', 'big', 'small', 'hot', 'cold', 'new', 'old', 'many', 'few',
    'fast', 'slow', 'person', 'man', 'woman', 'child', 'friend', 'family',
    'mother', 'father', 'sister', 'brother', 'name', 'age', 'house', 'school',
    'work', 'money', 'time', 'day', 'night', 'morning', 'today', 'tomorrow',
    'yesterday', 'week', 'month', 'year', 'number', 'one', 'two', 'three',
    'four', 'five', 'color', 'red', 'blue', 'white', 'black', 'green',
    'yellow', 'go', 'come', 'see', 'know', 'want', 'like', 'love', 'speak',
    'read', 'write', 'learn', 'teach', 'buy', 'sell', 'give', 'take', 'open',
    'close', 'sleep', 'walk', 'run', 'sit', 'stand', 'wait', 'help', 'think',
    'feel', 'happy', 'sad', 'beautiful', 'right', 'left', 'country', 'city',
    'street', 'store', 'hospital', 'station', 'book', 'door', 'window',
    'table', 'chair', 'clothes', 'body', 'head', 'hand', 'eye', 'ear',
    'mouth', 'heart', 'rain', 'snow', 'sun', 'moon', 'sky', 'tree', 'flower',
    'mountain', 'river', 'sea', 'animal', 'dog', 'cat', 'bird',
]
ALL_KW = set(w.lower() for w in FOOD_KW + ELEM_KW)


def build_korean_deck(kedict_path, output_dir):
    with open(kedict_path, encoding="utf-8") as f:
        entries = yaml.safe_load(f)

    # Score and filter entries.
    candidates = []
    seen_words = set()

    for entry in entries:
        word = str(entry.get("word", "")).strip()
        romaja = str(entry.get("romaja") or "").strip()
        if not word or not romaja:
            continue
        if not any("\uAC00" <= c <= "\uD7A3" for c in word):
            continue
        # Skip conjugated forms (keep base/dictionary forms).
        # Heuristic: skip if word is > 5 syllables (likely a conjugation or compound).
        hangul_chars = [c for c in word if "\uAC00" <= c <= "\uD7A3"]
        if len(hangul_chars) > 5:
            continue
        # Deduplicate.
        if word in seen_words:
            continue
        seen_words.add(word)

        defs = entry.get("defs") or []
        meanings = []
        for d in defs:
            defn = str(d.get("def", "")).strip().lstrip("':").strip()
            if defn:
                meanings.append(defn)
        if not meanings:
            continue

        meaning_text = " ".join(meanings).lower()
        score = sum(
            1 for kw in ALL_KW
            if re.search(r"\b" + re.escape(kw) + r"\b", meaning_text)
        )
        if score > 0:
            candidates.append({
                "word": word,
                "romaja": romaja,
                "meaning": "; ".join(meanings[:2]),
                "pos": entry.get("pos", ""),
                "score": score,
                "jamo": jamo_set(word),
            })

    # Greedy selection: pick high-scoring words, prioritizing jamo coverage.
    candidates.sort(key=lambda x: -x["score"])

    selected = []
    covered_jamo = set()
    target_cho = set(("cho", j) for j in CHOSEONG)
    target_jung = set(("jung", j) for j in JUNGSEONG)
    all_target = target_cho | target_jung

    # First pass: greedily pick words that add new jamo coverage.
    remaining = list(candidates)
    while remaining and len(selected) < 350:
        # Score by: new jamo added, then original keyword score.
        best_idx = 0
        best_new = 0
        for i, c in enumerate(remaining):
            new_jamo = len(c["jamo"] - covered_jamo)
            if new_jamo > best_new or (new_jamo == best_new and c["score"] > remaining[best_idx]["score"]):
                best_idx = i
                best_new = new_jamo
        if best_new == 0 and len(selected) >= 200:
            break  # Good enough coverage, stop adding.
        chosen = remaining.pop(best_idx)
        selected.append(chosen)
        covered_jamo |= chosen["jamo"]

    # Report coverage.
    cho_covered = set(j for t, j in covered_jamo if t == "cho")
    jung_covered = set(j for t, j in covered_jamo if t == "jung")
    jong_covered = set(j for t, j in covered_jamo if t == "jong")
    print(f"  Initial consonants: {len(cho_covered)}/{len(CHOSEONG)}")
    print(f"  Vowels: {len(jung_covered)}/{len(JUNGSEONG)}")
    print(f"  Final consonants: {len(jong_covered)}/{len(JONGSEONG_LIST)-1}")
    missing_jung = set(JUNGSEONG) - jung_covered
    if missing_jung:
        print(f"  Missing vowels: {', '.join(sorted(missing_jung))}")

    # Build deck.
    cards = []
    for entry in selected:
        card = {
            "field_values": [
                {"field": "hangul", "value": entry["word"]},
                {"field": "romanization", "value": entry["romaja"]},
                {"field": "meaning", "value": entry["meaning"]},
            ]
        }
        if entry["pos"]:
            card["tags"] = [entry["pos"]]
        cards.append(card)

    deck = {
        "id": "korean_hangul",
        "name": "Korean Hangul Reading Practice (한글)",
        "description": (
            "Curated Korean food and elementary vocabulary for hangul sight-reading practice. "
            "Selected for maximum hangul jamo coverage. "
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

    print(f"\n  Korean Hangul: {len(cards)} cards -> {out_path}")


def main():
    if len(sys.argv) != 3:
        print("Usage: build-korean-decks.py <kedict.yml> <output-dir>", file=sys.stderr)
        sys.exit(1)

    build_korean_deck(sys.argv[1], sys.argv[2])
    print("\nDone.")


if __name__ == "__main__":
    main()
