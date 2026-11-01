"""Reviewed upkeep/end-step abilities over one physical Commander kernel.

The host explicitly supplies the phase boundary, active seat, round identity
and choices. No turn advancement, APNAP ordering, opponent responses, priority,
player elimination or ability inference from printed Oracle prose.
"""
from dataclasses import dataclass, replace

from .ability_composition import (
    AbilitySlot,AbilityHandler,ComposedCard,AbilityDispatcher)
from .kernel_life import KernelLife
from .physical_common_effects import (
    CardQuantity,draw_physical_cards,GraveyardToHand,
    retrieve_reviewed_graveyard_card)
from .reviewed_token_spells import TokenBlueprint,create_reviewed_token_batches


_ZOMBIE=TokenBlueprint("Zombie",frozenset({"creature"}),
    frozenset({"Zombie"}),frozenset({"B"}),2,2)
_SNAKE=TokenBlueprint("Snake",frozenset({"creature"}),
    frozenset({"Snake"}),frozenset({"B"}),1,1,
    keywords=frozenset({"deathtouch"}))
_DECAYED_ZOMBIE=TokenBlueprint("Zombie",frozenset({"creature"}),
    frozenset({"Zombie"}),frozenset({"B"}),2,2,
    limitations=("Full decayed combat sacrifice and blocking rule unavailable",),
    keywords=frozenset({"decayed"}))
_PLAGUEBEARER=TokenBlueprint(
    "Plaguebearer of Nurgle",frozenset({"creature"}),
    frozenset({"Demon"}),frozenset({"B"}),1,3)


@dataclass(frozen=True)
class PhaseRule:
    oracle_id: str
    excerpt: str
    phase: str
    slot_id: str
    operation: str
    every_player: bool = False

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt or not self.slot_id
                or self.phase not in {"upkeep","end_step"}
                or self.operation not in {
                    "draw_lose_one","zombies_half","zombie_draw_lose",
                    "snake_if_none","decayed_zombie_if_none",
                    "opponent_loss_plaguebearers","death_draw_lose",
                    "graveyard_creature_to_hand"}):
            raise ValueError("Invalid reviewed phase trigger")


def _rule(oid,excerpt,phase,op,*,each=False):
    return PhaseRule(oid,excerpt,phase,op,op,each)


PHASE_RULES={
    "Phyrexian Arena":(_rule("ee579a32-a048-4335-b966-231ba731cdea",
        "At the beginning of your upkeep, you draw a card and lose 1 life.",
        "upkeep","draw_lose_one"),),
    "Endless Ranks of the Dead":(_rule("69d4ecac-4735-4667-bfc1-c8800b436d08",
        "At the beginning of your upkeep, create X 2/2 black Zombie creature tokens, where X is half the number of Zombies you control, rounded down.",
        "upkeep","zombies_half"),),
    "Graveborn Muse":(_rule("d2a65ff4-ab82-42f7-9d90-feb29132121e",
        "At the beginning of your upkeep, you draw X cards and lose X life, where X is the number of Zombies you control.",
        "upkeep","zombie_draw_lose"),),
    "Ophiomancer":(_rule("55eca80c-dcd8-4c2f-aa0f-fb0aec7b80f7",
        "At the beginning of each upkeep, if you control no Snakes, create a 1/1 black Snake creature token with deathtouch.",
        "upkeep","snake_if_none",each=True),),
    "Jadar, Ghoulcaller of Nephalia":(_rule(
        "fb3defc0-c93a-4423-9ff9-c399f8a8ef1f",
        "At the beginning of your end step, if you control no creatures with decayed, create a 2/2 black Zombie creature token with decayed.",
        "end_step","decayed_zombie_if_none"),),
    "Great Unclean One":(_rule("cd9031e4-9f6f-4dd8-908e-dcf7b79438e5",
        "Reverberating Summons — At the beginning of your end step, each opponent loses 2 life. Then for each opponent who has less life than you, create a 1/3 black Demon creature token named Plaguebearer of Nurgle.",
        "end_step","opponent_loss_plaguebearers"),),
    "Tallyman of Nurgle":(_rule("7cc4a635-8730-4018-a8fd-b29fb5479928",
        "The Seven-fold Chant — At the beginning of your end step, if a creature died this turn, you draw a card and you lose 1 life. If seven or more creatures died this turn, instead you draw seven cards and you lose 7 life.",
        "end_step","death_draw_lose"),),
    "Oversold Cemetery":(_rule("ed4cd3a1-688b-4c05-948d-39d3336e00c0",
        "At the beginning of your upkeep, if you have four or more creature cards in your graveyard, you may return target creature card from your graveyard to your hand.",
        "upkeep","graveyard_creature_to_hand"),),
}


@dataclass(frozen=True)
class PhaseResolution:
    source_id: int
    source_name: str
    slot_id: str
    operation: str
    created_token_ids: tuple[int,...] = ()
    drawn_ids: tuple[int,...] = ()
    returned_id: int | None = None


