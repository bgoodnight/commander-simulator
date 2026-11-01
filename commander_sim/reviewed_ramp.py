"""Shared physical land-search and ritual effects for the bounded pilot.

This is an explicitly reviewed subset, not a printed-text interpreter.
Card names select pinned parameters; one executor owns all zone movement,
source-paid activation, shuffling, and enter-tapped behavior.
"""
from dataclasses import dataclass
from .generic_cast import ReviewedCreatureCast, cast_reviewed_spell

@dataclass(frozen=True)
class RampRule:
    operation: str
    count: int
    activation_cost: str = ""
    sacrifice_source: bool = False
    tap_source: bool = False
    enter_tapped: bool = True

# Review gates include both printed source type and distinctive Oracle text.
# All implementations share search_basic_lands and move_basic_lands.
_RAMP = {
    "Wayfarer's Bauble": (RampRule("activated", 1, "{2}", True, True),
                         "Search your library for a basic land card"),
    "Myriad Landscape": (RampRule("activated", 2, "{2}", True, True),
                         "Search your library for up to two basic land cards"),
    "Solemn Simulacrum": (RampRule("enter", 1),
                         "search your library for a basic land card"),
}

def reviewed_ramp(name, raw):
    row = _RAMP.get(name)
    if row is None or not isinstance(raw, dict) or not raw.get("oracle_id"):
        return None
    rule, excerpt = row
    text = raw.get("oracle_text", "")
    types = raw.get("type_line", "").split(" — ", 1)[0]
    expected = {"Wayfarer's Bauble": "Artifact",
                "Myriad Landscape": "Land",
                "Solemn Simulacrum": "Artifact Creature"}[name]
    if expected not in types or excerpt.lower() not in text.lower():
        return None
    return rule


def basic_land_candidates(zones, seat, catalog, count=1, same_type=False):
    """Choose actual basic land IDs from the current library, never copies."""
    basics = []
    for oid in zones.ids(seat, "library"):
        obj = zones.kernel.get(oid)
        raw = catalog.get(obj.card.name, {})
        printed = raw.get("type_line", "")
        if printed.startswith("Basic Land — ") and raw.get("oracle_id") == obj.card.card_id:
            basics.append((obj.card.name, oid))
    basics.sort()
    if not same_type:
        return tuple(oid for _, oid in basics[:count])
    for name, _ in basics:
        same = [oid for candidate_name, oid in basics if candidate_name == name]
        if len(same) >= count:
            return tuple(same[:count])
    return ()


def put_basic_lands(zones, seat, ids, *, tapped=True):
    """Move real library cards to battlefield, then shuffle the library."""
    old = set(zones.ids(seat, "library"))
    if len(set(ids)) != len(ids) or any(i not in old for i in ids):
        raise ValueError("Land search requires distinct physical library cards")
    moved = []
    for oid in ids:
        new_id = zones.move(oid, "battlefield", "resolve")
        if tapped:
            zones.kernel.get(new_id).tapped = True
        moved.append(new_id)
    zones.shuffle(seat)
    zones.kernel._dirty()
    return tuple(moved)


def activate_land_ramp(zones, seat, source_id, catalog, mana_service):
    """Resolve Bauble/Landscape through the same typed activation path.

    Conservative payment: if the generic payment planner would tap the
    activation source, we decline rather than accidentally paying with it.
    """
    obj = zones.kernel.get(source_id)
    raw = catalog.get(obj.card.name)
    rule = reviewed_ramp(obj.card.name, raw)
    if (rule is None or rule.operation != "activated"
            or obj.zone != "battlefield" or obj.controller != seat
            or obj.tapped or obj.card.card_id != raw["oracle_id"]):
        return None
    targets = basic_land_candidates(
        zones, seat, catalog, rule.count,
        same_type=(obj.card.name == "Myriad Landscape"))
    if not targets:
        return None
    payment = mana_service.plan(seat, rule.activation_cost,
                                excluded_source_ids=(source_id,))
    if payment is None or source_id in payment.source_ids:
        return None
    committed = mana_service.pay(seat, rule.activation_cost,
                                 excluded_source_ids=(source_id,))
    if committed is None or source_id in committed.source_ids:
        raise AssertionError("Ramp activation payment changed")
    if rule.tap_source:
        obj.tapped = True
    if rule.sacrifice_source:
        zones.move(source_id, "graveyard", "sacrifice")
    return put_basic_lands(zones, seat, targets, tapped=rule.enter_tapped)


def resolve_enter_ramp(zones, seat, source_id, catalog):
    """The same basic search for a reviewed ETB source (Solemn)."""
    obj = zones.kernel.get(source_id)
    raw = catalog.get(obj.card.name)
    rule = reviewed_ramp(obj.card.name, raw)
    if (rule is None or rule.operation != "enter" or obj.zone != "battlefield"
            or obj.controller != seat or obj.card.card_id != raw["oracle_id"]):
        return None
    targets = basic_land_candidates(zones, seat, catalog, rule.count)
    return put_basic_lands(zones, seat, targets, tapped=rule.enter_tapped)


def reviewed_ritual(name, raw):
    """One verified common ritual profile; mana remains phase-bound."""
    return bool(name == "Dark Ritual" and isinstance(raw, dict)
                and raw.get("type_line", "").split(" — ", 1)[0] == "Instant"
                and raw.get("mana_cost") == "{B}"
                and "Add {B}{B}{B}" in raw.get("oracle_text", "")
                and raw.get("oracle_id"))


def cast_ritual(zones, seat, source_id, catalog, commander_colors, mana_service):
    """Cast and resolve a reviewed ritual using the generic spell path."""
    obj = zones.kernel.get(source_id)
    raw = catalog.get(obj.card.name)
    if obj.zone != "hand" or not reviewed_ritual(obj.card.name, raw):
        return None
    if obj.card.card_id != raw["oracle_id"]:
        return None
    review = ReviewedCreatureCast(obj.card.card_id, "{B}", True,
                                 ("Only the mana-producing spell effect is reviewed",))
    committed = cast_reviewed_spell(zones, seat, source_id, review,
                                    commander_colors, mana_service=mana_service,
                                    spell_type="instant")
    if committed is None:
        return None
    end_id = zones.resolve(committed.ticket)
    pool = list(mana_service.floating(seat))
    pool[2] += 3  # WUBRGC: black index 2
    zones.kernel.mana_pools[seat] = tuple(pool)
    zones.kernel._dirty()
    return end_id
