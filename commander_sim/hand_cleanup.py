"""Physical Commander cleanup hand-size enforcement and bounded discard policy.

No new zone inventories: the authoritative LiveZones moves every discarded
card. The heuristic is intentionally small, deterministic and board-aware.
It does not assert knowledge of unimplemented spells or predefine combos.
"""
from collections import Counter
from dataclasses import dataclass

from .mana_costs import UnsupportedManaCost, parse_fixed_mana_cost


NO_MAXIMUM_HAND_SIZE = {
    "Thought Vessel": (
        "9965d9c5-2ebf-4a6c-930e-55c5890979be",
        "You have no maximum hand size.\n{T}: Add {C}.",
    ),
    "Reliquary Tower": (
        "c23e5b80-08d2-4e24-9908-fe2aa4f30f6f",
        "You have no maximum hand size.\n{T}: Add {C}.",
    ),
}


@dataclass(frozen=True)
class CleanupDiscard:
    name: str
    old_id: int
    graveyard_id: int
    utility_score: int


@dataclass(frozen=True)
class CleanupResult:
    hand_before: int
    maximum_hand_size: int | None
    hand_after: int
    discarded: tuple[CleanupDiscard, ...]


def maximum_hand_size(kernel, seat, catalog):
    """Return the active verified limit (None for no maximum)."""
    if type(seat) is not int or not 0 <= seat < 4:
        raise ValueError("Invalid seat")
    for obj in kernel.objects.values():
        if obj.zone != "battlefield" or obj.controller != seat:
            continue
        pinned = NO_MAXIMUM_HAND_SIZE.get(obj.card.name)
        raw = catalog.get(obj.card.name)
        if (pinned is not None and isinstance(raw, dict)
                and raw.get("oracle_id") == pinned[0]
                and raw.get("oracle_text") == pinned[1]
                and obj.card.card_id == pinned[0]):
            return None
    return 7


def _printed_mana_value(raw):
    if isinstance(raw, dict):
        value = raw.get("cmc")
        if type(value) in (float, int) and value >= 0:
            return int(value)
        try:
            return parse_fixed_mana_cost(raw.get("mana_cost")).mana_value
        except (UnsupportedManaCost, ValueError, TypeError):
            pass
    return None


def discard_priority(zones, seat, catalog, oid, *,
                     land_count, mana_sources, duplicate_count,
                     supported_action=False):
    """Higher score means more useful to retain in the current state.

    Primary preferences: make early land drops, retain manageable spells and
    independently supported actions, avoid redundant land/cards. Printed
    characteristics describe *potential*, not permission or combo importance.
    """
    obj = zones.kernel.get(oid)
    raw = catalog.get(obj.card.name, {})
    mv = _printed_mana_value(raw)
    is_land = "land" in obj.types
    if is_land:
        score = 65 if land_count < 3 else (45 if land_count < 5 else
                                          22 if land_count < 7 else 8)
    else:
        score = 36
        score += 12 if supported_action else 0
        if "creature" in obj.types:
            score += 5
        if "instant" in obj.types:
            score += 3
        if mv is not None:
            if mv <= mana_sources + 1:
                score += 12
            else:
                score -= min(21, 3 * (mv - mana_sources - 1))
        # Unrecognized costly cards may still be useful later; only a mild
        # heuristic penalty, never an inference that the effect is worthless.
        if not supported_action:
            score -= 4
    score -= min(18, 9 * max(0, duplicate_count - 1))
    return score


def cleanup_hand(zones, seat, catalog, *, supported_action=None):
    """Resolve the cleanup discard in physical zones after end-step effects.

    No mana is paid and no discard decision alters an arbitrary printed card
    ability. The host has already performed legal main-phase actions and must
    execute downstream discard-trigger rules in a separate reviewed engine.
    """
    if type(seat) is not int or not 0 <= seat < zones.seats:
        raise ValueError("Invalid seat")
    if supported_action is not None and not callable(supported_action):
        raise TypeError("Supported-action predicate must be callable")
    hand = tuple(zones.ids(seat, "hand"))
    limit = maximum_hand_size(zones.kernel, seat, catalog)
    if limit is None or len(hand) <= limit:
        return CleanupResult(len(hand), limit, len(hand), ())
    battlefield = [obj for obj in zones.kernel.objects.values()
                   if obj.zone == "battlefield" and obj.controller == seat]
    land_count = sum("land" in obj.types for obj in battlefield)
    mana_sources = sum("land" in obj.types or (
        "artifact" in obj.types and not obj.token) for obj in battlefield)
    duplicates = Counter(zones.kernel.get(oid).card.name for oid in hand)
    ranked = []
    for oid in hand:
        obj = zones.kernel.get(oid)
        useful = bool(supported_action(obj)) if supported_action else False
        score = discard_priority(
            zones, seat, catalog, oid, land_count=land_count,
            mana_sources=mana_sources,
            duplicate_count=duplicates[obj.card.name],
            supported_action=useful)
        ranked.append((score, obj.card.name, oid))
    # A single simultaneous cleanup selection; deterministic tie-breaks.
    ranked.sort()
    discarded = []
    for score, name, oid in ranked[:len(hand) - limit]:
        new_id = zones.discard(seat, oid)
        discarded.append(CleanupDiscard(name, oid, new_id, score))
    if len(zones.ids(seat, "hand")) != limit:
        raise AssertionError("Cleanup hand limit not enforced")
    return CleanupResult(len(hand), limit, limit, tuple(discarded))
