"""Prevalidated physical zone movement batches with pre-move provenance.

A small shared primitive for mass zone effects such as Living Death. It stages
all source identities *before* mutation and returns one ordered group of moves.
It does not pretend sequential kernel transitions are fully simultaneous MTG
resolution, nor grant timing, spell permission, replacement choices, or triggers.
The caller must process resulting events at a legal resolution boundary.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ZoneMoveRequest:
    object_id: int
    destination: str
    reason: str = "resolve"


@dataclass(frozen=True)
class ZoneObjectBefore:
    object_id: int
    owner: int
    controller: int
    zone: str
    card_name: str
    types: frozenset[str]
    subtypes: frozenset[str]
    token: bool


@dataclass(frozen=True)
class ZoneBatchMovement:
    before: ZoneObjectBefore
    new_object_id: int | None
    destination: str
    reason: str


@dataclass(frozen=True)
class ZoneBatchOutcome:
    label: str
    movements: tuple[ZoneBatchMovement, ...]


def resolve_physical_zone_batch(zones, requests, *, label="zone_batch"):
    """Prevalidate all old object IDs, then move through authoritative zones.

    The returned per-object snapshots are last-known characteristics *before*
    this batch, including controller (which may differ from owner). Callers
    must resolve death/ETB/LTB triggers from a separate, properly timed event
    dispatcher; this function never invents trigger order or priorities.
    """
    if not isinstance(label,str) or not label:
        raise ValueError("Batch needs a descriptive label")
    actions=tuple(requests)
    if len(actions)>400 or any(not isinstance(x,ZoneMoveRequest) for x in actions):
        raise ValueError("Invalid physical zone movement batch")
    ids=[x.object_id for x in actions]
    if len(set(ids))!=len(ids):
        raise ValueError("One object cannot be moved twice in a phase")
    approved_reasons={"resolve","sacrifice","exile","destroy","state_based"}
    staged=[]
    for action in actions:
        if (type(action.object_id) is not int or
                action.destination not in zones.valid_zones or
                action.reason not in approved_reasons):
            raise ValueError("Invalid physical zone movement request")
        obj=zones.kernel.objects.get(action.object_id)
        if (obj is None or obj.zone not in zones.valid_zones
                or obj.zone==action.destination):
            raise ValueError("Batch source missing, stale or already in destination")
        staged.append(ZoneObjectBefore(
            obj.object_id,obj.owner,obj.controller,obj.zone,obj.card.name,
            frozenset(obj.types),frozenset(obj.subtypes),bool(obj.token)))
    moves=[]
    for action,before in zip(actions,staged):
        moved=zones.move(action.object_id,action.destination,action.reason)
        moves.append(ZoneBatchMovement(before,moved,action.destination,
                                       action.reason))
    return ZoneBatchOutcome(label,tuple(moves))