class ReviewedPhaseEngine:
    """Idempotent execution for externally authorized phase events."""
    def __init__(self,zones,life:KernelLife,catalog):
        if life.kernel is not zones.kernel:
            raise ValueError("Life and zones must share an authoritative kernel")
        self.zones=zones
        self.life=life
        self.catalog=catalog
        self._handled=set()
        self.invocations=[]

    def resolve(self,*,phase,active_seat,round_id,death_count=0,choices=None):
        if (phase not in {"upkeep","end_step"} or type(active_seat) is not int
                or active_seat not in self.life.kernel.life_totals
                or type(round_id) is not int or round_id<1
                or type(death_count) is not int or death_count<0):
            raise ValueError("Invalid reviewed phase boundary")
        decisions={} if choices is None else choices
        if not isinstance(decisions,dict):
            raise TypeError("Phase choices require source ID keyed mapping")
        kernel=self.zones.kernel
        planned=[]
        for source in sorted(kernel.on_battlefield(),key=lambda x:x.object_id):
            row=self.catalog.get(source.card.name)
            if row is None or row.get("oracle_id")!=source.card.card_id:
                continue
            for rule in PHASE_RULES.get(source.card.name,()):
                if (rule.oracle_id!=source.card.card_id
                        or rule.excerpt not in row.get("oracle_text","")
                        or rule.phase!=phase
                        or not (rule.every_player or source.controller==active_seat)):
                    continue
                key=(round_id,active_seat,phase,source.object_id,rule.slot_id)
                if key in self._handled:continue
                planned.append((source,rule,key))
        # No early mutation if this bounded no-loss-SBA environment cannot
        # fulfill a mandatory draw. Optional returns require explicit choice.
        required_draws={}
        for source,rule,_ in planned:
            controller=source.controller
            if rule.operation=="draw_lose_one":n=1
            elif rule.operation=="zombie_draw_lose":
                n=self._creature_count(controller,"Zombie")
            elif rule.operation=="death_draw_lose":
                n=7 if death_count>=7 else 1 if death_count>0 else 0
            else:n=0
            required_draws[controller]=required_draws.get(controller,0)+n
        if any(len(self.zones.ids(seat,"library"))<n
               for seat,n in required_draws.items()):
            raise NotImplementedError("Empty-library draw loss requires full game host")
        outcomes=[]
        for source,rule,key in planned:
            slot=AbilitySlot(source.card.card_id,"front",rule.slot_id,
                 "triggered",rule,rule.excerpt,"pinned-oracle-m1",
                 frozenset({"phase_event","physical_zones"}))
            card=ComposedCard(source.card.card_id,
                 self.catalog[source.card.name]["oracle_text"],(slot,),
                 (AbilityHandler(slot.key,"exact",rule,slot.source_revision,
                 frozenset({"phase_event","physical_zones"})),))
            dispatcher=AbilityDispatcher(card,"strict",
                 frozenset({"phase_event","physical_zones"}))
            def execute(operation):
                seat=source.controller
                tokens=()
                drawn=()
                returned=None
                if operation.operation in {"draw_lose_one","zombie_draw_lose",
                                         "death_draw_lose"}:
                    n=(1 if operation.operation=="draw_lose_one" else
                       self._creature_count(seat,"Zombie")
                       if operation.operation=="zombie_draw_lose" else
                       7 if death_count>=7 else 1 if death_count else 0)
                    if n:
                        outcome=draw_physical_cards(self.zones,seat,CardQuantity(n))
                        if not outcome.complete:
                            raise AssertionError("Draw preview changed during phase")
                        drawn=outcome.drawn_ids
                        self.life.lose(seat,n,source.object_id)
                elif operation.operation=="zombies_half":
                    n=self._creature_count(seat,"Zombie")//2
                    if n:
                        tokens=create_reviewed_token_batches(
                            self.zones,seat,(replace(_ZOMBIE,count=n),))
                elif operation.operation=="snake_if_none":
                    if not self._creature_count(seat,"Snake"):
                        tokens=create_reviewed_token_batches(
                            self.zones,seat,(_SNAKE,))
                elif operation.operation=="decayed_zombie_if_none":
                    if not any("creature" in obj.types and "decayed" in obj.keywords
                               for obj in kernel.controlled(seat)):
                        tokens=create_reviewed_token_batches(
                            self.zones,seat,(_DECAYED_ZOMBIE,))
                elif operation.operation=="opponent_loss_plaguebearers":
                    self.life.each_opponent_loses(seat,2,source.object_id)
                    count=sum(1 for opponent in self.life.kernel.life_totals
                        if opponent!=seat and self.life.total(opponent)<self.life.total(seat))
                    if count:
                        tokens=create_reviewed_token_batches(
                            self.zones,seat,(replace(_PLAGUEBEARER,count=count),))
                elif operation.operation=="graveyard_creature_to_hand":
                    creature_ids=tuple(oid for oid in self.zones.ids(seat,"graveyard")
                        if "creature" in kernel.get(oid).types)
                    if len(creature_ids)>=4:
                        selected=decisions.get(source.object_id)
                        if selected is not None:
                            if selected not in creature_ids:
                                raise ValueError("Unreviewed Cemetery graveyard choice")
                            returned=retrieve_reviewed_graveyard_card(
                                self.zones,seat,selected,
                                GraveyardToHand(frozenset({"creature"})))
                else:
                    raise NotImplementedError("Unregistered phase effect")
                return tuple(tokens),tuple(drawn),returned
            tokens,drawn,returned=dispatcher.invoke(rule.slot_id,source.object_id,execute)
            self.invocations.extend(dispatcher.events)
            self._handled.add(key)
            outcomes.append(PhaseResolution(source.object_id,source.card.name,
                rule.slot_id,rule.operation,tokens,drawn,returned))
        return tuple(outcomes)

    def _creature_count(self,seat,subtype):
        return sum("creature" in obj.types
            and subtype in self.zones.kernel.subtypes(obj.object_id)
            for obj in self.zones.kernel.controlled(seat))
