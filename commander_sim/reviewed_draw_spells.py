"""Reviewed, reusable source-paid draw operations on the existing physical zones.

Printed identities are exact-pinned; a card is never admitted by text parsing
or role alone. Omitted filtering/scry/flashback is independently reported.
"""
from dataclasses import dataclass
from .generic_cast import ReviewedCreatureCast,cast_reviewed_spell
from .physical_common_effects import CardQuantity,draw_physical_cards

@dataclass(frozen=True)
class DrawSpellReview:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    spell_type: str
    draw_count: int
    limitations: tuple[str,...] = ()
    def __post_init__(self):
        if not self.oracle_id or not self.oracle_text or not self.mana_cost:
            raise ValueError("Missing reviewed source identity")
        if self.spell_type not in ("instant","sorcery") or type(self.draw_count) is not int or self.draw_count<1:
            raise ValueError("Invalid reusable draw-spell template")

# Existing physical draw primitive, new declarative card parameters.
# Ponder/Preordain use an explicitly simplified draw-only fallback.
DRAW_SPELLS={
    "Quick Study":DrawSpellReview(
        "7bff8d4a-1c7d-48b8-b3e3-737dd6f01823",
        "Draw two cards.","{2}{U}","instant",2),
    "Think Twice":DrawSpellReview(
        "fa85c5a2-8e83-4624-a35a-a0bbf17ecbb4",
        "Draw a card.\nFlashback {2}{U} (You may cast this card from your graveyard for its flashback cost. Then exile it.)",
        "{1}{U}","instant",1,("Flashback permission and alternate-cost cast not modeled",)),
    "Ponder":DrawSpellReview(
        "02090581-61aa-4348-ad57-451be8ee91c2",
        "Look at the top three cards of your library, then put them back in any order. You may shuffle.\nDraw a card.",
        "{U}","sorcery",1,("Top-three selection/reordering and optional shuffle omitted",)),
    "Preordain":DrawSpellReview(
        "ac641490-ca14-48d7-8cc4-b69ce984befa",
        "Scry 2, then draw a card. (To scry 2, look at the top two cards of your library, then put any number of them on the bottom and the rest on top in any order.)",
        "{U}","sorcery",1,("Scry two choices omitted; only printed draw is resolved",)),
}

def reviewed_draw_spell(name,card):
    rule=DRAW_SPELLS.get(name)
    if (rule is None or not isinstance(card,dict)
            or card.get("layout")!="normal"
            or card.get("oracle_id")!=rule.oracle_id
            or card.get("oracle_text")!=rule.oracle_text
            or card.get("mana_cost")!=rule.mana_cost
            or card.get("type_line","").split(" — ",1)[0].lower()!=rule.spell_type):
        return None
    return rule

@dataclass(frozen=True)
class DrawSpellOutcome:
    name: str
    source_stack_id: int
    source_graveyard_id: int
    mana_source_ids: tuple[int,...]
    drawn_ids: tuple[int,...]
    limitations: tuple[str,...]

def cast_and_resolve_reviewed_draw_spell(zones,seat,object_id,catalog,colors,mana_service,*,on_cast=None):
    if object_id not in zones.ids(seat,"hand"):
        raise ValueError("Source spell is not in hand")
    obj=zones.kernel.get(object_id)
    raw=catalog.get(obj.card.name)
    rule=reviewed_draw_spell(obj.card.name,raw)
    if rule is None or obj.card.card_id!=rule.oracle_id or obj.card.types!=frozenset({rule.spell_type}):
        raise ValueError("Unreviewed spell source")
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("Authoritative physical mana service required")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("on_cast must be callable")
    if len(zones.ids(seat,"library"))<rule.draw_count:
        return None
    entry=ReviewedCreatureCast(rule.oracle_id,rule.mana_cost,True,rule.limitations)
    committed=cast_reviewed_spell(zones,seat,object_id,entry,colors,
                                  mana_service=mana_service,spell_type=rule.spell_type)
    if committed is None:
        return None
    if on_cast is not None:on_cast(committed.ticket)
    drawn=[]
    def effect(kernel,ticket):
        outcome=draw_physical_cards(zones,seat,CardQuantity(rule.draw_count))
        if not outcome.complete:raise AssertionError("Reviewed draw library shortfall")
        drawn.extend(outcome.drawn_ids)
    graveyard_id=zones.resolve(committed.ticket,effect=effect)
    return DrawSpellOutcome(obj.card.name,committed.ticket.object_id,
                            graveyard_id,tuple(committed.paid_source_ids),
                            tuple(drawn),rule.limitations)
