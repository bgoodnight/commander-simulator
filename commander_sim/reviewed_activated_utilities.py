"""Typed reusable activated abilities: life, counters, milling, temporary grants.

No individual card gets a bespoke battlefield model. Each source registers
a cost/target/operation recipe, verified against pinned Oracle text.
"""
from dataclasses import dataclass
from .reviewed_death_effects import capture_battlefield
from .physical_common_effects import (
    CounterPlacement,put_reviewed_counters,CardQuantity,mill_physical_cards)


@dataclass(frozen=True)
class ActiveRule:
    oracle_id:str
    excerpt:str
    cost:str=""
    life_cost:int=0
    tap:bool=False
    sacrifice_other:bool=False
    operation:str="counter_target"
    keyword:str=""
    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt or
                type(self.life_cost) is not int or self.life_cost<0 or
                self.operation not in {"counter_target",
                                       "keyword_own_until_end",
                                       "keyword_self_until_end",
                                       "mill_all"}):
            raise ValueError("Invalid reusable activated operation")


RULES={
    "Unspeakable Symbol":ActiveRule(
        "a5690d5f-633c-4a1e-afba-5fd79dcbf20e",
        "Pay 3 life: Put a +1/+1 counter on target creature.",
        life_cost=3,operation="counter_target"),
    "Vito, Thorn of the Dusk Rose":ActiveRule(
        "7336a541-3ae9-4ab2-acb8-f574c0a5b3a9",
        "{3}{B}{B}: Creatures you control gain lifelink until end of turn.",
        cost="{3}{B}{B}",operation="keyword_own_until_end",keyword="lifelink"),
    "Yahenni, Undying Partisan":ActiveRule(
        "fdba89eb-1cf5-46e6-9d09-1adb9bc40fcd",
        "Sacrifice another creature: Yahenni gains indestructible until end of turn.",
        sacrifice_other=True,operation="keyword_self_until_end",
        keyword="indestructible"),
    "Syr Konrad, the Grim":ActiveRule(
        "14c3ff84-1e82-4606-a433-869fc52cc382",
        "{1}{B}: Each player mills a card.",
        cost="{1}{B}",operation="mill_all")
}


def reviewed_activation(name,raw):
    rule=RULES.get(name)
    return rule if (rule is not None and isinstance(raw,dict)
                    and raw.get("oracle_id")==rule.oracle_id
                    and rule.excerpt in raw.get("oracle_text","")) else None


@dataclass(frozen=True)
class ActiveOutcome:
    source_id:int
    operation:str
    affected_ids:tuple[int,...]=()
    paid_source_ids:tuple[int,...]=()
    life_paid:int=0


def activate_reviewed(zones,life,mana,death_engine,catalog,source_id, *,
                      target_id=None,sacrifice_id=None,turn=1,
                      legal_window=True):
    from simulator.v7_rules.rules import Modifier
    kernel=zones.kernel
    source=kernel.objects.get(source_id)
    if source is None or source.zone!="battlefield" or not legal_window:
        return None
    rule=reviewed_activation(source.card.name,catalog.get(source.card.name))
    if rule is None or rule.oracle_id!=source.card.card_id:
        raise ValueError("Unreviewed activated source")
    if source.tapped and rule.tap:
        return None
    if life.total(source.controller)<=rule.life_cost:
        return None
    target=None
    if rule.operation=="counter_target":
        target=kernel.objects.get(target_id)
        if (target is None or target.zone!="battlefield"
                or not kernel.legal_target(source.controller,target_id,
                                           frozenset({"creature"}))):
            return None
    elif target_id is not None:
        raise ValueError("Operation has no target")
    sacrifice=None
    if rule.sacrifice_other:
        sacrifice=kernel.objects.get(sacrifice_id)
        if (sacrifice is None or sacrifice.object_id==source_id or
                sacrifice.zone!="battlefield" or
                sacrifice.controller!=source.controller or
                "creature" not in sacrifice.types):
            return None
    elif sacrifice_id is not None:
        raise ValueError("Unexpected sacrifice cost")
    if rule.operation=="mill_all" and any(
            not zones.ids(seat,"library") for seat in life.kernel.life_totals):
        # Empty library milling 0 is legal: milling does not lose the game.
        pass
    if rule.cost:
        try:
            if mana.plan(source.controller,rule.cost) is None:
                return None
        except ValueError as err:
            if str(err)!="Bounded mana search exhausted; no action committed":
                raise
            return None
    paid=mana.pay(source.controller,rule.cost) if rule.cost else None
    if rule.cost and paid is None:
        return None
    if rule.tap:
        source.tapped=True
        kernel._dirty()
    if rule.life_cost:
        life.lose(source.controller,rule.life_cost,source_id)
    if rule.sacrifice_other:
        before=capture_battlefield(kernel)
        move_index=len(kernel.moves)
        zones.move(sacrifice_id,"graveyard","sacrifice",commander_choice=True)
        death_engine.resolve_deaths(before,move_index=move_index,turn=turn)
    affected=()
    if rule.operation=="counter_target":
        put_reviewed_counters(kernel,source.controller,target_id,
            CounterPlacement("+1/+1"))
        affected=(target_id,)
    elif rule.operation=="keyword_self_until_end":
        live=kernel.objects.get(source_id)
        if live is not None:
            kernel.add_modifier(source_id,Modifier(
                keywords=frozenset({rule.keyword}),expires_at="end_turn"))
            affected=(source_id,)
    elif rule.operation=="keyword_own_until_end":
        affected=tuple(o.object_id for o in kernel.on_battlefield()
                       if o.controller==source.controller
                       and "creature" in o.types)
        for oid in affected:
            kernel.add_modifier(oid,Modifier(
                keywords=frozenset({rule.keyword}),expires_at="end_turn"))
    elif rule.operation=="mill_all":
        moved=[]
        for seat in sorted(life.kernel.life_totals):
            if zones.ids(seat,"library"):
                moved.extend(mill_physical_cards(zones,seat,CardQuantity(1)))
        affected=tuple(moved)
    return ActiveOutcome(source_id,rule.operation,affected,
                         tuple(paid.source_ids) if paid else (),rule.life_cost)
