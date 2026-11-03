"""Source-verified attack mill recipes over one physical library and token host.

These are explicitly reviewed triggered ability *effects*. Calling this
function never declares an attack, activates crew, or creates permission to
attack. The bounded combat host invokes it once for a declared attacker.
"""
from dataclasses import dataclass, replace

from .library_actions import LibraryAction, resolve_library_actions
from .reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches


_WARRIOR = TokenBlueprint(
    "Necron Warrior", frozenset({"artifact", "creature"}),
    frozenset({"Necron", "Warrior"}), frozenset({"B"}), 2, 2)


@dataclass(frozen=True)
class AttackMillRecipe:
    oracle_id: str
    oracle_text: str
    count: int
    followup: str
    token: TokenBlueprint | None = None

    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text
                or type(self.count) is not int or not 1 <= self.count <= 7
                or self.followup not in {"retrieve_milled_artifact_creature_or_vehicle",
                                         "token_per_milled_creature"}
                or (self.followup == "token_per_milled_creature")
                   != (self.token is not None)):
            raise ValueError("Invalid attack mill recipe")


RULES = {
    "Szarekh, the Silent King": AttackMillRecipe(
        "9a63f950-2e8a-4617-896c-1d0af538dbc7",
        "Flying\nMy Will Be Done — Whenever Szarekh attacks, mill three cards. You may put an artifact creature card or Vehicle card from among the cards milled this way into your hand.",
        3, "retrieve_milled_artifact_creature_or_vehicle"),
    "Necron Monolith": AttackMillRecipe(
        "20932bca-52be-4288-9c7d-4154650c5ec9",
        "Flying, indestructible\nEternity Gate — Whenever this Vehicle attacks, mill three cards. For each creature card milled this way, create a 2/2 black Necron Warrior artifact creature token.\nCrew 4 (Tap any number of creatures you control with total power 4 or more: This Vehicle becomes an artifact creature until end of turn.)",
        3, "token_per_milled_creature", _WARRIOR),
}


@dataclass(frozen=True)
class AttackMillOutcome:
    source_id: int
    milled_ids: tuple[int, ...]
    returned_id: int | None
    token_ids: tuple[int, ...]


def reviewed_attack_mill(name, raw):
    rule = RULES.get(name)
    if (rule is None or not isinstance(raw, dict)
            or raw.get("oracle_id") != rule.oracle_id
            or raw.get("oracle_text") != rule.oracle_text):
        return None
    return rule


def resolve_attack_mill(zones, catalog, attacker_id):
    """Mill and apply a reviewed follow-up, selecting only actually milled IDs.

    No guessed object characteristics: the existing physical kernel supplies
    card types and subtypes. A returned card is the same physical object
    moved once to hand, not a copy. Token creation uses the shared emitter.
    """
    source = zones.kernel.objects.get(attacker_id)
    if (source is None or source.zone != "battlefield"
            or "creature" not in source.types):
        return None
    rule = reviewed_attack_mill(source.card.name, catalog.get(source.card.name))
    if rule is None or source.card.card_id != rule.oracle_id:
        return None
    seat = source.controller
    milled = resolve_library_actions(
        zones, seat, (LibraryAction("mill", rule.count),)).milled_ids
    returned = None
    created = ()
    if rule.followup == "retrieve_milled_artifact_creature_or_vehicle":
        eligible = tuple(oid for oid in milled
            if (({"artifact", "creature"} <= zones.kernel.get(oid).types)
                or "Vehicle" in zones.kernel.get(oid).subtypes)
            and zones.kernel.get(oid).zone == "graveyard"
            and zones.kernel.get(oid).owner == seat)
        if eligible:
            # Explicit bounded selection policy: first matching milled card.
            returned = zones.move(eligible[0], "hand", "resolve")
    elif rule.followup == "token_per_milled_creature":
        creature_count = sum("creature" in zones.kernel.get(oid).types
                             for oid in milled)
        if creature_count:
            created = tuple(create_reviewed_token_batches(
                zones, seat, (replace(rule.token, count=creature_count),)))
    return AttackMillOutcome(attacker_id, tuple(milled), returned, created)
