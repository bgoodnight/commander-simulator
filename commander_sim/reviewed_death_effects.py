"""Reviewed death-event composition over existing physical kernel zone moves.

This is an explicitly bounded triggered-effect resolver: the host makes the
legal destruction/sacrifice decision and supplies a pre-event battlefield
snapshot. No invented death from Oracle prose. It handles pre-existing move
records with last-known information, distinct per-death and once-per-turn
semantics, and reviewed effect parameters. It does NOT provide stack/priority,
death replacement, prevention, APNAP ordering, or player elimination.
"""
from dataclasses import dataclass
from types import MappingProxyType

from .ability_composition import (
    AbilitySlot, AbilityHandler, ComposedCard, AbilityDispatcher)
from .kernel_life import KernelLife
from .physical_common_effects import CardQuantity, draw_physical_cards, (
    CounterPlacement), put_reviewed_counters
from .reviewed_token_spells import TokenBlueprint, create_reviewed_token_batches


@dataclass(frozen=True)
class BattlefieldFact:
    object_id: int
    name: str
    oracle_id: str
    owner: int
    controller: int
    types: frozenset[str]
    subtypes: frozenset[str]
    token: bool

    @classmethod
    def of(cls, obj):
        return cls(obj.object_id,obj.card.name,obj.card.card_id,
                   obj.owner,obj.controller,frozenset(obj.types),
                   frozenset(obj.subtypes),bool(obj.token))


def capture_battlefield(kernel):
    """Capture LKI *before* the authoritative kernel changes any objects."""
    return MappingProxyType({o.object_id:BattlefieldFact.of(o)
                             for o in kernel.on_battlefield()})


@dataclass(frozen=True)
class DeathAction:
    scope: str
    operation: str
    quantity: int = 1
    token: TokenBlueprint | None = None
    once_per_turn: bool = False

    def __post_init__(self):
        scopes={"own_nontoken_zombie","own_nontoken_creature",
                "own_zombie","any_zombie","own_creature","other_own_creature",
                "any_creature","other_any_creature","opponent_creature",
                "other_own_artifact_or_creature"}
        ops={"zombie","treasure","draw_lose","drain_gain","drain",
             "draw","counter_self","lose_controller","gain"}
        if (self.scope not in scopes or self.operation not in ops
                or type(self.quantity) is not int or self.quantity<=0
                or type(self.once_per_turn) is not bool
                or (self.operation in {"zombie","treasure"})!=(self.token is not None)):
            raise ValueError("Invalid reviewed death action")


@dataclass(frozen=True)
class DeathRule:
    oracle_id: str
    excerpt: str
    slot_id: str
    action: DeathAction

    def __post_init__(self):
        if not self.oracle_id or not self.excerpt or not self.slot_id:
            raise ValueError("Incomplete death trigger review")


_ZOMBIE=TokenBlueprint("Zombie",frozenset({"creature"}),
    frozenset({"Zombie"}),frozenset({"B"}),2,2)
_TREASURE=TokenBlueprint("Treasure",frozenset({"artifact"}),
    frozenset({"Treasure"}),frozenset(),0,0,
    limitations=("Treasure activated mana ability requires separate review",))


def _rule(oracle,excerpt,slot,scope,op,amount=1,token=None,once=False):
    return DeathRule(oracle,excerpt,slot,DeathAction(scope,op,amount,token,once))


