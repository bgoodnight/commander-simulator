"""Immutable printed characteristics from a validated offline snapshot.

This registry does not interpret Oracle text, grant abilities, or determine
legal actions. Multi-face defaults are restricted to reviewed layouts.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class FaceIdentity:
    name: str
    type_line: str
    types: frozenset
    subtypes: frozenset
    mana_cost: str | None
    mana_value: int | float | None
    colors: frozenset | None
    power: int | None
    toughness: int | None
    keywords: frozenset | None

@dataclass(frozen=True)
class CardIdentity:
    oracle_id: str
    name: str
    layout: str
    color_identity: frozenset
    source_uri: str
    faces: tuple
    def primary_face(self):
        if self.layout not in ('normal','adventure'):
            raise NotImplementedError(f'Primary-face semantics not reviewed for {self.layout}')
        return self.faces[0]

_TYPES=frozenset({'artifact','battle','creature','enchantment','instant','kindred','land','planeswalker','sorcery','tribal'})

def _number(value):
    if isinstance(value,str) and value.isdecimal():return int(value)
    return None

def _face(data, *, cmc, keywords):
    name=data.get('name');line=data.get('type_line')
    if not isinstance(name,str) or not isinstance(line,str) or not line:
        raise ValueError('Face missing name or type line')
    left,sep,right=line.partition(' — ')
    types=frozenset(word.lower() for word in left.split() if word.lower() in _TYPES)
    if not types:raise ValueError(f'Unrecognized type line: {line}')
    colors=data.get('colors')
    if colors is not None and (not isinstance(colors,list) or any(not isinstance(c,str) or len(c)!=1 or c not in 'WUBRG' for c in colors)):
        raise ValueError(f'Invalid printed colors for {name}')
    return FaceIdentity(name,line,types,frozenset(right.split()) if sep else frozenset(),
                        data.get('mana_cost'),cmc,None if colors is None else frozenset(colors),
                        _number(data.get('power')),_number(data.get('toughness')),
                        None if keywords is None else frozenset(keywords))

class CardRegistry:
    def __init__(self, snapshot):
        self._cards={}; self.snapshot_sha256=snapshot.snapshot_sha256
        for entry in snapshot.cards:
            card=entry['card'];layout=card['layout'];faces=card.get('card_faces', [])
            if faces:
                # Face-specific values and keywords are not safely inferred from
                # aggregate card fields. Preserve unknown explicitly.
                parsed=tuple(_face(face,cmc=None,keywords=None) for face in faces)
            else:
                parsed=(_face(card,cmc=card['cmc'],keywords=card['keywords']),)
            identity=CardIdentity(card['oracle_id'],card['name'],layout,
                                  frozenset(card['color_identity']),card['scryfall_uri'],parsed)
            aliases={card['name'],entry['deck_name']}
            if layout=='adventure':aliases.add(parsed[0].name)
            for name in aliases:
                if name in self._cards and self._cards[name] != identity:
                    raise ValueError(f'Ambiguous card identity: {name}')
                self._cards[name]=identity

    def get(self,name):
        try:return self._cards[name]
        except KeyError:raise KeyError(f'No verified identity for {name}') from None
