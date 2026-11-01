"""Reviewed entry-trigger effects shared by Necrons, Gisa and Mortarion.

The caller commits a real zone move *first*. This resolver verifies the
physical battlefield object and its immediately preceding zone transition,
then composes approved effects without manufacturing an ETB or bypassing
printed choices. It is a no-priority suboperation, not a full triggered stack.
"""
from dataclasses import dataclass

from .ability_composition import (
    AbilitySlot,AbilityHandler,ComposedCard,AbilityDispatcher)
from .kernel_life import KernelLife
from .physical_common_effects import (
    CardQuantity,draw_physical_cards,CounterPlacement,put_reviewed_counters,
    TargetedPermanentRemoval,remove_reviewed_permanent)
from .reviewed_token_spells import TokenBlueprint,create_reviewed_token_batches
from .reviewed_death_effects import capture_battlefield


_NECRON=TokenBlueprint("Necron Warrior",
    frozenset({"artifact","creature"}),frozenset({"Necron","Warrior"}),
    frozenset({"B"}),2,2,2,True)
_ZOMBIE=TokenBlueprint("Zombie",frozenset({"creature"}),
    frozenset({"Zombie"}),frozenset({"B"}),2,2,2)
_SOLDIER=TokenBlueprint("Soldier",frozenset({"creature"}),
    frozenset({"Human","Soldier"}),frozenset({"W"}),1,1)
_SERVO=TokenBlueprint("Servo",frozenset({"artifact","creature"}),
    frozenset({"Servo"}),frozenset(),1,1)


@dataclass(frozen=True)
class EnterRule:
    oracle_id: str
    excerpt: str
    operation: str
    only_from_graveyard: bool = False

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt
                or self.operation not in {
                    "necron_two","zombie_two","soldier_one",
                    "draw_lose_two","optional_exile_nonland",
                    "each_player_sacrifice","fabricate_one"}):
            raise ValueError("Invalid reviewed enter trigger")


ENTER_RULES={
    "Royal Warden":EnterRule("0192ba05-6144-4fec-a803-462ecdf64195",
        "Phalanx Commander — When this creature enters, create two tapped 2/2 black Necron Warrior artifact creature tokens.",
        "necron_two"),
    "Triarch Praetorian":EnterRule("52aa5a79-db0e-4eaa-b2df-e41674c47794",
        "Dynastic Codes — When this creature enters from a graveyard, you draw two cards and you lose 2 life.",
        "draw_lose_two",True),
    "Canoptek Tomb Sentinel":EnterRule("678b3fb5-aa9f-4268-9433-2a89dd37b927",
        "Exile Cannon — When this creature enters from a graveyard, exile up to one target nonland permanent.",
        "optional_exile_nonland",True),
    "Lokhust Heavy Destroyer":EnterRule("fd03f20a-d365-48fb-8b2a-ad4b502a0045",
        "Enmitic Exterminator — When this creature enters, each player sacrifices a creature of their choice.",
        "each_player_sacrifice"),
    "Bastion of Remembrance":EnterRule("c7f33cea-2ec8-4081-9208-a5b1d86721b3",
        "When this enchantment enters, create a 1/1 white Human Soldier creature token.",
        "soldier_one"),
    "Grave Titan":EnterRule("f3abd4d1-a975-4e85-8684-aa0fce029670",
        "Whenever this creature enters or attacks, create two 2/2 black Zombie creature tokens.",
        "zombie_two"),
    "Marionette Apprentice":EnterRule("726d9d2c-736a-4852-9938-a0f50d8fd89f",
        "Fabricate 1 (When this creature enters, put a +1/+1 counter on it or create a 1/1 colorless Servo artifact creature token.)",
        "fabricate_one"),
}


@dataclass(frozen=True)
class EnterResult:
    source_id: int
    source_name: str
    previous_zone: str
    operation: str
    token_ids: tuple[int,...] = ()
    drawn_ids: tuple[int,...] = ()
    exiled_id: int | None = None
    sacrificed_ids: tuple[int,...] = ()


def reviewed_enter_rule(name,raw):
    rule=ENTER_RULES.get(name)
    if (rule is None or raw is None or raw.get("oracle_id")!=rule.oracle_id
            or rule.excerpt not in raw.get("oracle_text","")):
        return None
    return rule


