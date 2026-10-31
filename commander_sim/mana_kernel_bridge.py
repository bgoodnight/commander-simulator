"""Read-only bridge from the authoritative live kernel to M2 fixed mana plans.

This module does not tap lands, mutate zones, authorize a cast, or establish
full spell legality. The live engine must revalidate the selected object IDs
and commit payment atomically before performing a real cast.
Only reviewed basic lands and Command Tower are admitted as sources.
"""
from dataclasses import dataclass

from .mana_costs import UnsupportedManaCost, parse_fixed_mana_cost, plan_source_payment

BASIC_COLORS = {
    'Plains': 'W', 'Island': 'U', 'Swamp': 'B',
    'Mountain': 'R', 'Forest': 'G', 'Wastes': 'C',
}


@dataclass(frozen=True)
class LivePaymentPreview:
    """Selected physical object IDs, not an authorization or payment."""
    source_ids: tuple[int, ...]
    source_colors: tuple[str, ...]


def _reviewed_modes(name, commander_colors):
    if name == 'Command Tower':
        return frozenset(commander_colors)  # Empty identity produces no mana.
    base = name.removeprefix('Snow-Covered ')
    if base in BASIC_COLORS and (name == base or name == 'Snow-Covered ' + base):
        return frozenset({BASIC_COLORS[base]})
    return frozenset()


def plan_live_basic_payment(kernel, controller, printed_cost, commander_colors):
    """Preview fixed printed cost against actual untapped controlled permanents.

    Reads kernel.objects, whose IDs and objects belong to the existing engine.
    Unsupported sources are excluded rather than assigned hypothetical mana.
    In particular, an object in another zone, an opponent's land, a tapped
    land, or a Treasure without reviewed ability data cannot fund the preview.

    Returns None for insufficient known sources and raises on malformed costs
    or invalid commander identity. A result never proves casting legality.
    """
    if type(controller) is not int or controller < 0:
        raise ValueError('Invalid controller seat')
    colors = frozenset(commander_colors)
    if any(c not in 'WUBRG' or len(c) != 1 for c in colors):
        raise ValueError('Invalid commander color identity')
    cost = parse_fixed_mana_cost(printed_cost)
    candidates = []
    for oid, obj in sorted(kernel.objects.items()):
        if (obj.zone != 'battlefield' or obj.controller != controller
                or obj.tapped or obj.token or 'land' not in obj.types):
            continue
        modes = _reviewed_modes(obj.card.name, colors)
        if modes:
            candidates.append((oid, modes))
    assignment = plan_source_payment(cost, [modes for _, modes in candidates])
    if assignment is None:
        return None
    ids = tuple(candidates[i][0] for i in assignment)
    # Deterministic chosen modes: preserve each explicit cost pip where possible.
    # Do not assert which mode the real engine will ultimately activate.
    return LivePaymentPreview(ids, tuple(''.join(sorted(candidates[i][1])) for i in assignment))
