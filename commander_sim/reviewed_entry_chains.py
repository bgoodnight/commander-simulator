"""Finite shared ETB trigger queue for physical reanimation and token engines.

Each source must independently pass reviewed_enter_rule and have a recorded
physical battlefield-entry transition. The queue processes triggers using a
stable bounded order, never assuming APNAP priority or opponent interaction.
Choices come from a policy callback; complex effects without a reviewed
action are explicitly skipped, not fabricated.
"""
from dataclasses import dataclass

from .reviewed_enter_effects import (
    reviewed_enter_rule, execute_reviewed_enter)


@dataclass(frozen=True)
class EntryChainOutcome:
    resolved: tuple[object,...]
    deferred_ids: tuple[int,...]
    unreviewed_ids: tuple[int,...]
    complete: bool


def bounded_entry_choice(rule, source, zones, life):
    """Deliberately simple pilot policy, replaceable without rules rewrites."""
    if rule.operation=="exile_graveyard_tokens":
        # The same typed choice works for any future ETB using graveyard
        # counting, not just this source. The actor may legally choose self.
        seats=tuple(sorted(life.kernel.life_totals))
        return max(seats,key=lambda seat:(
            sum(bool(zones.kernel.get(oid).types & rule.count_types_any)
                for oid in zones.ids(seat,"graveyard")),
            seat!=source.controller,-seat))
    if rule.operation=="fabricate_one":
        return "servo"
    if rule.operation=="optional_exile_nonland":
        return None
    if rule.operation=="each_player_sacrifice":
        chosen={}
        for seat in sorted(life.kernel.life_totals):
            options=tuple(obj for obj in zones.kernel.controlled(
                seat,{"creature"}))
            if options:
                selected=min(options,key=lambda o:(o.power,o.object_id))
                chosen[seat]=selected.object_id
        return chosen
    return None


def resolve_reviewed_entry_chain(
        zones,life,initial_ids,catalog,*,death_engine=None,turn=1,
        max_triggers=12,select=None):
    """Process actual entries, including further reanimated entrants.

    Retains physical IDs and exact Oracle admission. The returned
    deferred_ids identifies triggers left unresolved by the bounded cap.
    The caller should export this limitation to avoid implying that a
    capped sequence was completely simulated.
    """
    if (life.kernel is not zones.kernel
            or type(max_triggers) is not int
            or not 1<=max_triggers<=100):
        raise ValueError("Entry chain requires one kernel and finite budget")
    if not isinstance(catalog,dict):
        raise TypeError("Reviewed catalog required")
    pending=list(initial_ids)
    if any(type(oid) is not int for oid in pending):
        raise ValueError("Entry source IDs must be physical integers")
    chooser=bounded_entry_choice if select is None else select
    if not callable(chooser):
        raise TypeError("Entry choice must be callable")
    visited=set()
    outcomes=[]
    ignored=[]
    while pending and len(outcomes)<max_triggers:
        oid=pending.pop(0)
        if oid in visited:
            continue
        visited.add(oid)
        obj=zones.kernel.objects.get(oid)
        if obj is None or obj.zone!="battlefield":
            continue
        raw=catalog.get(obj.card.name)
        rule=reviewed_enter_rule(obj.card.name,raw)
        if rule is None or obj.card.card_id!=rule.oracle_id:
            ignored.append(oid)
            continue
        choice=chooser(rule,obj,zones,life)
        outcome=execute_reviewed_enter(
            zones,life,oid,catalog,choice=choice,
            death_engine=death_engine,turn=turn)
        if outcome is None:
            continue
        outcomes.append(outcome)
        pending.extend(outcome.reanimated_ids)
    return EntryChainOutcome(tuple(outcomes),tuple(pending),
                             tuple(ignored),not pending)