def execute_reviewed_enter(zones,life:KernelLife,source_id,catalog,*,
                            choice=None,death_engine=None,turn=1):
    """Resolve a single physical ETB using one pinned typed operation.

    choice for optional exile is a target ID or None.
    choice for fabricate is 'counter' or 'servo'.
    choice for each-player sacrifice is an explicit seat->creature ID map.
    """
    kernel=zones.kernel
    source=kernel.objects.get(source_id)
    if source is None or source.zone!="battlefield":
        raise ValueError("Entry source must be a live battlefield permanent")
    raw=catalog.get(source.card.name)
    rule=reviewed_enter_rule(source.card.name,raw)
    if rule is None or source.card.card_id!=rule.oracle_id:
        raise ValueError("Unreviewed entered ability source")
    move=next((m for m in reversed(kernel.moves)
               if m.new_object_id==source_id and m.new_zone=="battlefield"),None)
    if move is None or move.old_zone not in {"stack","graveyard","exile","hand"}:
        raise ValueError("No verified physical entry transition")
    if rule.only_from_graveyard and move.old_zone!="graveyard":
        return None
    if life.kernel is not kernel:
        raise ValueError("Life host is not authoritative kernel")
    if rule.operation=="fabricate_one" and choice not in {"counter","servo"}:
        raise ValueError("Mandatory fabricate choice not provided")
    if rule.operation=="optional_exile_nonland" and choice is not None:
        other=kernel.objects.get(choice)
        if (other is None or other.zone!="battlefield"
                or "land" in other.types or choice==source_id
                or not kernel.legal_target(source.controller,choice,
                         frozenset({"creature","artifact","enchantment",
                                    "planeswalker","battle"}))):
            raise ValueError("Illegal optional exile target")
    if rule.operation=="draw_lose_two" and len(zones.ids(source.controller,"library"))<2:
        raise NotImplementedError("Empty-library draw loss not modeled")
    if rule.operation=="each_player_sacrifice":
        if not isinstance(choice,dict):
            raise ValueError("Host must provide all players' sacrifice choices")
        expected={}
        for seat in life.kernel.life_totals:
            controlled=tuple(o.object_id for o in kernel.controlled(seat,{"creature"}))
            if controlled:
                selected=choice.get(seat)
                if selected not in controlled:
                    raise ValueError("Missing or illegal mandatory sacrifice choice")
                expected[seat]=selected
            elif seat in choice and choice[seat] is not None:
                raise ValueError("Cannot sacrifice nonexistent controlled creature")
        if set(choice)-set(life.kernel.life_totals):
            raise ValueError("Unknown sacrifice controller")
    slot=AbilitySlot(rule.oracle_id,"front","enter_effect","triggered",
        rule,rule.excerpt,"pinned-oracle-m1",
        frozenset({"physical_entry","reviewed_choices"}))
    card=ComposedCard(rule.oracle_id,raw["oracle_text"],(slot,),
        (AbilityHandler(slot.key,"exact",rule,slot.source_revision,
                        slot.prereqs),))
    dispatcher=AbilityDispatcher(card,"strict",slot.prereqs)
    def apply(effect):
        tokens=()
        drawn=()
        exiled=None
        sacrificed=()
        if effect.operation in {"necron_two","zombie_two","soldier_one"}:
            batch={"necron_two":_NECRON,"zombie_two":_ZOMBIE,
                   "soldier_one":_SOLDIER}[effect.operation]
            tokens=create_reviewed_token_batches(
                zones,source.controller,(batch,))
        elif effect.operation=="draw_lose_two":
            answer=draw_physical_cards(zones,source.controller,CardQuantity(2))
            if not answer.complete:
                raise AssertionError("Draw feasibility changed during ETB")
            drawn=answer.drawn_ids
            life.lose(source.controller,2,source_id)
        elif effect.operation=="optional_exile_nonland":
            if choice is not None:
                moved=remove_reviewed_permanent(kernel,source.controller,
                    choice,TargetedPermanentRemoval("exile",
                        frozenset({"creature","artifact","enchantment",
                                   "planeswalker","battle"})))
                exiled=moved.new_object_id if moved is not None else None
        elif effect.operation=="fabricate_one":
            if choice=="counter":
                put_reviewed_counters(kernel,source.controller,source_id,
                    CounterPlacement("+1/+1"))
            else:
                tokens=create_reviewed_token_batches(
                    zones,source.controller,(_SERVO,))
        elif effect.operation=="each_player_sacrifice":
            before=capture_battlefield(kernel)
            start=len(kernel.moves)
            for seat in sorted(expected):
                zones.move(expected[seat],"graveyard","sacrifice")
            sacrificed=tuple(expected[seat] for seat in sorted(expected))
            if death_engine is not None:
                death_engine.resolve_deaths(before,move_index=start,turn=turn)
        else:
            raise NotImplementedError("Unknown reviewed enter effect")
        return tokens,tuple(drawn),exiled,sacrificed
    created,drawn,exiled,sacrificed=dispatcher.invoke(slot.slot_id,source_id,apply)
    return EnterResult(source_id,source.card.name,move.old_zone,
                       rule.operation,tuple(created),tuple(drawn),
                       exiled,tuple(sacrificed))
