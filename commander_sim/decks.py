"""Validated deck composition; independent of any simulation engine.

Metadata must come from a trusted, locally supplied identity snapshot. A valid
composition does not imply that the simulator implements the cards' effects.
"""
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import re
from types import MappingProxyType

_ROOT = Path(__file__).resolve().parents[1]
PRESETS = MappingProxyType({
    'premium': _ROOT / 'decklists/magnus_thousand_sons_v1_14_premium.txt',
    'budget': _ROOT / 'decklists/magnus_thousand_sons_v1_13_budget.txt',
})
_IDENTITY_FILES = (_ROOT / 'simulator/v20_verified_types/CARD_IDENTITIES.json',
                   _ROOT / 'simulator/v31_premium_deck/NEW_CARD_IDENTITIES.json')
_BASIC = frozenset({'Plains', 'Island', 'Swamp', 'Mountain', 'Forest', 'Wastes',
                    'Snow-Covered Plains', 'Snow-Covered Island', 'Snow-Covered Swamp',
                    'Snow-Covered Mountain', 'Snow-Covered Forest'})

@dataclass(frozen=True)
class Deck:
    commander: str
    cards: tuple  # (section, name, quantity), in file order

    @property
    def count(self):
        return sum(qty for _, _, qty in self.cards)

class DeckProvider:
    """Parse and validate Magnus lists; does not load or execute card effects."""
    def __init__(self, records):
        self._records = {}
        for row in records:
            name = row.get('name')
            if not isinstance(name, str) or not name or name in self._records:
                raise ValueError(f'Missing or duplicate metadata name: {name!r}')
            self._records[name] = dict(row)
            alias = row.get('deck_name')
            if alias is not None:
                faces = row.get('card_faces', [])
                if (not isinstance(alias, str) or alias == name or alias in self._records
                    or not any(isinstance(face, dict) and face.get('name') == alias for face in faces)):
                    raise ValueError(f'Invalid or duplicate deck name: {alias!r}')
                self._records[alias] = dict(row)

    @classmethod
    def bundled(cls):
        records = []
        for path in _IDENTITY_FILES:
            records.extend(json.loads(path.read_text(encoding='utf-8'))['cards'])
        return cls(records)

    def preset(self, name):
        if name not in PRESETS:
            raise ValueError(f'Unknown deck preset: {name}')
        return self.load(PRESETS[name])

    def load(self, path):
        return self.parse(Path(path).read_text(encoding='utf-8'))

    def parse(self, text):
        section = None
        cards = Counter()
        declared = None
        section_count = 0
        for number, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            if not line:
                continue
            heading = re.fullmatch(r'(Commander|Library|Creatures|Other Permanents|Instants and Sorceries|Lands)(?: \((\d+)\))?', line)
            if heading:
                if declared is not None and section_count != declared:
                    raise ValueError(f'Section count differs from declared {declared}')
                section = 'Commander' if heading[1] == 'Commander' else 'Library'
                declared = int(heading[2]) if heading[2] else None
                section_count = 0
                continue
            match = re.fullmatch(r'([1-9]\d*) (\S(?:.*\S)?)', line)
            if not match or section is None:
                raise ValueError(f'Invalid deck entry on line {number}: {line}')
            qty, name = int(match[1]), match[2]
            row = self._records.get(name)
            if row and row.get('deck_name'):
                name = row['deck_name']
            cards[section, name] += qty
            section_count += qty
        if declared is not None and section_count != declared:
            raise ValueError(f'Section count differs from declared {declared}')
        commander = [(name, qty) for (zone, name), qty in cards.items() if zone == 'Commander']
        if commander != [('Magnus the Red', 1)]:
            raise ValueError('Expected exactly one Magnus the Red commander')
        if sum(cards.values()) != 100:
            raise ValueError('Expected exactly 100 cards including commander')
        totals = Counter()
        for (_, name), qty in cards.items():
            totals[name] += qty
        ids = Counter()
        for name, qty in totals.items():
            row = self._records.get(name)
            if not row or row.get('status', 'valid') != 'valid':
                raise ValueError(f'Unverified card identity: {name}')
            identity, oracle_id = row.get('color_identity'), row.get('oracle_id')
            if (not isinstance(identity, list) or any(not isinstance(c, str) or len(c) != 1 or c not in 'WUBRG' for c in identity)
                or not isinstance(oracle_id, str) or not oracle_id
                or not isinstance(row.get('type_line'), str) or not row['type_line'].strip()
                or row.get('commander_legality') != 'legal'):
                raise ValueError(f'Incomplete card metadata: {name}')
            if not set(identity) <= {'U', 'R'}:
                raise ValueError(f'Card outside commander color identity: {name}')
            if name not in _BASIC:
                ids[oracle_id] += qty
                if ids[oracle_id] > 1:
                    raise ValueError(f'Duplicate nonbasic card: {name}')
        return Deck('Magnus the Red', tuple((zone, name, qty) for (zone, name), qty in cards.items()))
