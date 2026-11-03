"""Reusable, reviewed attack triggers using existing payment/zone/death services.

Attack declaration and legality belong to the calling combat host. A recipe
never grants permission to attack or interpret unreviewed Oracle prose.
"""
from dataclasses import dataclass

from .graveyard_recipes import GraveyardRecipe, eligible_graveyard_cards, resolve_graveyard_recipe
from .reviewed_death_effects import capture_battlefield


@dataclass(frozen=True)
class AttackZoneRule:
    oracle_id: str
    oracle_text: str
    operation: str
    mana_cost: str = ""

    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text
                or self.operation not in {"paid_graveyard_creature_to_hand",
                                          "each_opponent_sacrifices_nonland"}
                or (self.operation == "paid_graveyard_creature_to_hand")
                   != bool(self.mana_cost)):
            raise ValueError("Invalid reviewed attack zone rule")


RULES = {
    "Eternal Taskmaster": AttackZoneRule(
        "a7c000a8-1864-4bb2-80fa-a61d74dbd966",
        "This creature enters tapped.\nWhenever this creature attacks, you may pay {2}{B}. If you do, return target creature card from your graveyard to your hand.",
        "paid_graveyard_creature_to_hand", "{2}{B}"),
    "Shard of the Void Dragon": AttackZoneRule(
        "d04d2434-121e-4420-abfc-fa21ad5577c3",
        "Flying\nSpear of the Void Dragon — Whenever this creature attacks, each opponent sacrifices a nonland permanent of their choice.\nMatter Absorption — Whenever an artifact is put into a graveyard from the battlefield or is put into exile from the battlefield, put two +1/+1 counters on this creature.",
        "each_opponent_sacrifices_nonland"),
}

_RETRIEVE = GraveyardRecipe("hand", "own", frozenset({"creature"}))


@dataclass(frozen=True)
class AttackZoneOutcome:
    operation: str
    returned_id: int | None = None
    sacrificed_old_ids: tuple[int, ...] = ()
    skipped_seats: tuple[int, ...] = ()


def reviewed_attack_zone(name, raw):
    rule = RULES.get(name)
    if (rule is None or not isinstance(raw, dict)
            or raw.get("oracle_id") != rule.oracle_id
            or raw.get("oracle_text") != rule.oracle_text):
        return None
    return rule


def resolve_attack_zone(zones, life, catalog, attacker_id, *,
                        mana_service=None, death_engine=None, turn=1,
                        choices=None):
    """Resolve one explicitly declared attack on the authoritative kernel.

    A bounded opponent choice is the lowest object ID nonland permanent, with
    a caller-supplied seat->object mapping overriding it. Unsupported commander
    replacement is deliberately rejected *before* any sacrifices occur.
    """
    kernel = zones.kernel
    source = kernel.objects.get(attacker_id)
    if (source is None or source.zone != "battlefield"
            or "creature" not in source.types):
        return None
    rule = reviewed_attack_zone(source.card.name, catalog.get(source.card.name))
    if rule is None or source.card.card_id != rule.oracle_id:
        return None
    if life.kernel is not kernel:
        raise ValueError("Life and attack effect must share the same kernel")
    if type(turn) is not int or turn < 1:
        raise ValueError("Invalid turn")
    if rule.operation == "paid_graveyard_creature_to_hand":
        if mana_service is None or mana_service.kernel is not kernel:
            return None  # cannot silently waive optional printed cost
        eligible = eligible_graveyard_cards(zones, source.controller, _RETRIEVE)
        if not eligible:
            return AttackZoneOutcome(rule.operation)
        if mana_service.plan(source.controller, rule.mana_cost) is None:
            return AttackZoneOutcome(rule.operation)
        # Deterministic choice is made before payment, not after mutation.
        chosen = min(eligible)
        if mana_service.pay(source.controller, rule.mana_cost) is None:
            raise AssertionError("Preflighted mana payment failed")
        moved = resolve_graveyard_recipe(
            zones, source.controller, (chosen,), _RETRIEVE)
        return AttackZoneOutcome(rule.operation, returned_id=moved[0].new_id)

    if choices is not None and not isinstance(choices, dict):
        raise TypeError("Sacrifice choices must be keyed by opponent seat")
    choice_map = {} if choices is None else choices
    victims = []
    skipped = []
    for seat in life.active_opponents(source.controller):
        candidates = sorted(
            o.object_id for o in kernel.on_battlefield()
            if o.controller == seat and "land" not in o.types)
        if not candidates:
            skipped.append(seat)
            continue
        picked = choice_map.get(seat, candidates[0])
        if type(picked) is not int or picked not in candidates:
            raise ValueError("Opponent sacrifice must select its own nonland permanent")
        obj = kernel.get(picked)
        if "commander" in obj.card.supertypes:
            raise NotImplementedError("Commander sacrifice replacement not modeled")
        victims.append(picked)
    if not victims:
        return AttackZoneOutcome(rule.operation, skipped_seats=tuple(skipped))
    if death_engine is not None and death_engine.zones is not zones:
        raise ValueError("Death resolver must share physical zones")
    before = capture_battlefield(kernel)
    move_index = len(kernel.moves)
    for oid in victims:
        zones.move(oid, "graveyard", "sacrifice")
    if death_engine is not None:
        death_engine.resolve_deaths(before, move_index=move_index, turn=turn)
    return AttackZoneOutcome(
        rule.operation, sacrificed_old_ids=tuple(victims),
        skipped_seats=tuple(skipped))
