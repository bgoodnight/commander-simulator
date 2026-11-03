"""Reusable physical -1/-1 counter upkeep and counter-conditioned destruction.

Reviewed phase handlers authorize their exact printed source. This module
only supplies reusable target selection, counter placement, simultaneous SBA
and the existing death-event bridge. It does not parse unknown Oracle cards.
"""
from dataclasses import dataclass

from .physical_common_effects import (
    CounterPlacement, put_reviewed_counters,
    TargetedPermanentRemoval, remove_reviewed_permanent)
from .reviewed_death_effects import capture_battlefield


@dataclass(frozen=True)
class CounterPhaseOutcome:
    affected_ids: tuple[int, ...] = ()
    destroyed_old_id: int | None = None


def put_counter_on_creatures_by_color(
        zones, source_id, *, kind="-1/-1", quantity=1,
        excluded_color="B", death_engine=None, turn=1):
    """Place simultaneous counters on all creatures lacking a verified color.

    An unknown color is not guessed to be nonblack. All selected recipients
    are physical objects on the shared battlefield, including opponents'.
    Deaths are checked once after the whole batch has received its counters.
    """
    kernel=zones.kernel
    source=kernel.get(source_id)
    if source.zone!="battlefield":
        raise ValueError("Counter source not on battlefield")
    if not isinstance(excluded_color,str) or excluded_color not in "WUBRG":
        raise ValueError("Invalid excluded color")
    if death_engine is not None and death_engine.zones is not zones:
        raise ValueError("Death resolver must use the same zones")
    if type(turn) is not int or turn<1:
        raise ValueError("Invalid turn")
    effect=CounterPlacement(kind,quantity,require_controller=False)
    targets=tuple(obj.object_id for obj in kernel.on_battlefield()
                  if "creature" in obj.types
                  and obj.card.colors is not None
                  and excluded_color not in obj.card.colors)
    before=capture_battlefield(kernel)
    start=len(kernel.moves)
    for oid in targets:
        put_reviewed_counters(kernel,source.controller,oid,effect)
    kernel.check_state_based()
    if death_engine is not None:
        death_engine.resolve_deaths(before,move_index=start,turn=turn)
    return CounterPhaseOutcome(affected_ids=targets)


def destroy_creature_with_counter(
        zones, source_id, *, counter_kind="-1/-1",
        target_id=None, death_engine=None, turn=1):
    """Select or verify a countered creature, then destroy by physical move.

    Target choice is a host/pilot policy. The bounded fallback picks the
    lowest-ID legal noncommander creature. Hexproof and shroud remain handled
    by kernel.legal_target; an unsupported commander replacement is refused.
    """
    kernel=zones.kernel
    source=kernel.get(source_id)
    if source.zone!="battlefield":
        raise ValueError("Destroy source not on battlefield")
    if death_engine is not None and death_engine.zones is not zones:
        raise ValueError("Death resolver must share zones")
    if type(turn) is not int or turn<1:
        raise ValueError("Invalid turn")
    legal=tuple(obj.object_id for obj in sorted(
        kernel.on_battlefield(),key=lambda item:item.object_id)
        if "creature" in obj.types and obj.counters[counter_kind]>0
        and "commander" not in obj.card.supertypes
        and "indestructible" not in obj.keywords
        and kernel.legal_target(source.controller,obj.object_id,
                                frozenset({"creature"})))
    if target_id is None:
        selected=legal[0] if legal else None
    else:
        if type(target_id) is not int or target_id not in legal:
            raise ValueError("Invalid counter-conditioned destruction target")
        selected=target_id
    if selected is None:
        return CounterPhaseOutcome()
    before=capture_battlefield(kernel)
    start=len(kernel.moves)
    remove_reviewed_permanent(
        kernel,source.controller,selected,
        TargetedPermanentRemoval("destroy",frozenset({"creature"})))
    if death_engine is not None:
        death_engine.resolve_deaths(before,move_index=start,turn=turn)
    return CounterPhaseOutcome(destroyed_old_id=selected)
