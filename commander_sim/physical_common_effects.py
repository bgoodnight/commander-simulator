"""Reusable physical draw, mill, counter and graveyard-to-hand operations.

Each action must be authorized by an independently reviewed card/ability
slot. These functions are NOT an Oracle parser, a target/timing engine or an
alternate game state. They mutate the existing IndexedKernel/LiveZones only.
"""
from dataclasses import dataclass
from types import SimpleNamespace

from .legacy_common_ops import ZoneTransfer, transfer_physical_object


@dataclass(frozen=True)
class CardQuantity:
    count: int
    def __post_init__(self):
        if type(self.count) is not int or self.count<0:
            raise ValueError("Card quantity must be a nonnegative integer")


@dataclass(frozen=True)
class DrawOutcome:
    drawn_ids: tuple[int, ...]
    complete: bool


@dataclass(frozen=True)
class CounterPlacement:
    kind: str
    quantity: int = 1
    permitted_types: frozenset[str] = frozenset({"creature"})
    require_controller: bool = True

    def __post_init__(self):
        if (not isinstance(self.kind,str) or not self.kind
                or type(self.quantity) is not int or self.quantity<=0
                or not isinstance(self.permitted_types,frozenset)
                or not self.permitted_types
                or any(not isinstance(t,str) or not t for t in self.permitted_types)
                or type(self.require_controller) is not bool):
            raise ValueError("Invalid reviewed counter placement")


@dataclass(frozen=True)
class GraveyardToHand:
    """Restrict a reviewed retrieval; caller owns target/permission resolution."""
    permitted_types: frozenset[str]

    def __post_init__(self):
        if (not isinstance(self.permitted_types,frozenset)
                or not self.permitted_types or
                any(not isinstance(t,str) or not t for t in self.permitted_types)):
            raise ValueError("Graveyard retrieval requires printed target types")


def draw_physical_cards(zones, seat, quantity: CardQuantity):
    """Draw using existing zone order and loss indicator; caller handles SBA."""
    if not isinstance(quantity,CardQuantity):
        raise TypeError("Expected typed draw quantity")
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid seat")
    ids,complete=zones.draw(seat,quantity.count)
    return DrawOutcome(tuple(ids),bool(complete))


def mill_physical_cards(zones, seat, quantity: CardQuantity):
    """Mill exact physical top cards; no new objects or replacement shortcuts."""
    if not isinstance(quantity,CardQuantity):
        raise TypeError("Expected typed mill quantity")
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid seat")
    return tuple(zones.mill(seat,quantity.count))


def put_reviewed_counters(kernel, seat, object_id, effect: CounterPlacement,
                          *, refresh=None):
    """Add counters to an existing lawful object, then optionally refresh view.

    The caller must separately establish target timing, protection,
    replacement, and post-effect state-based actions.
    """
    if not isinstance(effect,CounterPlacement):
        raise TypeError("Expected reviewed counter placement")
    if type(seat) is not int or seat<0:
        raise ValueError("Invalid seat")
    obj=kernel.objects.get(object_id)
    if (obj is None or obj.zone!="battlefield"
            or not obj.types & effect.permitted_types
            or (effect.require_controller and obj.controller!=seat)):
        raise ValueError("Counter target fails reviewed restrictions")
    kernel.add_counter(object_id,effect.kind,effect.quantity)
    if refresh is not None:
        if not callable(refresh):
            raise TypeError("Refresh must be existing host callback")
        refresh(object_id)
    return object_id


def retrieve_reviewed_graveyard_card(zones, seat, object_id, effect: GraveyardToHand):
    """Return one owned, correctly typed graveyard object to physical hand.

    Does not grant permission to activate a printed recursion ability.
    """
    if not isinstance(effect,GraveyardToHand):
        raise TypeError("Expected reviewed retrieval")
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid seat")
    return transfer_physical_object(
        SimpleNamespace(rules=zones.kernel,zones=zones),seat,object_id,
        ZoneTransfer("graveyard","hand",
                     allowed_types_any=effect.permitted_types,
                     require_owner=True))
