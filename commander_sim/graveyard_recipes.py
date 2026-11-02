"""Typed, reusable graveyard-to-zone recipes on authoritative physical cards.

Descriptors enforce printed source/destination/ownership/type constraints.
No descriptor grants timing, targeting, cast-from-zone permission, or priority:
callers must independently review and pay the card/ability first. Every batch
is validated before the first kernel movement (never invent new card objects).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GraveyardRecipe:
    destination: str
    ownership: str = "own"     # own, opponent, any
    allowed_types_any: frozenset[str] = frozenset()
    required_subtypes: frozenset[str] = frozenset()
    required_supertypes: frozenset[str] = frozenset()
    controller_on_entry: str = "owner"  # owner or actor
    enter_tapped: bool = False
    enter_counters: tuple[str, int] = ("", 0)
    required_types_all: frozenset[str] = frozenset()

    def __post_init__(self):
        kind, count = self.enter_counters if (
            isinstance(self.enter_counters, tuple)
            and len(self.enter_counters) == 2) else (None, None)
        if (self.destination not in {"hand", "battlefield", "library", "exile"}
                or self.ownership not in {"own", "opponent", "any"}
                or self.controller_on_entry not in {"owner", "actor"}
                or not all(isinstance(items, frozenset) and
                           all(isinstance(x, str) and x for x in items)
                           for items in (self.allowed_types_any,
                                         self.required_subtypes,
                                         self.required_supertypes,
                                         self.required_types_all))
                or type(self.enter_tapped) is not bool
                or type(kind) is not str or type(count) is not int
                or count < 0 or bool(kind) != bool(count)
                or (self.destination != "battlefield"
                    and (self.enter_tapped or count
                         or self.controller_on_entry != "owner"))):
            raise ValueError("Invalid graveyard effect recipe")


@dataclass(frozen=True)
class GraveyardMove:
    old_id: int
    new_id: int
    card_name: str
    original_owner: int
    destination: str


def _allowed(zones, actor, oid, recipe):
    obj = zones.kernel.objects.get(oid)
    if obj is None or obj.zone != "graveyard" or obj.token:
        return False
    if (recipe.ownership == "own" and obj.owner != actor
            or recipe.ownership == "opponent" and obj.owner == actor):
        return False
    if (recipe.allowed_types_any
            and not obj.types.intersection(recipe.allowed_types_any)):
        return False
    if recipe.required_types_all and not recipe.required_types_all <= obj.types:
        return False
    if recipe.required_subtypes and not recipe.required_subtypes <= obj.subtypes:
        return False
    if (recipe.required_supertypes
            and not recipe.required_supertypes <= obj.card.supertypes):
        return False
    return oid in zones.ids(obj.owner, "graveyard")


def eligible_graveyard_cards(zones, actor, recipe: GraveyardRecipe):
    """Return matching physical IDs without selecting, moving or granting access."""
    if not isinstance(recipe, GraveyardRecipe):
        raise TypeError("Expected typed graveyard recipe")
    if type(actor) is not int or actor < 0 or actor >= zones.seats:
        raise ValueError("Invalid graveyard effect actor")
    return tuple(oid for owner in range(zones.seats)
                 for oid in zones.ids(owner, "graveyard")
                 if _allowed(zones, actor, oid, recipe))


def resolve_graveyard_recipe(zones, actor, object_ids, recipe: GraveyardRecipe):
    """Prevalidate a whole finite batch and apply exact zone moves in order.

    For destination=library, the FIRST supplied ID must end up on top.
    The game kernel generates new IDs on transitions; old physical cards are
    not duplicated. Battlefield controller/tap/counters are explicit args.
    """
    if not isinstance(recipe, GraveyardRecipe):
        raise TypeError("Expected typed graveyard recipe")
    if type(actor) is not int or not 0 <= actor < zones.seats:
        raise ValueError("Invalid graveyard effect actor")
    ids = tuple(object_ids)
    if (len(ids) > 100 or len(set(ids)) != len(ids)
            or any(type(oid) is not int or
                   not _allowed(zones, actor, oid, recipe) for oid in ids)):
        raise ValueError("Illegal graveyard recipe selection")
    outcome = []
    moves = reversed(ids) if recipe.destination == "library" else ids
    for oid in moves:
        before = zones.kernel.get(oid)
        owner, name = before.owner, before.card.name
        # Exile uses the kernel's native exile reason. Other resolutions use
        # the native 'resolve' reason; there is no custom zone-reason shortcut.
        moved = zones.move(oid, recipe.destination,
                           "exile" if recipe.destination == "exile"
                           else "resolve")
        if moved is None:
            raise AssertionError("Reviewed graveyard zone move did not produce an ID")
        if recipe.destination == "battlefield":
            target = zones.kernel.get(moved)
            if recipe.controller_on_entry == "actor":
                target.controller = actor
            if recipe.enter_tapped:
                target.tapped = True
            if (recipe.controller_on_entry == "actor"
                    or recipe.enter_tapped):
                zones.kernel._dirty()
            kind, count = recipe.enter_counters
            if count:
                zones.kernel.add_counter(moved, kind, count)
        outcome.append(GraveyardMove(oid, moved, name, owner,
                                     recipe.destination))
    # Reordering the batch for library puts the first selected object top.
    if recipe.destination == "library":
        outcome.reverse()
    return tuple(outcome)


def select_bounded_graveyard_batch(zones, actor, recipe: GraveyardRecipe,
                                  catalog, *, max_total_mana_value=None,
                                  max_count=100):
    """Choose a finite legal subset under a printed mana-value budget.

    Bounded policy: prefer higher printed mana-value eligible cards, then
    stable object ID. This is NOT optimal strategy. Fail closed if metadata
    is missing or conflicts with a real physical Oracle ID. A caller still
    must independently authorize any recursion effect and pay its costs.
    """
    if (not isinstance(catalog,dict)
            or max_total_mana_value is not None and
            (type(max_total_mana_value) is not int or
             max_total_mana_value < 0)
            or type(max_count) is not int or not 0<=max_count<=100):
        raise ValueError("Invalid pinned graveyard selection budget")
    candidates=eligible_graveyard_cards(zones,actor,recipe)
    values={}
    for oid in candidates:
        obj=zones.kernel.get(oid)
        row=catalog.get(obj.card.name)
        if (not isinstance(row,dict)
                or row.get("oracle_id")!=obj.card.card_id):
            # Unknown card identity cannot be silently assigned a CMC.
            continue
        printed=row.get("cmc")
        if (type(printed) not in (int,float)
                or printed<0 or int(printed)!=printed):
            continue
        values[oid]=int(printed)
    chosen=[]
    budget=max_total_mana_value
    for oid in sorted(values,key=lambda ident:(-values[ident],ident)):
        if len(chosen)>=max_count:
            break
        mv=values[oid]
        if budget is None or mv<=budget:
            chosen.append(oid)
            if budget is not None:
                budget-=mv
    return tuple(chosen)
