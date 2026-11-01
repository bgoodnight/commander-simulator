"""One reusable, exact-pinned library-search action on existing live zones.

This service NEVER grants cast permission: a caller must first pay, cast,
satisfy timing, and resolve the reviewed source through its shared kernel.
The source must be on stack (tutor spell) or battlefield (reviewed ETB).
Search target is a real object in the selected owner's authoritative library.
"""
from dataclasses import dataclass

from .effect_templates import tutor_matches
from .reviewed_tutors import reviewed_tutor


@dataclass(frozen=True)
class SearchResult:
    source_id: int
    target_old_id: int
    target_new_id: int
    target_name: str
    destination: str
    revealed: bool
    shuffled: bool


def legal_search_targets(zones, seat, source_id, catalog):
    """Return exact real library IDs that satisfy the reviewed search template."""
    if type(seat) is not int or not 0 <= seat < zones.seats:
        raise ValueError("Invalid seat")
    source = zones.kernel.get(source_id)
    if (source.controller != seat or source.zone not in {"stack", "battlefield"}):
        raise ValueError("Search source has not resolved/cannot activate")
    card = catalog.get(source.card.name)
    if card is None:
        raise ValueError("Unreviewed tutor source")
    found = reviewed_tutor(source.card.name, card)
    if found is None:
        raise ValueError("Tutor effect not reviewed")
    template, cost, kind = found
    if ((kind == "creature" and source.zone != "battlefield")
            or (kind in {"instant", "sorcery"} and source.zone != "stack")):
        raise ValueError("Tutor source in wrong effect timing zone")
    return tuple(oid for oid in zones.ids(seat, "library")
                 if (zones.kernel.get(oid).card.name in catalog
                     and tutor_matches(template,
                                       catalog[zones.kernel.get(oid).card.name])))


def execute_reviewed_search_to_hand(zones, seat, source_id, target_id, catalog):
    """Move one eligible physical card to hand and shuffle same library.

    The caller must invoke during reviewed effect resolution. The executor
    does not make its own cast, replay trigger, priority decision or target
    policy. An unsupported destination fails before changing any objects.
    """
    source = zones.kernel.get(source_id)
    card = catalog.get(source.card.name)
    if card is None:
        raise ValueError("Unknown search source")
    found = reviewed_tutor(source.card.name, card)
    if found is None:
        raise ValueError("Unreviewed tutor")
    template, _, kind = found
    if (source.zone != "stack" or kind not in {"instant", "sorcery"}
            or source_id not in zones._pending):
        raise ValueError("An unresolved reviewed spell cast is required; ETB/activated tutors remain gated")
    if template.destination != "hand" or not template.shuffle:
        raise NotImplementedError("This tutor needs a different destination/ordering handler")
    eligible = legal_search_targets(zones, seat, source_id, catalog)
    if type(target_id) is not int or target_id not in eligible:
        raise ValueError("Target is not a legal library card")
    target_name = zones.kernel.get(target_id).card.name
    # Move the *selected physical object ID*; matching only by name would
    # silently fetch the wrong copy of a repeated basic land.
    new_id = zones.move(target_id, "hand", "resolve")
    zones.shuffle(seat)
    return SearchResult(source_id, target_id, new_id, target_name,
                        template.destination, template.reveal, template.shuffle)
