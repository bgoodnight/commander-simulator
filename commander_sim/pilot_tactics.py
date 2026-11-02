"""Pure, bounded opportunity scoring over existing reviewed sacrifice rules.

This does NOT authorize sacrifices. The physical runner supplies legal source,
target, tap readiness, mana and timing; the reviewed executor pays costs.
No card identity decides strategic value: scoring uses registered effect
operations, live death-trigger predicates, observed life/hand and token costs.
"""
from dataclasses import dataclass

from .reviewed_sacrifice_actions import SACRIFICE_MODES
from .reviewed_death_effects import BattlefieldFact, DEATH_RULES, _matches


@dataclass(frozen=True)
class SacrificeChoice:
    source_id: int
    victim_id: int
    score: int
    trigger_count: int
    factors: tuple[str,...]


_DEATH_VALUE = {
    "drain_gain":5, "target_drain_gain":4, "damage_opponents":4,
    "drain":4, "draw":5, "draw_lose":3, "treasure":3,
    "zombie":4, "counter_self":2, "gain":2, "lose_controller":2,
    "damage_all":1,
}


def _trigger_value(action, hand_size):
    if action.operation=="sequence":
        weights={"draw":5 if hand_size<=4 else 3,
                 "opponents_lose":4,"gain_life":2,"token":4,
                 "counter_self":2,"lose_life":-4,"damage_self":-4}
        return sum(weights.get(step.kind,0)*step.count
                   for step in action.steps)
    if action.operation in {"draw","draw_lose"}:
        return (5 if hand_size<=4 else 3)*action.quantity
    return _DEATH_VALUE.get(action.operation,0)*action.quantity


def _needed_draws(action):
    if action.operation=="sequence":
        return sum(step.count for step in action.steps
                   if step.kind=="draw")
    if action.operation in {"draw","draw_lose"}:
        return action.quantity
    return 0


def _mode_value(action, victim, hand_size):
    if action=="scry":
        return 1
    if action=="draw":
        return 7 if hand_size<=4 else 3
    if action=="wither_draw":
        return 8 if hand_size<=4 else 4
    if action=="self_counter":
        return 3
    if action=="zombies_by_power":
        return 3*max(0,victim.power)
    return 0


def choose_discretionary_sacrifice(
    zones,seat,life,mana_service,catalog,death_engine,*,turn,
    entered_on_turn,archetype="midrange"):
    """Select one profitable reviewed non-mana sacrifice or decline.

    Rejects speculative sacrifices without a positive realized payoff,
    exhausted once-a-turn triggers, tapped/summoning-sick sources,
    unpayable costs and mandatory draws that would exceed actual library.
    Returns a *candidate only*; activation still goes through the kernel.
    """
    if (life.kernel is not zones.kernel or
            mana_service.kernel is not zones.kernel or
            death_engine.zones is not zones):
        raise ValueError("Sacrifice policy requires one authoritative host")
    if type(turn) is not int or turn<1:
        raise ValueError("Expected positive physical turn")
    if not isinstance(entered_on_turn,dict):
        raise TypeError("Physical entry evidence required")
    kernel=zones.kernel
    hand_size=len(zones.ids(seat,"hand"))
    source_cards=sorted(
        (o for o in kernel.on_battlefield()
         if o.controller==seat and o.card.name in SACRIFICE_MODES),
        key=lambda o:o.object_id)
    creatures=sorted(
        (o for o in kernel.on_battlefield()
         if o.controller==seat and "creature" in o.types
         and "commander" not in o.card.supertypes),
        key=lambda o:o.object_id)
    candidates=[]
    for source in source_cards:
        mode=SACRIFICE_MODES[source.card.name]
        if mode.action in {"colorless_mana","any_color_mana",
                           "black_mana_by_value"}:
            continue
        raw=catalog.get(source.card.name,{})
        if (raw.get("oracle_id")!=source.card.card_id or
                mode.oracle_id!=source.card.card_id or
                mode.excerpt not in raw.get("oracle_text","")):
            continue
        if mode.tap and (source.tapped or (
                "creature" in source.types and
                entered_on_turn.get(source.object_id,0)>=turn and
                "haste" not in source.keywords)):
            continue
        if mode.black_cost:
            try:
                if mana_service.plan(seat,"{B}"*mode.black_cost) is None:
                    continue
            except ValueError as err:
                if str(err)!="Bounded mana search exhausted; no action committed":
                    raise
                continue
        if mode.life_cost and life.total(seat)<=mode.life_cost+6:
            continue
        if mode.action in {"draw","wither_draw"} and not zones.ids(seat,"library"):
            continue
        for victim in creatures:
            if (mode.sacrifice_other and source.object_id==victim.object_id
                    or mode.victim_color and
                    (victim.card.colors is None or
                     mode.victim_color not in victim.card.colors)):
                continue
            if mode.action=="zombies_by_power" and victim.power<=0:
                continue
            dead=BattlefieldFact.of(victim)
            triggers=[]
            draws={}
            for permanent in kernel.on_battlefield():
                # Only our own validated triggers are payoffs. Opponent
                # death triggers are not strategic benefits.
                if permanent.controller!=seat:
                    continue
                live=BattlefieldFact.of(permanent)
                raw_trigger=catalog.get(live.name,{})
                if raw_trigger.get("oracle_id")!=live.oracle_id:
                    continue
                for rule in DEATH_RULES.get(live.name,()):
                    if (rule.oracle_id!=live.oracle_id or
                        rule.excerpt not in raw_trigger.get("oracle_text","") or
                        not _matches(rule.action,live,dead)):
                        continue
                    if (rule.action.once_per_turn and
                        (turn,live.object_id,rule.slot_id) in death_engine._once):
                        continue
                    triggers.append(rule.action)
                    count=_needed_draws(rule.action)
                    if count:
                        draws[live.controller]=draws.get(live.controller,0)+count
            if mode.action in {"draw","wither_draw"}:
                draws[seat]=draws.get(seat,0)+1
            if any(len(zones.ids(owner,"library"))<needed
                   for owner,needed in draws.items()):
                continue
            effect=_mode_value(mode.action,victim,hand_size)
            effect+=sum(_trigger_value(rule,hand_size) for rule in triggers)
            # A token still contributes board presence, so paying one away
            # requires a tangible effect. Real permanents cost more, with
            # extra caution for high-power and non-expendable engine bodies.
            victim_cost=(5+max(0,victim.power)//2 if victim.token else
                         10+max(0,victim.power))
            if source.object_id==victim.object_id:
                victim_cost+=4
            net=effect-victim_cost-mode.life_cost*2
            # Archetype is a modest preference, never permission to use a
            # useless outlet or pay a life-threatening activation cost.
            if archetype=="aristocrats" and triggers:
                net+=1
            if net<2:
                continue
            factors=(f"ability:{mode.action}",
                     f"reviewed_death_triggers:{len(triggers)}",
                     f"estimated_effect:{effect}",
                     f"sacrificed_token:{bool(victim.token)}",
                     f"net_value:{net}")
            candidates.append((
                -net, -len(triggers), int(not victim.token),
                victim.object_id,source.object_id,
                SacrificeChoice(source.object_id,victim.object_id,
                                net,len(triggers),factors)))
    if not candidates:
        return None
    return min(candidates)[-1]
