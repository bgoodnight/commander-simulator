"""Source-pinned spell recipes using shared parameterized physical library actions.

Cards register only arguments and exact printed identities. Library choices
are made by a separate bounded pilot policy, not by a hardcoded card handler.
"""
from dataclasses import dataclass

from .generic_cast import ReviewedCreatureCast, cast_reviewed_spell
from .library_actions import LibraryAction, required_draws, resolve_library_actions
from .reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches


@dataclass(frozen=True)
class DrawSpellReview:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    spell_type: str
    draw_count: int
    limitations: tuple[str, ...] = ()
    actions: tuple[LibraryAction, ...] = ()
    token_batches: tuple[TokenBlueprint, ...] = ()

    def __post_init__(self):
        if not self.oracle_id or not self.oracle_text or not self.mana_cost:
            raise ValueError("Missing reviewed source identity")
        if (self.spell_type not in ("instant", "sorcery")
                or type(self.draw_count) is not int or self.draw_count < 1):
            raise ValueError("Invalid reusable draw-spell template")
        if self.actions and required_draws(self.actions) != self.draw_count:
            raise ValueError("Draw count and library recipe disagree")
        if not isinstance(self.token_batches,tuple) or any(
                not isinstance(batch,TokenBlueprint) for batch in self.token_batches):
            raise ValueError("Draw spell token batches must be physical blueprints")

    def library_actions(self):
        return self.actions or (LibraryAction("draw", self.draw_count),)


# Note how Ponder, Preordain, Consider, Brainstorm and Faithless Looting share
# the SAME action executor with different typed parameters. The historical
# flashback permission for Faithless Looting remains separately source-gated.
DRAW_SPELLS = {
    "Meeting of Minds": DrawSpellReview(
        "3b91dc3e-46ef-4a68-829f-ef7d79598cf7",
        "Convoke (Your creatures can help cast this spell. Each creature you tap while casting this spell pays for {1} or one mana of that creature's color.)\nDraw two cards.",
        "{3}{U}", "instant", 2,
        ("Optional convoke payment not yet used; only normal mana sources",)),
    "Deduce": DrawSpellReview(
        "eeae4161-9f35-45df-8b3c-c55e37f49cd1",
        'Draw a card. Investigate. (Create a Clue token. It\'s an artifact with "{2}, Sacrifice this token: Draw a card.")',
        "{1}{U}", "instant", 1,
        ("Clue activated sacrifice-and-draw not yet implemented",),
        token_batches=(TokenBlueprint(
            "Clue",frozenset({"artifact"}),frozenset({"Clue"}),
            frozenset(),0,0,1,limitations=(
                "Clue activated sacrifice-and-draw not yet implemented",)),)),
    "Quick Study": DrawSpellReview(
        "7bff8d4a-1c7d-48b8-b3e3-737dd6f01823",
        "Draw two cards.", "{2}{U}", "instant", 2),
    "Think Twice": DrawSpellReview(
        "fa85c5a2-8e83-4624-a35a-a0bbf17ecbb4",
        "Draw a card.\nFlashback {2}{U} (You may cast this card from your graveyard for its flashback cost. Then exile it.)",
        "{1}{U}", "instant", 1,
        ("Flashback permission and alternate-cost cast not modeled",)),
    "Ponder": DrawSpellReview(
        "02090581-61aa-4348-ad57-451be8ee91c2",
        "Look at the top three cards of your library, then put them back in any order. You may shuffle.\nDraw a card.",
        "{U}", "sorcery", 1,
        ("Reorder and optional shuffle use bounded pilot decisions",),
        (LibraryAction("reorder_top", 3), LibraryAction("shuffle"),
         LibraryAction("draw", 1))),
    "Preordain": DrawSpellReview(
        "ac641490-ca14-48d7-8cc4-b69ce984befa",
        "Scry 2, then draw a card. (To scry 2, look at the top two cards of your library, then put any number of them on the bottom and the rest on top in any order.)",
        "{U}", "sorcery", 1,
        ("Scry selection uses bounded pilot decisions",),
        (LibraryAction("scry", 2), LibraryAction("draw", 1))),
    "Consider": DrawSpellReview(
        "4c9bcba6-87b5-4fb3-97ee-6fe5b739337d",
        "Surveil 1. (Look at the top card of your library. You may put it into your graveyard.)\nDraw a card.",
        "{U}", "instant", 1,
        ("Surveil choice uses bounded pilot decisions",),
        (LibraryAction("surveil", 1), LibraryAction("draw", 1))),
    "Brainstorm": DrawSpellReview(
        "36cd2364-d113-47d1-b2c4-b088d9eb88dd",
        "Draw three cards, then put two cards from your hand on top of your library in any order.",
        "{U}", "instant", 3,
        ("Returned cards and top order use bounded pilot decisions",),
        (LibraryAction("draw", 3), LibraryAction("put_back", 2))),
    "Faithless Looting": DrawSpellReview(
        "3d6fa57a-aa53-4b5c-b8af-a7612c823117",
        "Draw two cards, then discard two cards.\nFlashback {2}{R} (You may cast this card from your graveyard for its flashback cost. Then exile it.)",
        "{R}", "sorcery", 2,
        ("Discard choice uses bounded pilot decisions; graveyard flashback is separate",),
        (LibraryAction("draw", 2), LibraryAction("discard", 2))),
}


