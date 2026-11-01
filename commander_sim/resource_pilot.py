"""Reusable bounded resource sequencing policy; never grants card abilities.

The reviewed sacrifice engine and physical mana planner remain authoritative.
This layer only decides when trading an expendable token for mana is likely
to unlock an independently reviewed spell in the current main phase.
"""
from .mana_costs import parse_fixed_mana_cost, UnsupportedManaCost
from .reviewed_sacrifice_actions import SACRIFICE_MODES
from .resource_development import assess_resources

_MANA_OPERATIONS = frozenset({"colorless_mana", "any_color_mana"})


def choose_token_mana_sacrifice(zones, seat, catalog, mana_service,
                                *, supported_spell, max_sacrifices=4):
    """Return (source_id, token_id) or None, with bounded lookahead.

    Requires a real token creature and a registered mana-producing sacrifice
    outlet. The only decision heuristic is a currently unpayable *reviewed*
    spell plausibly reachable using up to max_sacrifices token sacrifices.
    It never assumes extra token creation, untaps, or repeated triggers.
    """
    if mana_service.kernel is not zones.kernel or not callable(supported_spell):
        raise ValueError("Resource policy requires the authoritative host")
    if type(max_sacrifices) is not int or max_sacrifices < 1:
        raise ValueError("Expected positive sacrifice bound")
    objects = list(zones.kernel.on_battlefield())
    sources = sorted((o for o in objects if o.controller == seat
                      and o.card.name in SACRIFICE_MODES
                      and SACRIFICE_MODES[o.card.name].action in _MANA_OPERATIONS
                      and not o.tapped),
                     key=lambda o:o.object_id)
    tokens = sorted((o for o in objects if o.controller == seat
                     and o.token and "creature" in o.types
                     and "commander" not in o.card.supertypes),
                    key=lambda o:(o.power, o.object_id))
    if not sources or not tokens:
        return None
    resource = assess_resources(zones.kernel, mana_service, seat)
    current = resource.available_fixed_mana
    capacity = current + 2 * min(len(tokens), max_sacrifices)
    has_payoff = False
    for oid in zones.ids(seat, "hand"):
        card = zones.kernel.get(oid)
        if not supported_spell(card):
            continue
        raw = catalog.get(card.card.name)
        if not raw:
            continue
        try:
            cost = parse_fixed_mana_cost(raw.get("mana_cost"))
            payable = mana_service.plan_spell(seat, raw["mana_cost"], card)
        except (UnsupportedManaCost, ValueError):
            continue
        total = cost.generic + len(cost.colored)
        if payable is None and current < total <= capacity:
            has_payoff = True
            break
    if not has_payoff:
        return None
    for source in sources:
        mode = SACRIFICE_MODES[source.card.name]
        for victim in tokens:
            if mode.sacrifice_other and source.object_id == victim.object_id:
                continue
            return source.object_id, victim.object_id
    return None
