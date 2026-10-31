"""Explicit mana-ability metadata for named and synthetic card providers.

This boundary contains the limited named-card catalog; Resources only executes
and plans generic Ability values. Unknown sources produce no mana.
"""
from resources import Ability, Cost, fixed, C, U, R
from state import v6


NAMED = {
    'Frostboil Snarl': fixed(U, R),
    'Fabled Passage': (),
    'Sol Ring': fixed((2, 0, 0)),
    'Izzet Signet': (Ability((0, 1, 1), Cost(generic=1)),),
    'Cascade Bluffs': fixed(C) + tuple(Ability(output, cost)
        for cost in (Cost(blue=1), Cost(red=1))
        for output in ((0, 2, 0), (0, 1, 1), (0, 0, 2))),
    'Shivan Reef': fixed(C) + fixed(U, R, damage=1),
    'Talisman of Creativity': fixed(C) + fixed(U, R, damage=1),
    'Fiery Islet': fixed(U, R, life=1),
    'Mind Stone': fixed(C),
    'Arcane Signet': fixed(U, R),
    'Riverglide Pathway [U]': fixed(U),
    'Riverglide Pathway [R]': fixed(R),
}
TREASURE_MODES = fixed(U, R, sacrifice=True)
LAND_MODES = {'C': fixed(C), 'U': fixed(U), 'R': fixed(R), 'D': fixed(U, R)}


def abilities_for(resources, obj, visiting=frozenset()):
    """Provider metadata chooses abilities; the planner contains no card-name rules."""
    if obj.zone != 'battlefield' or obj.object_id in visiting: return ()
    name = resources.kernel.resource_names.get(obj.object_id, obj.card.name)
    if obj.token and obj.card.card_id == 'treasure':
        return TREASURE_MODES
    if not obj.card.card_id.startswith('named:'):
        # Synthetic resources remain declared approximations, now tied to IDs.
        if 'land' in obj.types: return LAND_MODES['C']
        entry = resources.table.world.views.get(obj.object_id)
        if entry and entry.kind == 'permanent' and entry.view.kind == 'ramp':
            return fixed((entry.view.value, 0, 0)) if entry.view.value > 0 else ()
        return ()
    if name in NAMED: return NAMED[name]
    if name in ('Fellwar Stone', 'Exotic Orchard'):
        # Derive available types from opposing lands; ignore activation costs
        # for 'could produce', and break Orchard dependency cycles.
        types = set()
        for land in resources.kernel.on_battlefield():
            if land.controller != obj.controller and 'land' in land.types:
                for ability in resources.abilities(land, visiting | {obj.object_id}):
                    types.update(i for i, amount in enumerate(ability.output) if amount)
        types.discard(0)  # both abilities add a color, never colorless
        return fixed(*(tuple(int(i == color) for i in range(3)) for color in sorted(types)))
    if 'land' in obj.types:
        return LAND_MODES.get(v6.CAT.get(name, {}).get('land_profile'), ())
    return ()  # unknown mana text cannot generate invented mana
