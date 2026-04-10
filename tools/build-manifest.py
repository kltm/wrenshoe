#!/usr/bin/env python3
"""Generate deck-manifest.json for the Wrenshoe web app.

Scans data/*.json and writes a lightweight manifest to docs/deck-manifest.json
containing just enough metadata to render the deck picker without loading every
deck file up front.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / 'data'
OUTPUT = REPO / 'docs' / 'deck-manifest.json'


def main():
    manifest = []
    for f in sorted(DATA_DIR.glob('*.json')):
        try:
            with open(f, encoding='utf-8') as fh:
                deck = json.load(fh)
            manifest.append({
                'id': deck['id'],
                'name': deck['name'],
                'description': deck.get('description', ''),
                'source_language': deck.get('source_language', ''),
                'filename': f.name,
                'card_count': len(deck.get('cards') or []),
            })
        except (json.JSONDecodeError, KeyError) as e:
            print(f'Warning: skipping {f.name}: {e}', file=sys.stderr)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write('\n')

    print(f'Generated {OUTPUT} with {len(manifest)} decks')


if __name__ == '__main__':
    main()