def reviewed_draw_spell(name, card):
    rule = DRAW_SPELLS.get(name)
    if (rule is None or not isinstance(card, dict)
            or card.get("layout") != "normal"
            or card.get("oracle_id") != rule.oracle_id
            or card.get("oracle_text") != rule.oracle_text
            or card.get("mana_cost") != rule.mana_cost
            or card.get("type_line", "").split(" — ", 1)[0].lower()
                != rule.spell_type):
        return None
    return rule


@dataclass(frozen=True)
class DrawSpellOutcome:
    name: str
    source_stack_id: int
    source_graveyard_id: int
    mana_source_ids: tuple[int, ...]
    drawn_ids: tuple[int, ...]
    limitations: tuple[str, ...]
    library_steps: tuple[dict, ...] = ()
    discarded_ids: tuple[int, ...] = ()
    surveilled_ids: tuple[int, ...] = ()
    bottomed_ids: tuple[int, ...] = ()
    returned_ids: tuple[int, ...] = ()
    created_token_ids: tuple[int, ...] = ()


def cast_and_resolve_reviewed_draw_spell(
        zones, seat, object_id, catalog, colors, mana_service, *,
        on_cast=None, select=None):
    if object_id not in zones.ids(seat, "hand"):
        raise ValueError("Source spell is not in hand")
    obj = zones.kernel.get(object_id)
    raw = catalog.get(obj.card.name)
    rule = reviewed_draw_spell(obj.card.name, raw)
    if (rule is None or obj.card.card_id != rule.oracle_id
            or obj.card.types != frozenset({rule.spell_type})):
        raise ValueError("Unreviewed spell source")
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("Authoritative physical mana service required")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("on_cast must be callable")
    if len(zones.ids(seat, "library")) < rule.draw_count:
        return None
    entry = ReviewedCreatureCast(
        rule.oracle_id, rule.mana_cost, True, rule.limitations)
    committed = cast_reviewed_spell(
        zones, seat, object_id, entry, colors,
        mana_service=mana_service, spell_type=rule.spell_type)
    if committed is None:
        return None
    if on_cast is not None:
        on_cast(committed.ticket)
    outcomes = []
    created_tokens=[]

    def effect(kernel, ticket):
        outcomes.append(resolve_library_actions(
            zones, seat, rule.library_actions(), select=select))
        if rule.token_batches:
            created_tokens.extend(create_reviewed_token_batches(
                zones,seat,rule.token_batches))

    graveyard_id = zones.resolve(committed.ticket, effect=effect)
    outcome = outcomes[0]
    return DrawSpellOutcome(
        obj.card.name, committed.ticket.object_id, graveyard_id,
        tuple(committed.paid_source_ids), outcome.drawn_ids, rule.limitations,
        outcome.steps, outcome.discarded_ids, outcome.milled_ids,
        outcome.bottomed_ids, outcome.returned_ids,tuple(created_tokens))