DEATH_RULES={
    "Headless Rider":(
        _rule("d4fdacd7-3101-44e2-a880-dde7326137a4",
              "Whenever this creature or another nontoken Zombie you control dies, create a 2/2 black Zombie creature token.",
              "zombie_death","own_nontoken_zombie","zombie",token=_ZOMBIE),),
    "Open the Graves":(
        _rule("28778958-a1f9-4fea-b551-c193d1257f18",
              "Whenever a nontoken creature you control dies, create a 2/2 black Zombie creature token.",
              "creature_death","own_nontoken_creature","zombie",token=_ZOMBIE),),
    "Undead Augur":(
        _rule("c26887e1-27f4-4550-921b-53460e43c079",
              "Whenever this creature or another Zombie you control dies, you draw a card and lose 1 life.",
              "zombie_death","own_zombie","draw_lose"),),
    "Vengeful Dead":(
        _rule("277c8ee9-0157-4e45-96ad-1b67716955ee",
              "Whenever this creature or another Zombie dies, each opponent loses 1 life.",
              "zombie_death","any_zombie","drain"),),
    "Bastion of Remembrance":(
        _rule("c7f33cea-2ec8-4081-9208-a5b1d86721b3",
              "Whenever a creature you control dies, each opponent loses 1 life and you gain 1 life.",
              "creature_death","own_creature","drain_gain"),),
    "Pitiless Plunderer":(
        _rule("a784481f-eccb-4112-bb38-04a659319660",
              "Whenever another creature you control dies, create a Treasure token.",
              "other_creature_death","other_own_creature","treasure",token=_TREASURE),),
    "Morbid Opportunist":(
        _rule("322f44f0-e6da-4ee0-b474-e7d5e9a461c5",
              "Whenever one or more other creatures die, draw a card. This ability triggers only once each turn.",
              "once_per_turn_death","other_any_creature","draw",once=True),),
    "Venomcrawler":(
        _rule("f3a07ae4-b0f8-43e6-adba-217f220cc2d0",
              "Devourer of Souls — Whenever another creature dies, put a +1/+1 counter on this creature.",
              "other_creature_death","other_any_creature","counter_self"),),
    "Yahenni, Undying Partisan":(
        _rule("fdba89eb-1cf5-46e6-9d09-1adb9bc40fcd",
              "Whenever a creature an opponent controls dies, put a +1/+1 counter on Yahenni.",
              "opponent_creature_death","opponent_creature","counter_self"),),
    "Massacre Wurm":(
        _rule("93cf50cf-0ecc-4d3e-abea-778c1ebacec4",
              "Whenever a creature an opponent controls dies, that player loses 2 life.",
              "opponent_creature_death","opponent_creature","lose_controller",2),),
    "The Meathook Massacre":(
        _rule("127de52b-df75-4342-95a0-20d84c5bf916",
              "Whenever a creature you control dies, each opponent loses 1 life.",
              "own_creature_death","own_creature","drain"),
        _rule("127de52b-df75-4342-95a0-20d84c5bf916",
              "Whenever a creature an opponent controls dies, you gain 1 life.",
              "opponent_creature_death","opponent_creature","gain")),
    "Marionette Apprentice":(
        _rule("726d9d2c-736a-4852-9938-a0f50d8fd89f",
              "Whenever another creature or artifact you control is put into a graveyard from the battlefield, each opponent loses 1 life.",
              "other_permanent_to_graveyard","other_own_artifact_or_creature","drain"),),
}


def _matches(effect,source,dead):
    scope=effect.scope
    creature="creature" in dead.types
    zombie=creature and "Zombie" in dead.subtypes
    own=source.controller==dead.controller
    other=source.object_id!=dead.object_id
    if scope=="own_nontoken_zombie":return own and zombie and not dead.token
    if scope=="own_nontoken_creature":return own and creature and not dead.token
    if scope=="own_zombie":return own and zombie
    if scope=="any_zombie":return zombie
    if scope=="own_creature":return own and creature
    if scope=="other_own_creature":return other and own and creature
    if scope=="any_creature":return creature
    if scope=="other_any_creature":return other and creature
    if scope=="opponent_creature":return not own and creature
    if scope=="other_own_artifact_or_creature":
        return other and own and bool(dead.types & {"artifact","creature"})
    raise ValueError("Unrecognized reviewed death predicate")


@dataclass(frozen=True)
class DeathResolution:
    source_id: int
    source_name: str
    dead_id: int
    ability_id: str
    operation: str
    token_ids: tuple[int,...] = ()
    drawn_ids: tuple[int,...] = ()


