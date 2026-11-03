"""Reviewed attack-trigger recipes using shared physical token creation.

This module does not declare attackers, grant attack permission, or interpret
arbitrary Oracle text. The combat host calls it once after an attacker is
declared; no separate battlefield or event bus is introduced.
"""
from dataclasses import dataclass

from .reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches


@dataclass(frozen=True)
class AttackTokenRecipe:
    oracle_id: str
    oracle_text: str
    token_name: str
    token_types: frozenset[str]
    token_subtypes: frozenset[str]
    token_colors: frozenset[str]
    power: int
    toughness: int
    amount: int

    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text or not self.token_name
                or not self.token_types or not self.token_subtypes
                or not isinstance(self.token_colors, frozenset)
                or type(self.power) is not int or type(self.toughness) is not int
                or type(self.amount) is not int or self.amount < 1):
            raise ValueError("Invalid reviewed attack token recipe")

    def blueprint(self):
        return TokenBlueprint(
            self.token_name, self.token_types, self.token_subtypes,
            self.token_colors, self.power, self.toughness, self.amount)


RULES = {
    "Grave Titan": AttackTokenRecipe(
        "f3abd4d1-a975-4e85-8684-aa0fce029670",
        "Deathtouch\nWhenever this creature enters or attacks, create two 2/2 black Zombie creature tokens.",
        "Zombie", frozenset({"creature"}), frozenset({"Zombie"}),
        frozenset({"B"}), 2, 2, 2),
}


def reviewed_attack_token_recipe(name, raw):
    """Require pinned identity and complete Oracle text, never just a name."""
    recipe = RULES.get(name)
    if (recipe is None or not isinstance(raw, dict)
            or raw.get("oracle_id") != recipe.oracle_id
            or raw.get("oracle_text") != recipe.oracle_text):
        return None
    return recipe


def resolve_attack_tokens(zones, catalog, attacker_id):
    """Resolve a declared attack's bounded token effect on the same kernel.

    The caller is responsible for declaring a legal attack exactly once;
    this function is NOT safe as a generic 'attacks?' predicate. Token ETB
    processing remains the responsibility of the existing entry engine.
    """
    attacker = zones.kernel.objects.get(attacker_id)
    if (attacker is None or attacker.zone != "battlefield"
            or "creature" not in attacker.types):
        return ()
    raw = catalog.get(attacker.card.name)
    recipe = reviewed_attack_token_recipe(attacker.card.name, raw)
    if recipe is None or attacker.card.card_id != recipe.oracle_id:
        return ()
    return tuple(create_reviewed_token_batches(
        zones, attacker.controller, (recipe.blueprint(),)))
