"""Small declared card expansion; fixed Wizard choice is an explicit subset."""
from dataclasses import replace
from types import MappingProxyType
from rules import CardDefinition, Cost, Ability
import integrated as v6

NEW = {
    'Abrade': ('instant', 'named_abrade'),
    'Capsize': ('instant', 'named_capsize'),
    'Arcane Adaptation': ('enchantment', 'named_adaptation'),
}


def install(table):
    for name, (typ, effect) in NEW.items():
        key = 'named:' + name
        previous = table.zones.specs[key]
        spec = replace(previous, card_type=typ, effect=effect,
                       parameters=MappingProxyType({'coverage': 'verified_subset'}))
        table.zones.specs[key] = spec
        generic, blue, red = v6.CAT[name]['cost']
        abilities = ((Ability('static', op='add_creature_subtype', args=(('subtype', 'Wizard'),)),)
                     if name == 'Arcane Adaptation' else ())
        definition = CardDefinition(key, name, frozenset({typ}), cost=Cost(generic, blue, red),
                                    abilities=abilities)
        for obj in table.rules.objects.values():
            if obj.card.card_id == key: obj.card = definition
    table.rules._dirty()


def action(table, player, card, tags=None):
    if card.name == 'Arcane Adaptation':
        if tags not in (None, ()): raise ValueError('Only the declared Wizard choice is supported')
        return base_action(table, player, card, (), {})
    if card.name == 'Capsize':
        if tags is None:
            trial = base_action(table, player, card, ('buyback',), {'buyback': True})
            tags = ('buyback',) if table.can_pay(player, trial) else ()
        if tags not in ((), ('buyback',)): raise ValueError('Unknown buyback choice')
        result = base_action(table, player, card, tags, {'buyback': bool(tags)})
        types = {'creature', 'artifact', 'enchantment', 'planeswalker', 'battle', 'land'}
    elif card.name == 'Abrade':
        if tags is None:
            artifacts = [o for o in table.rules.on_battlefield() if o.controller != player.seat
                         and table.rules.legal_target(player.seat, o.object_id, {'artifact'})]
            tags = ('artifact',) if artifacts else ('damage',)
        if tags not in (('artifact',), ('damage',)): raise ValueError('Abrade needs exactly one supported mode')
        result = base_action(table, player, card, tags, {'mode': tags[0]})
        types = {'artifact'} if tags == ('artifact',) else {'creature'}
    else: raise ValueError('Unknown expanded card')
    options = [o for o in table.rules.on_battlefield() if o.controller != player.seat
               and table.rules.legal_target(player.seat, o.object_id, types)]
    if options:
        target = max(options, key=lambda o: ('land' not in o.types, o.power + o.toughness, o.object_id))
        result.target = target.controller; result.target_object = target.object_id
    return result


def base_action(table, player, card, tags, choices):
    import simulation as base
    generic, blue, red = v6.CAT[card.name]['cost']
    if card.name == 'Capsize' and tags: generic += 3
    cost = table.rules.modified_cost(player.seat, frozenset({card.card_type}), Cost(generic, blue, red))
    result = base.Action(player.seat, card.name, card.card_type, card.effect, cost.total,
                         parameters={**card.parameters, 'U': blue, 'R': red, **choices}, tags=tags)
    adjust = getattr(table, 'adjust_named_action_cost', None)
    return adjust(result) if adjust else result
