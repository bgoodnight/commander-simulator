"""Narrow verified-card bridge into the historical live-zone kernel.

Only ordinary U/R creatures with simple printed costs are supported. The
object is created in a library, its effects are explicitly unsupported, and
it cannot be cast through strict mode. Printed keywords remain in the
identity registry; this bridge does not implement them or authorize targeting.
It is not a complete deck loader or a hybrid casting implementation.
"""
from dataclasses import replace
import re


def _simple_cost(face):
    cost=face.mana_cost
    if not isinstance(cost,str) or not cost:
        raise ValueError('Missing printed mana cost')
    symbols=re.findall(r'\{([^{}]+)\}',cost)
    if ''.join('{'+s+'}' for s in symbols) != cost:
        raise ValueError('Invalid printed mana cost')
    generic=blue=red=0
    for symbol in symbols:
        if symbol.isascii() and symbol.isdecimal():generic+=int(symbol)
        elif symbol=='U':blue+=1
        elif symbol=='R':red+=1
        else:raise NotImplementedError(f'Unsupported mana symbol: {symbol}')
    if face.mana_value != generic+blue+red:
        raise ValueError('Printed mana value disagrees with cost')
    return generic,blue,red


def add_library_creature(table, registry, name, owner):
    """Create one verified but uncastable creature in the authoritative library."""
    identity=registry.get(name)
    if identity.layout != 'normal':
        raise NotImplementedError('Only ordinary single-faced cards are supported')
    face=identity.primary_face()
    if face.types != frozenset({'creature'}) or face.power is None or face.toughness is None:
        raise NotImplementedError('Requires verified ordinary creature characteristics')
    if name != face.name or face.colors is None:
        raise ValueError('Card name or printed colors are incomplete')
    generic,blue,red=_simple_cost(face)
    if 'named:'+name in table.zones.specs:
        raise ValueError('A definition for this card is already registered')
    # Historical modules have colliding names and are available only after the
    # isolated legacy engine has been imported by the caller.
    from simulation import CardSpec
    from rules import Cost
    spec=CardSpec(name,'verified_unimplemented',face.mana_value,'creature','unsupported',
                  {'coverage':'verified_identity_effects_unsupported'}, {'U':blue,'R':red})
    definition=table.zones.register(spec,detailed=True)
    definition=replace(definition,types=face.types,subtypes=face.subtypes,colors=face.colors,
                       cost=Cost(generic=generic,blue=blue,red=red),
                       base_power=face.power,base_toughness=face.toughness,
                       keywords=frozenset(),abilities=(),coverage='unimplemented')
    return table.zones.add(definition,owner,'library')
