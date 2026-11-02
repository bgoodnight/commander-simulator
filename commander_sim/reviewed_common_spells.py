"""Shared source-paid Commander spell operations with pinned printed profiles.

This module adds *operations*, not card-specific game engines. Spell profiles
are declarative sequences of the same physical draw/life/token operations.
The bounded policy owns X, victims and whether to cast. No opponent priority,
stack interaction or multiplayer targeting AI is asserted.
"""
from dataclasses import dataclass
from .generic_cast import ReviewedCreatureCast, cast_reviewed_spell
from .physical_common_effects import CardQuantity, draw_physical_cards
from .reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches
from .reviewed_death_effects import capture_battlefield

_TREASURE = TokenBlueprint(
    "Treasure", frozenset({"artifact"}), frozenset({"Treasure"}),
    frozenset(), 0, 0)


@dataclass(frozen=True)
class SpellStep:
    kind: str
    quantity: int = 0
    def __post_init__(self):
        if self.kind not in {"draw", "lose_life", "opponent_drain_x",
                             "treasure"} or type(self.quantity) is not int:
            raise ValueError("Unreviewed common spell step")


@dataclass(frozen=True)
class SpellRecipe:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    spell_type: str
    steps: tuple[SpellStep, ...]
    sacrifice_cost: str = ""
    variable_x: bool = False
    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text or not self.mana_cost
                or self.spell_type not in {"instant", "sorcery"}
                or not self.steps or not all(isinstance(s, SpellStep) for s in self.steps)
                or self.sacrifice_cost not in {"", "artifact_or_creature", "optional_creatures"}):
            raise ValueError("Incomplete reviewed spell recipe")


RECIPES = {
    "Sign in Blood": SpellRecipe(
        "c6207f6a-a624-4754-88f5-dbe700c841ff",
        "Target player draws two cards and loses 2 life.",
        "{B}{B}", "sorcery", (SpellStep("draw", 2), SpellStep("lose_life", 2))),
    "Exsanguinate": SpellRecipe(
        "8164b1e8-3350-465e-8a17-75f57d326344",
        "Each opponent loses X life. You gain life equal to the life lost this way.",
        "{X}{B}{B}", "sorcery", (SpellStep("opponent_drain_x"),), variable_x=True),
    "Deadly Dispute": SpellRecipe(
        "457af74a-02b3-4659-846d-63e482667f34",
        "As an additional cost to cast this spell, sacrifice an artifact or creature.\nDraw two cards and create a Treasure token. (It's an artifact with \"{T}, Sacrifice this token: Add one mana of any color.\")",
        "{1}{B}", "instant",
        (SpellStep("draw", 2), SpellStep("treasure", 1)),
        sacrifice_cost="artifact_or_creature"),
    "Plumb the Forbidden": SpellRecipe(
        "b099fc54-cdbc-46cb-b4e4-7c2ca77b115b",
        "As an additional cost to cast this spell, you may sacrifice one or more creatures. When you do, copy this spell for each creature sacrificed this way.\nYou draw a card and lose 1 life.",
        "{1}{B}", "instant", (SpellStep("draw", 1), SpellStep("lose_life", 1)),
        sacrifice_cost="optional_creatures"),
}


def reviewed_common_spell(name, raw):
    recipe = RECIPES.get(name)
    if (recipe is None or not isinstance(raw, dict)
            or raw.get("oracle_id") != recipe.oracle_id
            or raw.get("oracle_text") != recipe.oracle_text
            or raw.get("mana_cost") != recipe.mana_cost
            or raw.get("type_line", "").split(" — ", 1)[0].lower() != recipe.spell_type):
        return None
    return recipe


def spell_payment_cost(recipe, x=0):
    if type(x) is not int or x < 0:
        raise ValueError("X must be nonnegative")
    if not recipe.variable_x and x:
        raise ValueError("Fixed-cost spell cannot pay X")
    return recipe.mana_cost.replace("{X}", "{" + str(x) + "}")


@dataclass(frozen=True)
class CommonSpellResult:
    name: str
    paid_source_ids: tuple[int, ...]
    created_token_ids: tuple[int, ...]
    drawn_ids: tuple[int, ...]
    sacrificed_ids: tuple[int, ...]
    life_lost: int
    graveyard_id: int