class ReviewedDeathEngine:
    """Consume authoritative death moves; never replay the same old object ID."""

    def __init__(self,zones,life:KernelLife,catalog):
        if life.kernel is not zones.kernel:
            raise ValueError("Life and zone state must share same kernel")
        self.zones=zones
        self.life=life
        self.catalog=catalog
        self._handled=set()
        self._once=set()
        self.invocations=[]

    def _reviewed_card(self,source):
        row=self.catalog.get(source.name)
        if row is None or row.get("oracle_id")!=source.oracle_id:
            return ()
        rules=DEATH_RULES.get(source.name,())
        return tuple(rule for rule in rules if rule.oracle_id==source.oracle_id
                     and rule.excerpt in row.get("oracle_text",""))

    def resolve_deaths(self,before,*,move_index,turn):
        """Handle the death moves of one already-applied physical batch.

        LKI must be captured before the moves. Trigger timing/APNAP is still a
        higher-level host responsibility. Fails closed on missing draw capacity,
        unknown dead object IDs, or incomplete event snapshots.
        """
        if not isinstance(before,MappingProxyType):
            raise TypeError("Pre-event LKI must come from capture_battlefield")
        if (type(move_index) is not int or not 0<=move_index<=len(self.zones.kernel.moves)
                or type(turn) is not int or turn<1):
            raise ValueError("Invalid physical death event boundary")
        changes=[m for m in self.zones.kernel.moves[move_index:]
                 if m.old_zone=="battlefield" and m.new_zone=="graveyard"
                 and m.reason in {"sacrifice","destroy","state_based"}
                 and m.object_id not in self._handled]
        for m in changes:
            if m.object_id not in before:
                raise ValueError("A dead object was missing from its LKI snapshot")
        agenda=[]
        pending_once=set()
        for source in before.values():
            for rule in self._reviewed_card(source):
                for move in changes:
                    dead=before[move.object_id]
                    action=rule.action
                    if not _matches(action,source,dead):
                        continue
                    once_key=(turn,source.object_id,rule.slot_id)
                    if action.once_per_turn and (
                        once_key in self._once or once_key in pending_once):
                        continue
                    if action.once_per_turn:pending_once.add(once_key)
                    agenda.append((source,dead,rule))
        draws={}
        for source,_,rule in agenda:
            if rule.action.operation in {"draw","draw_lose"}:
                seat=source.controller
                draws[seat]=draws.get(seat,0)+rule.action.quantity
        if any(len(self.zones.ids(seat,"library"))<need
               for seat,need in draws.items()):
            raise NotImplementedError(
                "Full empty-library draw loss and APNAP ordering are not yet modeled")
        resolved=[]
        for source,dead,rule in agenda:
            action=rule.action
            slot=AbilitySlot(source.oracle_id,"front",rule.slot_id,"triggered",
                             action,rule.excerpt,"pinned-oracle-m1",
                             frozenset({"physical_death","last_known_source"}))
            ability=ComposedCard(
                source.oracle_id,self.catalog[source.name]["oracle_text"],
                (slot,),(AbilityHandler(slot.key,"exact",action,slot.source_revision,
                frozenset({"physical_death","last_known_source"})),))
            dispatcher=AbilityDispatcher(
                ability,"strict",frozenset({"physical_death","last_known_source"}))
            def apply(operation):
                controller=source.controller
                token_ids=()
                drawn_ids=()
                count=operation.quantity
                if operation.operation in {"zombie","treasure"}:
                    token_ids=create_reviewed_token_batches(
                        self.zones,controller,(operation.token,))
                elif operation.operation in {"draw","draw_lose"}:
                    outcome=draw_physical_cards(
                        self.zones,controller,CardQuantity(count))
                    if not outcome.complete:
                        raise AssertionError("Death-trigger draw preview changed")
                    drawn_ids=outcome.drawn_ids
                    if operation.operation=="draw_lose":
                        self.life.lose(controller,count,source.object_id)
                elif operation.operation in {"drain","drain_gain"}:
                    self.life.each_opponent_loses(controller,count,source.object_id)
                    if operation.operation=="drain_gain":
                        self.life.gain(controller,count,source.object_id)
                elif operation.operation=="gain":
                    self.life.gain(controller,count,source.object_id)
                elif operation.operation=="lose_controller":
                    self.life.lose(dead.controller,count,source.object_id)
                elif operation.operation=="counter_self":
                    live=self.zones.kernel.objects.get(source.object_id)
                    if live is not None and live.zone=="battlefield":
                        put_reviewed_counters(
                            self.zones.kernel,controller,source.object_id,
                            CounterPlacement("+1/+1",count))
                else:
                    raise NotImplementedError("Unreviewed death suboperation")
                return tuple(token_ids),tuple(drawn_ids)
            created,drawn=dispatcher.invoke(rule.slot_id,source.object_id,apply)
            self.invocations.extend(dispatcher.events)
            resolved.append(DeathResolution(
                source.object_id,source.name,dead.object_id,rule.slot_id,
                action.operation,created,drawn))
        self._handled.update(m.object_id for m in changes)
        self._once.update(pending_once)
        return tuple(resolved)
