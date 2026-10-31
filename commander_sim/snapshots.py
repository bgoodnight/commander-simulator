"""Validate a versioned offline Scryfall snapshot against its exact deck file.

Identity verification is separate from effect or target-rule support. This
module never downloads data and never creates or casts a game object.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from .decks import DeckProvider

@dataclass(frozen=True)
class ValidatedSnapshot:
    deck: object
    deck_sha256: str
    snapshot_sha256: str
    source: str
    retrieved_at: str
    cards: tuple


def validate_snapshot(deck_path, snapshot_path, *, commander='Magnus the Red'):
    deck_bytes = Path(deck_path).read_bytes()
    snapshot_bytes = Path(snapshot_path).read_bytes()
    data = json.loads(snapshot_bytes)
    digest = hashlib.sha256(deck_bytes).hexdigest()
    if data.get('deck_sha256') != digest:
        raise ValueError('Snapshot deck hash does not match deck file')
    if data.get('problems') or not data.get('source') or not data.get('retrieved_at'):
        raise ValueError('Snapshot is incomplete or missing provenance')
    entries = data.get('cards')
    if not isinstance(entries, list) or len(entries) != data.get('distinct_requested'):
        raise ValueError('Snapshot card count does not match request')
    rows = []
    for item in entries:
        card = item.get('card', {})
        name = card.get('name'); listed = item.get('deck_name')
        faces = card.get('card_faces', [])
        if not isinstance(name, str) or (listed != name and listed not in [f.get('name') for f in faces]):
            raise ValueError(f'Snapshot name mismatch: {listed!r}')
        if (not isinstance(card.get('cmc'), (int, float)) or isinstance(card.get('cmc'), bool)
            or card['cmc'] < 0 or not isinstance(card.get('keywords'), list)
            or not isinstance(card.get('layout'), str) or not card.get('scryfall_uri')):
            raise ValueError(f'Incomplete characteristics: {name}')
        row = {'name':name, 'oracle_id':card.get('oracle_id'), 'type_line':card.get('type_line'),
               'color_identity':card.get('color_identity'),
               'commander_legality':card.get('legalities', {}).get('commander')}
        # A deck may name a reviewed face of a modal DFC, transform card,
        # Adventure, etc. Preserve the actual listed face alias rather than
        # assuming only the "adventure" layout can have a different parent
        # Oracle name. The identity remains one canonical Oracle object.
        if listed != name and listed in [f.get('name') for f in faces]:
            row['deck_name'] = listed
            row['card_faces'] = faces
        rows.append(row)
    commanders = [row for row in rows if row['name'] == commander]
    if len(commanders) != 1:
        raise ValueError('Commander missing or ambiguous in snapshot')
    commander_row = commanders[0]
    type_line = commander_row.get('type_line')
    words = set(type_line.split(' — ', 1)[0].split()) if isinstance(type_line,str) else set()
    if not {'Legendary','Creature'} <= words:
        raise ValueError('Only a verified legendary creature commander is supported')
    identity=commander_row.get('color_identity')
    if not isinstance(identity,list) or any(not isinstance(c,str) or len(c)!=1 or c not in 'WUBRG' for c in identity):
        raise ValueError('Commander color identity is missing or invalid')
    provider = DeckProvider(rows, commander=commander, color_identity=frozenset(identity))
    deck = provider.parse(deck_bytes.decode('utf-8'))
    return ValidatedSnapshot(deck, digest, hashlib.sha256(snapshot_bytes).hexdigest(),
                             data['source'], data['retrieved_at'], tuple(entries))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('deck'); parser.add_argument('snapshot')
    parser.add_argument('--commander', default='Magnus the Red', help='Explicit verified legendary creature commander')
    args = parser.parse_args()
    try:
        result = validate_snapshot(args.deck, args.snapshot, commander=args.commander)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps({'commander': result.deck.commander, 'physical_cards': result.deck.count,
                      'distinct_names': len(result.cards), 'deck_sha256': result.deck_sha256,
                      'snapshot_sha256': result.snapshot_sha256, 'source': result.source,
                      'retrieved_at': result.retrieved_at,
                      'effects': 'not assessed by identity validation'}, indent=2))
