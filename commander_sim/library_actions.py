"""Composable, parameterized library actions on one authoritative physical deck.

A LibraryAction describes an operation, not permission to play any card.
An independently reviewed spell, trigger or import grammar must authorize
the recipe and pay its costs. Selectors only see cards already legally exposed
by the requested action (or the pilot's own hand).
"""
from dataclasses import dataclass

from .physical_common_effects import (
    CardQuantity, draw_physical_cards, mill_physical_cards, scry_physical_cards,
)

_KINDS = frozenset({
    "draw", "mill", "scry", "surveil", "reorder_top", "shuffle",
    "discard", "put_back",
})


@dataclass(frozen=True)
class LibraryAction:
    kind: str
    count: int = 0

    def __post_init__(self):
        if (self.kind not in _KINDS or type(self.count) is not int
                or not (self.count == 0 if self.kind == "shuffle"
                        else 1 <= self.count <= 7)):
            raise ValueError("Invalid parameterized library action")


@dataclass(frozen=True)
class LibraryOutcome:
    drawn_ids: tuple[int, ...]
    discarded_ids: tuple[int, ...]
    milled_ids: tuple[int, ...]
    bottomed_ids: tuple[int, ...]
    returned_ids: tuple[int, ...]
    steps: tuple[dict, ...]


def required_draws(actions):
    if not all(isinstance(action, LibraryAction) for action in actions):
        raise TypeError("Library recipe needs typed actions")
    return sum(action.count for action in actions if action.kind == "draw")


def _cards(zones, ids):
    return [{"id": oid, "card": zones.kernel.get(oid).card.name} for oid in ids]


def bounded_library_choice(kind, available, count, zones, seat):
    """Deterministic, deliberately weak development-oriented choice policy.

    Only uses the current pilot's hand/battlefield and the cards legally seen
    by an action. For filtered top cards, keep lands when early mana is short,
    otherwise favor nonlands. This is NOT a competitive card valuation AI.
    """
    own_lands = sum("land" in obj.types and obj.controller == seat
                    for obj in zones.kernel.on_battlefield())
    hand_lands = sum("land" in zones.kernel.get(oid).types
                     for oid in zones.ids(seat, "hand"))
    needs_land = own_lands + hand_lands < 4

    def score(oid):
        is_land = "land" in zones.kernel.get(oid).types
        return 2 if is_land == needs_land else 0

    ordered = tuple(sorted(available, key=lambda oid: -score(oid)))
    if kind == "scry":
        bottom = tuple(oid for oid in available if score(oid) == 0)
        top = tuple(oid for oid in ordered if oid not in bottom)
        return {"bottom": bottom, "top": top}
    if kind == "surveil":
        return tuple(oid for oid in available if score(oid) == 0)
    if kind == "reorder_top":
        return ordered
    if kind == "shuffle":
        return bool(available) and all(score(oid) == 0 for oid in available)
    if kind in {"discard", "put_back"}:
        return tuple(sorted(available, key=lambda oid: score(oid)))[:count]
    raise ValueError("Unknown library choice kind")