def cast_common_spell(zones, life, seat, source_id, catalog, commander_colors,
                      mana_service, *, x=0, sacrifice_ids=(), death_engine=None,
                      turn=1, on_cast=None):
    """Execute source-reviewed spell plus physical additional-cost sacrifice.

    Choices are explicit. None is returned for unaffordable spells; malformed
    or illegal sacrifices raise before committing a spell. This operation
    does not secretly cast unsupported copies or search opponent targets.
    """
    if source_id not in zones.ids(seat,"hand") or life.kernel is not zones.kernel:
        raise ValueError("Physical spell source or life host mismatch")
    if mana_service.kernel is not zones.kernel:
        raise ValueError("Mana source mismatch")
    source = zones.kernel.get(source_id)
    recipe = reviewed_common_spell(source.card.name,catalog.get(source.card.name))
    if recipe is None or source.card.card_id != recipe.oracle_id:
        raise ValueError("Unreviewed printed spell profile")
    cost=spell_payment_cost(recipe,x)
    ids=tuple(sacrifice_ids)
    if len(set(ids)) != len(ids):
        raise ValueError("Cannot sacrifice one permanent twice")
    if recipe.sacrifice_cost == "" and ids:
        raise ValueError("This spell has no sacrifice cost")
    if recipe.sacrifice_cost == "artifact_or_creature" and len(ids)!=1:
        raise ValueError("Exactly one artifact or creature must be sacrificed")
    for oid in ids:
        obj=zones.kernel.objects.get(oid)
        if (obj is None or obj.zone!="battlefield" or obj.controller!=seat
                or not bool(obj.types & ({"artifact","creature"}
                      if recipe.sacrifice_cost=="artifact_or_creature" else {"creature"}))):
            raise ValueError("Illegal physical additional-cost sacrifice")
    copies=1+len(ids) if recipe.sacrifice_cost=="optional_creatures" else 1
    draw_need=copies*sum(s.quantity for s in recipe.steps if s.kind=="draw")
    if len(zones.ids(seat,"library"))<draw_need:
        return None
    if (copies*sum(s.quantity for s in recipe.steps if s.kind=="lose_life")
            >= life.total(seat)):
        return None
    review=ReviewedCreatureCast(recipe.oracle_id,cost,True,
                    ("Bounded/no priority; pilot supplies all optional choices",))
    if mana_service.plan_spell(seat,cost,source) is None:
        return None
    before=capture_battlefield(zones.kernel)
    move_index=len(zones.kernel.moves)
    # Source-paid physical cast, then additional sacrifices before cast triggers.
    committed=cast_reviewed_spell(zones,seat,source_id,review,commander_colors,
                                  mana_service=mana_service,spell_type=recipe.spell_type)
    if committed is None:
        return None
    for oid in ids:
        zones.move(oid,"graveyard","sacrifice")
    if ids and death_engine is not None:
        death_engine.resolve_deaths(before,move_index=move_index,turn=turn)
    if on_cast is not None:
        on_cast(committed.ticket)
    drawn=[]
    created=[]
    life_lost=[0]
    def execute(kernel,ticket):
        for _ in range(copies):
            for step in recipe.steps:
                if step.kind=="draw":
                    result=draw_physical_cards(zones,seat,CardQuantity(step.quantity))
                    if not result.complete:
                        raise AssertionError("Checked library draw unexpectedly incomplete")
                    drawn.extend(result.drawn_ids)
                elif step.kind=="lose_life":
                    life.lose(seat,step.quantity,source_id)
                    life_lost[0]+=step.quantity
                elif step.kind=="treasure":
                    created.extend(create_reviewed_token_batches(
                        zones,seat,(_TREASURE,)))
                elif step.kind=="opponent_drain_x":
                    lost=0
                    for opponent in sorted(life.kernel.life_totals):
                        if opponent==seat:
                            continue
                        # Respect actual remaining life rather than awarding
                        # phantom life from a player already at zero.
                        n=min(x,max(0,life.total(opponent)))
                        life.lose(opponent,n,source_id)
                        lost+=n
                    if lost:
                        life.gain(seat,lost,source_id)
    gy=zones.resolve(committed.ticket,effect=execute)
    return CommonSpellResult(source.card.name,tuple(committed.paid_source_ids),
                             tuple(created),tuple(drawn),ids,life_lost[0],gy)
