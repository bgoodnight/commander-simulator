"""Reusable source-reviewed combat-damage-to-player recipes.

The existing combat host verifies unblocked positive damage before dispatch.
Steps operate on the same physical kernel; no inferred keyword or Oracle parser
grants card behavior, and combat legality remains the responsibility of host.
"""
from dataclasses import dataclass

from .reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches


@dataclass(frozen=True)
class PlayerDamageStep:
    kind: str
    amount: int = 1
    token: TokenBlueprint | None = None

    def __post_init__(self):
        if (self.kind not in {"create_tokens", "damaged_player_discards"}
                or type(self.amount) is not int or self.amount < 1
                or (self.kind == "create_tokens") != (self.token is not None)):
            raise ValueError("Invalid combat-damage operation")


@dataclass(frozen=True)
class CombatDamageRule:
    oracle_id: str
    oracle_text: str
    steps: tuple[PlayerDamageStep, ...]

    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text or not self.steps
                or not all(isinstance(s, PlayerDamageStep) for s in self.steps)):
            raise ValueError("Invalid source-verified combat damage recipe")


_SPAWN = TokenBlueprint("Spawn", frozenset({"creature"}),
    frozenset({"Spawn"}), frozenset({"R"}), 3, 3)
_ZOMBIE = TokenBlueprint("Zombie", frozenset({"creature"}),
    frozenset({"Zombie"}), frozenset({"B"}), 2, 2, tapped=True)

RULES = {
    "Magnus the Red": CombatDamageRule(
        "86c9b01e-18a2-4616-8e04-5343f97d2efe",
        "Flying\nUnearthly Power — Instant and sorcery spells you cast cost {1} less to cast for each creature token you control.\nBlade of Magnus — Whenever Magnus the Red deals combat damage to a player, create a 3/3 red Spawn creature token.",
        (PlayerDamageStep("create_tokens", token=_SPAWN),)),
    "Liliana's Reaver": CombatDamageRule(
        "97332d4e-a55c-4e4f-9040-bf426a7c8e39",
        "Deathtouch\nWhenever this creature deals combat damage to a player, that player discards a card and you create a tapped 2/2 black Zombie creature token.",
        (PlayerDamageStep("damaged_player_discards"),
         PlayerDamageStep("create_tokens", token=_ZOMBIE))),
}


@dataclass(frozen=True)
class CombatDamageOutcome:
    source_id: int
    damaged_player: int
    damage: int
    token_ids: tuple[int, ...]
    discarded_ids: tuple[int, ...]


def reviewed_combat_damage(name, raw):
    rule = RULES.get(name)
    return rule if (rule is not None and isinstance(raw, dict)
                    and raw.get("oracle_id") == rule.oracle_id
                    and raw.get("oracle_text") == rule.oracle_text) else None


def resolve_combat_damage_player(zones, catalog, source_id, damaged_player,
                                 damage, *, choose_discard=None):
    """Resolve a confirmed unblocked combat damage event, once per host call.

    Damaged player's discard choice may be supplied as a callback accepting
    (seat, physical_hand_ids). The bounded default chooses the first hand card.
    If that player has an empty hand, discard is impossible but other printed
    steps still resolve. Host owns exactly-once combat-event dispatch.
    """
    kernel = zones.kernel
    source = kernel.objects.get(source_id)
    if (source is None or source.zone != "battlefield"
            or "creature" not in source.types
            or type(damaged_player) is not int
            or damaged_player not in kernel.life_totals
            or damaged_player == source.controller
            or type(damage) is not int or damage <= 0):
        return None
    rule = reviewed_combat_damage(source.card.name, catalog.get(source.card.name))
    if rule is None or source.card.card_id != rule.oracle_id:
        return None
    if choose_discard is not None and not callable(choose_discard):
        raise TypeError("Discard selection must be callable")
    controller = source.controller
    selected = []
    for step in rule.steps:
        if step.kind == "damaged_player_discards":
            current = tuple(zones.ids(damaged_player, "hand"))
            if current:
                selected_id = (choose_discard(damaged_player, current)
                               if choose_discard is not None else current[0])
                if type(selected_id) is not int or selected_id not in current:
                    raise ValueError("Player must choose a card from their own hand")
                selected.append(selected_id)
    # Selection is prevalidated before mutating any physical zones/tokens.
    selected_iter = iter(selected)
    created = []
    discarded = []
    for step in rule.steps:
        if step.kind == "damaged_player_discards" and selected:
            discarded.append(zones.discard(damaged_player, next(selected_iter)))
        elif step.kind == "create_tokens":
            from dataclasses import replace
            created.extend(create_reviewed_token_batches(
                zones, controller, (replace(step.token, count=step.amount),)))
    return CombatDamageOutcome(
        source_id, damaged_player, damage, tuple(created), tuple(discarded))