def resolve_library_actions(zones, seat, actions, *, select=None):
    """Apply reviewed library actions in printed order to physical card IDs.

    select(kind, available_ids, count, zones, seat) supplies legal choices:
    scry -> {"bottom": ids, "top": ids}; surveil -> ids to graveyard;
    reorder_top -> complete top-first permutation; shuffle -> bool;
    discard/put_back -> exactly count current-hand IDs.

    No replacements, priority, library loss, card selection or timing are
    invented. A host must process SBA and use an appropriate policy.
    """
    actions = tuple(actions)
    needed = required_draws(actions)
    if type(seat) is not int or not 0 <= seat < zones.seats:
        raise ValueError("Invalid library action seat")
    # A mandatory mill before a required draw cannot be shortened merely to
    # preserve that draw; the bounded host must handle library-loss SBA before
    # permitting this compound recipe. A mill-only action may mill fewer cards.
    mandatory_mill=sum(a.count for a in actions if a.kind=="mill")
    if len(zones.ids(seat, "library")) < needed + (mandatory_mill if needed else 0):
        raise ValueError("Library cannot satisfy mandatory draws in bounded mode")
    if select is None:
        select = bounded_library_choice
    if not callable(select):
        raise TypeError("Library selector must be callable")
    drawn, discarded, milled, bottomed, returned, steps = [], [], [], [], [], []
    remaining_draws = needed
    last_inspected = ()

    for action in actions:
        kind, count = action.kind, action.count
        record = {"kind": kind, "count": count}
        if kind in {"scry", "surveil", "reorder_top"}:
            inspected = tuple(reversed(
                zones.ids(seat, "library")[-count:]))
            last_inspected = inspected
            record["seen"] = _cards(zones, inspected)

            if kind == "scry":
                choice = select(kind, inspected, count, zones, seat)
                if not isinstance(choice, dict):
                    raise ValueError("Scry needs bottom and top order")
                chosen_bottom = tuple(choice.get("bottom", ()))
                chosen_top = tuple(choice.get("top", ()))
                if (len(set(chosen_bottom + chosen_top)) != len(inspected)
                        or set(chosen_bottom + chosen_top) != set(inspected)):
                    raise ValueError("Invalid scry ordering choice")
                # Selection cannot silently draw from an emptied library.
                limit = len(zones.ids(seat, "library")) - remaining_draws
                if len(chosen_bottom) > limit:
                    if select is not bounded_library_choice:
                        raise ValueError("Scry would strand mandatory draws")
                    chosen_bottom = chosen_bottom[:limit]
                    chosen_top = tuple(oid for oid in inspected
                                       if oid not in chosen_bottom)
                scry_physical_cards(
                    zones, seat, count, bottom_ids=chosen_bottom,
                    top_ids=chosen_top)
                bottomed.extend(chosen_bottom)
                record["bottomed"] = _cards(zones, chosen_bottom)
                record["top_order"] = _cards(zones, chosen_top)

            elif kind == "surveil":
                chosen = tuple(select(kind, inspected, count, zones, seat))
                if len(set(chosen)) != len(chosen) or not set(chosen) <= set(inspected):
                    raise ValueError("Surveil must select inspected physical cards")
                limit = len(zones.ids(seat, "library")) - remaining_draws
                if len(chosen) > limit:
                    if select is not bounded_library_choice:
                        raise ValueError("Surveil would strand mandatory draws")
                    chosen = chosen[:limit]
                record["to_graveyard"] = _cards(zones, chosen)
                for oid in chosen:
                    # The physical kernel's reason vocabulary predates surveil.
                    # Use a resolving spell's legal zone-move reason; keep
                    # the action recorded as surveil, never mill.
                    new_id = zones.move(oid, "graveyard", "resolve")
                    milled.append(new_id)

            else:
                chosen = tuple(select(kind, inspected, count, zones, seat))
                if len(chosen) != len(inspected) or set(chosen) != set(inspected):
                    raise ValueError("Reorder must preserve all inspected cards")
                scry_physical_cards(zones, seat, count,
                                    bottom_ids=(), top_ids=chosen)
                record["top_order"] = _cards(zones, chosen)

        elif kind == "shuffle":
            chosen = select(kind, last_inspected, 0, zones, seat)
            if type(chosen) is not bool:
                raise ValueError("Optional shuffle decision must be Boolean")
            if chosen:
                zones.shuffle(seat)
            record["shuffled"] = chosen
            last_inspected = ()

        elif kind == "mill":
            # Unlike a failed mandatory draw, milling beyond an empty
            # library is legal and simply moves whatever remains.
            actual=min(count,len(zones.ids(seat,"library")))
            ids=mill_physical_cards(zones,seat,CardQuantity(actual))
            milled.extend(ids)
            record["milled"]=_cards(zones,ids)

        elif kind == "draw":
            outcome = draw_physical_cards(zones, seat, CardQuantity(count))
            if not outcome.complete:
                raise AssertionError("Validated library draw unexpectedly failed")
            drawn.extend(outcome.drawn_ids)
            remaining_draws -= count
            record["drawn"] = _cards(zones, outcome.drawn_ids)

        elif kind in {"discard", "put_back"}:
            eligible = tuple(zones.ids(seat, "hand"))
            chosen = tuple(select(kind, eligible, count, zones, seat))
            if (len(chosen) != count or len(set(chosen)) != count
                    or not set(chosen) <= set(eligible)):
                raise ValueError("Illegal library/hand selection")
            record["selected"] = _cards(zones, chosen)
            if kind == "discard":
                for oid in chosen:
                    discarded.append(zones.discard(seat, oid))
            else:
                # First selected card will be on the top of the library.
                moves = {}
                for oid in reversed(chosen):
                    moves[oid] = zones.move(oid, "library", "resolve")
                new_top_ids = tuple(moves[oid] for oid in chosen)
                returned.extend(new_top_ids)
                record["new_top_ids"] = list(new_top_ids)
        steps.append(record)

    return LibraryOutcome(tuple(drawn), tuple(discarded), tuple(milled),
                          tuple(bottomed), tuple(returned), tuple(steps))
