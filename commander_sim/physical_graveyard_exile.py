"""Physical whole-graveyard exile primitive shared across sources.

This operation is deliberately not a casting or targeting permission. A pinned
land, spell, or enter-trigger must independently establish the legal target and
pay any costs. One physical card is counted once even if it matches several
types, and exiling from an empty graveyard is legal.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GraveyardExileOutcome:
    target_seat: int
    exiled_ids: tuple[int, ...]
    matched_count: int


def exile_physical_graveyard(zones, target_seat, *, count_types_any=frozenset()):
    """Move all real graveyard objects to exile and count matching original types."""
    if type(target_seat) is not int or not 0 <= target_seat < zones.seats:
        raise ValueError("Graveyard target must be an existing player seat")
    if (not isinstance(count_types_any, frozenset)
            or any(not isinstance(t, str) or not t
                   for t in count_types_any)):
        raise TypeError("Exile counting filter must be a frozen set of card types")
    ids = tuple(zones.ids(target_seat, "graveyard"))
    matched = sum(bool(zones.kernel.get(oid).types & count_types_any)
                  for oid in ids)
    moved = tuple(zones.move(oid, "exile", "exile") for oid in ids)
    return GraveyardExileOutcome(target_seat, moved, matched)
