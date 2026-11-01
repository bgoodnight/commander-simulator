"""Reviewed, stackable generic spell-cost reductions on real battlefield IDs.

A source must match pinned Oracle identity and printed text. A reduction changes
the generic portion of a fixed spell cost only: colored requirements remain.
No effect is inferred from a similar name or unsupported printed abilities.
"""
from dataclasses import dataclass

from .mana_costs import FixedManaCost, parse_fixed_mana_cost


@dataclass(frozen=True)
class CostReducer:
    oracle_id: str
    excerpt: str
    scope: str
    amount: int = 1

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt
                or self.scope not in {"instant_sorcery", "blue", "tokens_instant_sorcery"}
                or type(self.amount) is not int or self.amount <= 0):
            raise ValueError("Invalid reviewed cost reducer")


REDUCERS = {
    "Baral, Chief of Compliance": CostReducer(
        "baf80db7-2ca8-4bfc-b5b6-25ed51878dd7",
        "Instant and sorcery spells you cast cost {1} less to cast.",
        "instant_sorcery"),
    "Goblin Electromancer": CostReducer(
        "81f06f84-1580-43c0-89d5-08d34541a519",
        "Instant and sorcery spells you cast cost {1} less to cast.",
        "instant_sorcery"),
    "Stormcatch Mentor": CostReducer(
        "b2252471-01ca-4d58-aa99-4ab0aa5eae12",
        "Instant and sorcery spells you cast cost {1} less to cast.",
        "instant_sorcery"),
    "Sapphire Medallion": CostReducer(
        "f1ef5698-14bd-42bf-aae5-2870699e4186",
        "Blue spells you cast cost {1} less to cast.", "blue"),
    "Magnus the Red": CostReducer(
        "86c9b01e-18a2-4616-8e04-5343f97d2efe",
        "Instant and sorcery spells you cast cost {1} less to cast for each creature token you control.",
        "tokens_instant_sorcery"),
}


def reduction_for_spell(kernel, catalog, seat, *, spell_types, spell_colors):
    """Return typed source evidence and sum of approved generic reductions."""
    if type(seat) is not int or not 0 <= seat < 4:
        raise ValueError("Invalid player seat")
    if not isinstance(spell_types, frozenset) or not isinstance(spell_colors, frozenset):
        raise TypeError("Spell characteristics must be verified sets")
    if not spell_types or not spell_types <= {
            "creature", "artifact", "enchantment", "instant", "sorcery",
            "planeswalker", "battle"}:
        raise ValueError("Unreviewed spell type")
    if any(c not in "WUBRG" for c in spell_colors):
        raise ValueError("Invalid printed spell color")
    battlefield = [obj for obj in kernel.objects.values()
                   if obj.zone == "battlefield" and obj.controller == seat]
    token_creatures = sum(obj.token and "creature" in obj.types for obj in battlefield)
    sources = []
    for obj in sorted(battlefield, key=lambda x: x.object_id):
        rule = REDUCERS.get(obj.card.name)
        raw = catalog.get(obj.card.name)
        if (rule is None or not isinstance(raw, dict)
                or raw.get("oracle_id") != rule.oracle_id
                or rule.excerpt not in raw.get("oracle_text", "")
                or obj.card.card_id != rule.oracle_id):
            continue
        if rule.scope in {"instant_sorcery", "tokens_instant_sorcery"}:
            if not spell_types & {"instant", "sorcery"}:
                continue
        if rule.scope == "blue" and "U" not in spell_colors:
            continue
        amount = (token_creatures * rule.amount
                  if rule.scope == "tokens_instant_sorcery" else rule.amount)
        if amount:
            sources.append((obj.object_id, obj.card.name, amount))
    return tuple(sources)


def reduced_fixed_cost(kernel, catalog, seat, mana_cost, *,
                       spell_types, spell_colors):
    """Return (cost, sources) preserving the printed colored pip requirement."""
    base = parse_fixed_mana_cost(mana_cost)
    sources = reduction_for_spell(
        kernel, catalog, seat,
        spell_types=spell_types, spell_colors=spell_colors)
    discount = sum(amount for _, _, amount in sources)
    return FixedManaCost(max(0, base.generic - discount), base.colored), sources


def cost_symbols(cost: FixedManaCost):
    if not isinstance(cost, FixedManaCost):
        raise TypeError("Expected an authorized fixed cost")
    return "{" + str(cost.generic) + "}" + "".join("{" + c + "}" for c in cost.colored)
