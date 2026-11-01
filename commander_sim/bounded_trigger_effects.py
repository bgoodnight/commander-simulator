"""Reviewed spell-trigger effects for the bounded multi-deck physical runner.

A narrow deterministic no-opponent/no-priority slice: the existing kernel's
physical cast remains the event source. No role-based trigger inference,
priority windows, replacement effects, Harmonic doubling or full event bus.
"""
from dataclasses import dataclass

from .ability_composition import AbilitySlot, AbilityHandler, ComposedCard, AbilityDispatcher
from .legacy_common_ops import DrawDiscard
from .physical_common_effects import CardQuantity, draw_physical_cards
from .reviewed_token_spells import (TokenBlueprint, TOKEN_SPELLS,
                                    create_reviewed_token_batches)


_CAPABILITIES=frozenset({"reviewed_spell_cast","token_creation","draw"})


@dataclass(frozen=True)
class ReviewedCastTrigger:
    card: ComposedCard
    events: frozenset[str]

    def __post_init__(self):
        if (not self.events or not self.events <= {"spell_cast","spell_copied"}
                or len(self.card.slots)!=1 or self.card.slots[0].kind!="triggered"):
            raise ValueError("Invalid reviewed bounded trigger")


def _slot(oracle_id, oracle_text, excerpt, slot_id, operation, events, prereqs):
    reviewed=AbilitySlot(oracle_id,"front",slot_id,"triggered",operation,
                         excerpt,"pinned-oracle-m1",frozenset(prereqs))
    handler=AbilityHandler(reviewed.key,"exact",operation,
                           reviewed.source_revision,frozenset(prereqs))
    return ReviewedCastTrigger(
        ComposedCard(oracle_id,oracle_text,(reviewed,),(handler,)),
        frozenset(events))


_PYRO_TEXT="Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token."
_MAGE_TEXT="Magecraft — Whenever you cast or copy an instant or sorcery spell, draw a card."
_TALRAND_TEXT="Whenever you cast an instant or sorcery spell, create a 2/2 blue Drake creature token with flying."
_KILN_TEXT=("This creature gets +1/+0 for each artifact you control.\n"
            "Magecraft — Whenever you cast or copy an instant or sorcery spell, create a Treasure token. "
            '(It\'s an artifact with "{T}, Sacrifice this token: Add one mana of any color.")')

# The exact reviewed *parameters* differ, but every token trigger uses one
# create_reviewed_token_batches operation. Trigger conditions are declarations.
REVIEWED_CAST_TRIGGERS={
    "Young Pyromancer":(_slot(
        "5fac139a-07d3-4e6c-98e3-d98b199f7a6f",_PYRO_TEXT,_PYRO_TEXT,
        "spell_token",TokenBlueprint("Elemental",frozenset({"creature"}),
            frozenset({"Elemental"}),frozenset({"R"}),1,1),
        {"spell_cast"},{"reviewed_spell_cast","token_creation"}),),
    "Talrand, Sky Summoner":(_slot(
        "ea1eb902-a23c-44ff-9169-19baf71de238",_TALRAND_TEXT,
        _TALRAND_TEXT,"spell_token",
        TokenBlueprint("Drake",frozenset({"creature"}),
            frozenset({"Drake"}),frozenset({"U"}),2,2,
            keywords=frozenset({"flying"})),
        {"spell_cast"},{"reviewed_spell_cast","token_creation"}),),
    "Archmage Emeritus":(_slot(
        "8305d576-21d8-4ce7-8eda-a7cd9793aca5",_MAGE_TEXT,_MAGE_TEXT,
        "magecraft_draw",DrawDiscard(1),
        {"spell_cast","spell_copied"},{"reviewed_spell_cast","draw"}),),
    "Storm-Kiln Artist":(_slot(
        "a145ff8c-5812-4bcb-bd16-9839dc25121d",_KILN_TEXT,
        "Magecraft — Whenever you cast or copy an instant or sorcery spell, create a Treasure token.",
        "magecraft_treasure",TOKEN_SPELLS["Strike It Rich"].batches[0],
        {"spell_cast","spell_copied"},{"reviewed_spell_cast","token_creation"}),),
}


@dataclass(frozen=True)
class CastTriggerOutcome:
    source_id: int
    card_name: str
    slot_id: str
    fidelity: str
    created_token_ids: tuple[int,...] = ()
    drawn_ids: tuple[int,...] = ()


def resolve_reviewed_spell_triggers(zones, seat, catalog, *,
                                    event="spell_cast", spell_types=frozenset({"sorcery"})):
    """Resolve approved cast/copy triggers against existing battlefield IDs.

    The enclosing host must have already legally committed a physical spell
    or verified copy. It owns costs, timing, and the true event identity.
    Triggers are executed without opposing responses in this bounded pilot.
    """
    if event not in {"spell_cast","spell_copied"}:
        raise ValueError("Unreviewed event for bounded trigger resolver")
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid controller")
    if not isinstance(spell_types,frozenset):
        raise TypeError("Expected verified spell type set")
    if not spell_types & {"instant","sorcery"}:
        return ()
    outcomes=[]
    invoked=set()
    for obj in sorted(zones.kernel.objects.values(),key=lambda o:o.object_id):
        if obj.zone!="battlefield" or obj.controller!=seat:
            continue
        candidate=REVIEWED_CAST_TRIGGERS.get(obj.card.name,())
        raw=catalog.get(obj.card.name)
        for spec in candidate:
            card=spec.card
            if (event not in spec.events
                    or raw is None or raw.get("oracle_id")!=card.oracle_id
                    or raw.get("oracle_text")!=card.oracle_text
                    or obj.card.card_id!=card.oracle_id):
                continue
            slot=card.slots[0]
            identity=(obj.object_id,slot.key,event)
            if identity in invoked:
                continue
            invoked.add(identity)
            dispatcher=AbilityDispatcher(card,"strict",_CAPABILITIES)
            def commit(operation):
                if isinstance(operation,TokenBlueprint):
                    return create_reviewed_token_batches(zones,seat,(operation,)),()
                if isinstance(operation,DrawDiscard) and not operation.discard:
                    result=draw_physical_cards(zones,seat,CardQuantity(operation.draw))
                    if not result.complete:
                        raise ValueError("Draw into empty library needs full loss/SBA host")
                    return (),result.drawn_ids
                raise NotImplementedError("Unregistered bounded cast-trigger operation")
            created,drawn=dispatcher.invoke(slot.slot_id,obj.object_id,commit)
            outcomes.append(CastTriggerOutcome(
                obj.object_id,obj.card.name,slot.slot_id,
                dispatcher.events[-1].fidelity,tuple(created),tuple(drawn)))
    return tuple(outcomes)
