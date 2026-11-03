"""Typed, source-independent three-phase mass creature zone sequence.

Faithfully preserves the *ordered categories* of Living Death-like effects:
exile prior graveyard creatures, sacrifice battlefield creatures, return only
objects exiled in the first step. Each phase is prevalidated and commits over
the existing kernel. This is still a bounded mechanics primitive, not a
finished spell: complete simultaneity, replacement/commander choices, APNAP
trigger order and priority require the full multiplayer host.
"""
from dataclasses import dataclass

from .batch_zone_resolution import ZoneMoveRequest,resolve_physical_zone_batch


@dataclass(frozen=True)
class MassCreatureExchange:
    exiled: object
    sacrificed: object
    returned: object
    participating_seats: tuple[int,...]
    fidelity: str = "three_phase_physical_no_simultaneous_trigger_stack"


def resolve_mass_creature_exchange(zones,life):
    """Run a reviewed, already-authorized three-step physical zone sequence.

    This helper never chooses whether to cast a spell or pays its mana costs.
    Fail closed if a creature commander would require an unmodeled command-zone
    replacement choice. Caller must separately resolve replacement effects,
    state-based actions and collected triggers at actual game boundaries.
    """
    if life.kernel is not zones.kernel:
        raise ValueError("Mass effect must share authoritative life and zones")
    active=life.active_seats()
    # Snapshot both groups before any mutation. Only creatures currently in a
    # participating player's graveyard or under their control are affected.
    grave_ids=tuple(oid for seat in active
        for oid in tuple(zones.ids(seat,"graveyard"))
        if "creature" in zones.kernel.get(oid).types
        and not zones.kernel.get(oid).token)
    board_ids=tuple(obj.object_id for obj in zones.kernel.on_battlefield()
        if "creature" in obj.types and obj.controller in active)
    # In the bounded host, no unmodeled commander-choice fallback.
    if any("commander" in zones.kernel.get(oid).card.supertypes
           for oid in board_ids):
        raise NotImplementedError(
            "Mass sacrifice of a commander requires reviewed replacement choice")
    exiled=resolve_physical_zone_batch(zones,
        (ZoneMoveRequest(oid,"exile","exile") for oid in grave_ids),
        label="mass_creature_exile")
    sacrificed=resolve_physical_zone_batch(zones,
        (ZoneMoveRequest(oid,"graveyard","sacrifice") for oid in board_ids),
        label="mass_creature_sacrifice")
    # Only the creatures that went to exile in phase one return. Creatures
    # sacrificed in phase two must not accidentally be reanimated.
    return_ids=tuple(move.new_object_id for move in exiled.movements
        if move.new_object_id is not None
        and zones.kernel.get(move.new_object_id).zone=="exile")
    returned=resolve_physical_zone_batch(zones,
        (ZoneMoveRequest(oid,"battlefield","resolve") for oid in return_ids),
        label="mass_creature_return")
    return MassCreatureExchange(exiled,sacrificed,returned,tuple(active))
