"""Data descriptions for the currently modeled named counterspells.

No printed card-name branches are present in the shared stack. Providers can
register further response descriptors; unregistered special effects fail closed.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ResponseCard:
    legal_spell_types:tuple[str,...]
    after_resolution:str='none'
    coverage:str='partial'

DEFAULT_TYPES=('creature','instant','sorcery','artifact','enchantment','planeswalker')
COUNTER_CARDS={
    'Counterspell':ResponseCard(DEFAULT_TYPES,coverage='subset'),
    'Arcane Denial':ResponseCard(DEFAULT_TYPES,coverage='partial'),
    'Swan Song':ResponseCard(('instant','sorcery','enchantment'),'bird_token',coverage='subset'),
    "An Offer You Can't Refuse":ResponseCard(('noncreature',),'two_treasures',coverage='partial'),
    'Flusterstorm':ResponseCard(('instant','sorcery'),coverage='partial'),
}

def descriptor(card):
    if card.name in COUNTER_CARDS:return COUNTER_CARDS[card.name]
    legal=card.parameters.get('can_counter_types',DEFAULT_TYPES)
    return ResponseCard(tuple(legal),'none','synthetic')
