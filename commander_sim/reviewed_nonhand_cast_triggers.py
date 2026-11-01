"""Reviewed triggers responding to a cast originating outside the hand.

Consumes real cast events from the original physical kernel. First supported
card: Poxwalkers. A verified nonhand cast returns the real graveyard card tapped.
No inferred combos, phantom permanents, or Oracle-text parsing.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NonhandCastReview:
    oracle_id: str
    oracle_text: str


POXWALKERS_ORACLE = "e4275202-4960-4cde-b941-27be8163ad6e"
POXWALKERS_TEXT = (
    "Deathtouch\nCurse of the Walking Pox — Whenever you cast a spell "
    "from anywhere other than your hand, return this card from your graveyard "
    "to the battlefield tapped."
)

NONHAND_CAST_TRIGGERS = {
    "Poxwalkers": NonhandCastReview(POXWALKERS_ORACLE, POXWALKERS_TEXT),
}


def resolve_reviewed_nonhand_cast_triggers(zones, seat, ticket, catalog):
    """Resolve only a verified original physical cast event.

    Ticket must be the currently pending physical stack ticket. The bounded
    host resolves this trigger without opponent priority, while retaining
    correct source and zone provenance for a future full-stack driver.
    """
    if type(seat) is not int or not 0 <= seat < zones.seats:
        raise ValueError("Invalid caster")
    pending = getattr(zones, "_pending", {})
    if pending.get(ticket.object_id) != ticket:
        raise ValueError("Not an active physical cast ticket")
    source = zones.kernel.objects.get(ticket.object_id)
    if source is None or source.zone != "stack" or source.controller != seat:
        raise ValueError("Cast source not on actor stack")
    events = zones.kernel.events
    if not events:
        raise ValueError("Missing authoritative spell-cast event")
    event = events[-1]
    if (event.name != "spell_cast" or event.source_id != ticket.object_id
            or event.controller != seat):
        raise ValueError("Trigger requires the immediate original cast event")
    origin = dict(event.metadata).get("origin", "hand")
    if origin not in {"hand", "graveyard", "command", "exile"}:
        raise ValueError("Unrecognized verified casting origin")
    if origin == "hand":
        return ()
    outcomes = []
    for oid in tuple(zones.ids(seat, "graveyard")):
        obj = zones.kernel.get(oid)
        rule = NONHAND_CAST_TRIGGERS.get(obj.card.name)
        raw = catalog.get(obj.card.name)
        if (rule is None or not isinstance(raw, dict)
                or raw.get("oracle_id") != rule.oracle_id
                or raw.get("oracle_text") != rule.oracle_text
                or obj.card.card_id != rule.oracle_id
                or "creature" not in obj.types
                or obj.owner != seat):
            continue
        new_id = zones.move(oid, "battlefield", "resolve")
        zones.kernel.get(new_id).tapped = True
        zones.kernel._dirty()
        outcomes.append({
            "card": obj.card.name, "source_graveyard_id": oid,
            "object_id": new_id, "triggered_by_stack_id": ticket.object_id,
            "origin": origin})
    return tuple(outcomes)
