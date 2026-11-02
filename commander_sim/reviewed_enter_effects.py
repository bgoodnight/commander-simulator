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
from .physical_common_effects import TemporaryCreatureChange, change_reviewed_creature_stats
from .library_actions import LibraryAction, resolve_library_actions
from .graveyard_recipes import (GraveyardRecipe,resolve_graveyard_recipe,
                                select_bounded_graveyard_batch)


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
    amount: int = 0
    library_actions: tuple[LibraryAction,...] = ()
    life_gain: int = 0
    reanimate: GraveyardRecipe | None = None
    total_mana_value_max: int = 0

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt
                or self.operation not in {
                    "necron_two","zombie_two","soldier_one",
                    "draw_lose_two","optional_exile_nonland",
                    "each_player_sacrifice","fabricate_one",
                    "debuff_opponent_creatures","library_recipe",
                    "mill_then_reanimate"}
                or type(self.amount) is not int or self.amount<0
                or type(self.life_gain) is not int or self.life_gain<0
                or not isinstance(self.library_actions,tuple)
                or not all(isinstance(x,LibraryAction) for x in self.library_actions)
                or (self.operation in {"library_recipe","mill_then_reanimate"})
                    !=bool(self.library_actions)
                or self.life_gain and self.operation!="library_recipe"
                or type(self.total_mana_value_max) is not int
                or self.total_mana_value_max<0
                or (self.operation=="mill_then_reanimate")
                    !=(self.reanimate is not None)
                or (self.reanimate is not None and
                    (not isinstance(self.reanimate,GraveyardRecipe)
                     or self.reanimate.destination!="battlefield"
                     or not self.total_mana_value_max))):

            raise ValueError("Invalid reviewed enter trigger")


ENTER_RULES={
    "Lord of Change":EnterRule(
        "f26fbd53-3c26-4b0a-9182-fc50dd35d0db",
        "Architect of Deception — When this creature enters, draw three cards.",
        "library_recipe",library_actions=(LibraryAction("draw",3),)),
    "Technomancer":EnterRule(
        "3f97541e-34f3-4f7f-8ac2-7167b2ec9b33",
        "When this creature enters, mill three cards, then return any number of artifact creature cards with total mana value 6 or less from your graveyard to the battlefield.",
        "mill_then_reanimate",
        library_actions=(LibraryAction("mill",3),),
        reanimate=GraveyardRecipe(
            "battlefield","own",frozenset({"creature"}),
            required_types_all=frozenset({"artifact","creature"})),
        total_mana_value_max=6),
    "Flayed One":EnterRule(
        "899415fd-4164-42a5-a0c7-eef1967c5ec5",
        "Flesh Flayer — When this creature enters, mill three cards.",
        "library_recipe",library_actions=(LibraryAction("mill",3),)),
    "Undead Butler":EnterRule(
        "426fa8e8-b0f9-4b6c-b22b-04ec2073187a",
        "When this creature enters, mill three cards.",
        "library_recipe",library_actions=(LibraryAction("mill",3),)),
    "Mire Triton":EnterRule(
        "4fe6f784-0290-4d4a-85ae-0b66522d31e9",
        "When this creature enters, mill two cards and you gain 2 life.",
        "library_recipe",library_actions=(LibraryAction("mill",2),),life_gain=2),
    "Massacre Wurm":EnterRule("93cf50cf-0ecc-4d3e-abea-778c1ebacec4",
        "When this creature enters, creatures your opponents control get -2/-2 until end of turn.",
        "debuff_opponent_creatures",amount=2),
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
    milled_ids: tuple[int,...] = ()
    library_steps: tuple[dict,...] = ()
    reanimated_ids: tuple[int,...] = ()


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
                or "land" in other.types
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
        milled=()
        library_steps=()
        reanimated=()
        if effect.operation=="mill_then_reanimate":
            result=resolve_library_actions(
                zones,source.controller,effect.library_actions)
            milled=result.milled_ids
            library_steps=result.steps
            eligible=select_bounded_graveyard_batch(
                zones,source.controller,effect.reanimate,catalog,
                max_total_mana_value=effect.total_mana_value_max)
            restored=resolve_graveyard_recipe(
                zones,source.controller,eligible,effect.reanimate)
            reanimated=tuple(move.new_id for move in restored)
        elif effect.operation=="library_recipe":
            result=resolve_library_actions(zones,source.controller,
                                           effect.library_actions)
            milled=result.milled_ids
            library_steps=result.steps
            if effect.life_gain:
                life.gain(source.controller,effect.life_gain,source_id)
        elif effect.operation in {"necron_two","zombie_two","soldier_one"}:
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
        elif effect.operation=="debuff_opponent_creatures":
            eligible=tuple(o.object_id for o in kernel.on_battlefield()
                           if o.controller!=source.controller
                           and "creature" in o.types)
            change_reviewed_creature_stats(
                zones,eligible,TemporaryCreatureChange(
                    -effect.amount,-effect.amount),
                death_engine=death_engine,turn=turn)
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
        return (tokens,tuple(drawn),exiled,sacrificed,tuple(milled),
                tuple(library_steps),tuple(reanimated))
    created,drawn,exiled,sacrificed,milled,steps,reanimated=dispatcher.invoke(
        slot.slot_id,source_id,apply)
    return EnterResult(source_id,source.card.name,move.old_zone,
                       rule.operation,tuple(created),tuple(drawn),
                       exiled,tuple(sacrificed),milled,steps,reanimated)
