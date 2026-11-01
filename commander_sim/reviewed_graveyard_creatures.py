"""Conditional casting permissions from the physical graveyard.

This adds reviewed permanent-cast permissions, not predefined combos. A cast
moves the actual graveyard card through the shared stack into the battlefield,
pays the normal source-backed mana cost, and generates the kernel's real
spell-cast event. Only reviewed Oracle sources can grant permission.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GraveyardCreaturePermission:
    oracle_id: str
    oracle_text: str
    printed_cost: str
    required_controlled_subtype: str


GRAVEYARD_CREATURES = {
    "Gravecrawler": GraveyardCreaturePermission(
        "09ff28b1-b6c9-48e6-b12e-2f0e644f709f",
        "This creature can't block.\n"
        "You may cast this card from your graveyard as long as you control a Zombie.",
        "{B}", "Zombie"),
}


def reviewed_graveyard_creature(name, raw):
    rule = GRAVEYARD_CREATURES.get(name)
    if (rule is None or not isinstance(raw, dict)
            or raw.get("oracle_id") != rule.oracle_id
            or raw.get("oracle_text") != rule.oracle_text
            or raw.get("mana_cost") != rule.printed_cost
            or "Creature" not in raw.get("type_line", "").split(" — ", 1)[0]):
        return None
    return rule


def graveyard_creature_cast_ready(zones, seat, object_id, catalog):
    """Pure authorization check, including the *current* battlefield."""
    if type(seat) is not int or not 0 <= seat < zones.seats:
        raise ValueError("Invalid seat")
    if object_id not in zones.ids(seat, "graveyard"):
        return None
    obj = zones.kernel.get(object_id)
    raw = catalog.get(obj.card.name)
    rule = reviewed_graveyard_creature(obj.card.name, raw)
    if (rule is None or obj.card.card_id != rule.oracle_id
            or obj.owner != seat or obj.zone != "graveyard"
            or "creature" not in obj.types
            or obj.card.coverage == "unimplemented"):
        return None
    controlled = [o for o in zones.kernel.objects.values()
                  if o.zone == "battlefield" and o.controller == seat
                  and "creature" in o.types
                  and rule.required_controlled_subtype in o.subtypes]
    return rule if controlled else None


@dataclass(frozen=True)
class GraveyardCreatureCastResult:
    source_old_id: int
    stack_id: int
    permanent_id: int
    card_name: str
    paid_source_ids: tuple[int, ...]


def cast_reviewed_graveyard_creature(
        zones, seat, object_id, catalog, mana_service, *,
        sorcery_window=False, on_cast=None):
    """Cast an eligible graveyard creature at an authorized sorcery window.

    One shared physical ticket, no exile replacement and no token duplication.
    Caller supplies the timing window. This is the enabling primitive for
    repetitive sacrifice/recursion effects, not a loop runner.
    """
    if sorcery_window is not True:
        raise ValueError("Creature graveyard cast needs verified sorcery timing")
    rule = graveyard_creature_cast_ready(zones, seat, object_id, catalog)
    if rule is None:
        raise ValueError("Conditional graveyard cast permission not satisfied")
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("Physical mana service must own the same kernel")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("Cast notification must be callable")
    source = zones.kernel.get(object_id)
    payment_plan = mana_service.plan_spell(seat, rule.printed_cost, source)
    if payment_plan is None:
        return None
    # The pilot supplies a single-threaded window. Requirements were checked
    # before irreversible mana activation; the same physical object is cast.
    paid = mana_service.pay_spell(seat, rule.printed_cost, source)
    ticket = zones.cast(seat, object_id, reviewed_origin="graveyard")
    if on_cast is not None:
        on_cast(ticket)
    entered = zones.resolve(ticket)
    return GraveyardCreatureCastResult(
        object_id, ticket.object_id, entered, source.card.name,
        paid.source_ids)
