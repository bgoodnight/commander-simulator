"""Fetch an exact-name Scryfall snapshot for a deck, outside simulation runs.

Usage: python tools/fetch_deck_identities.py DECK OUTPUT
The output preserves original API objects and missing/error diagnostics. It is
not evidence that a card's game effects are implemented.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch(deck_path, output):
    data = deck_path.read_bytes()
    names = list(dict.fromkeys(m[2] for line in data.decode('utf-8').splitlines()
                 if (m := re.fullmatch(r'([1-9]\d*) (.+)', line.strip()))))
    cards, problems = [], []
    for offset in range(0, len(names), 75):
        batch = names[offset:offset+75]
        payload = json.dumps({'identifiers': [{'name': name.split(' // ', 1)[0]} for name in batch]}).encode()
        request = Request('https://api.scryfall.com/cards/collection', data=payload,
                          headers={'User-Agent': 'CommanderSimulator/1.0 (offline deck identity snapshot)',
                                   'Accept': 'application/json', 'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=45) as response:
                result = json.load(response)
            returned = result.get('data', [])
            for name in batch:
                matches = [card for card in returned if card.get('name') == name or
                           name in [face.get('name') for face in card.get('card_faces', [])]]
                if len(matches) == 1:
                    cards.append({'deck_name': name, 'card': matches[0]})
                else:
                    problems.append({'name': name, 'error': f'expected one exact card/face, found {len(matches)}'})
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            problems.extend({'name': name, 'error': str(exc)} for name in batch)
        time.sleep(.12)
    result = {'source': 'Scryfall collection API, exact card/face match',
              'retrieved_at': datetime.now(timezone.utc).isoformat(),
              'deck_sha256': hashlib.sha256(data).hexdigest(),
              'distinct_requested': len(names), 'cards': cards, 'problems': problems}
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({'requested': len(names), 'retrieved': len(cards), 'problems': problems}, indent=2))
    return not problems

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('deck', type=Path); parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if fetch(args.deck, args.output) else 1)
