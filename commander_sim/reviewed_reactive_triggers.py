"""Reusable bounded subscriptions to physical token and life-change events.

This is a typed supplement to existing death/phase engines, not a secondary
battlefield or a universal MTG priority/stack engine. Every registration is
source-pinned. A driver calls resolve() after reviewed physical transactions;
the dispatcher consumes only new events and handles newly generated life events
until quiescent. Event ordering is bounded, not full APNAP priority ordering.
"""
from dataclasses import dataclass
from .ability_composition import (
    AbilitySlot, AbilityHandler, ComposedCard, AbilityDispatcher)


@dataclass(frozen=True)
class ReactiveRule:
    oracle_id: str
    excerpt: str
    event: str
    operation: str
    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt
                or self.event not in {"token_created","token_sacrificed",
                                       "token_left","life_gained"}
                or self.operation not in {"drain_opponents","drain_gain",
                                          "target_opponent_loses_amount"}):
            raise ValueError("Invalid reactive trigger descriptor")


RULES={
    "Mirkwood Bats":(
        ReactiveRule("0636b6c3-0662-420a-b30d-f0a14e7c512d",
                     "Whenever you create or sacrifice a token, each opponent loses 1 life.",
                     "token_created","drain_opponents"),
        ReactiveRule("0636b6c3-0662-420a-b30d-f0a14e7c512d",
                     "Whenever you create or sacrifice a token, each opponent loses 1 life.",
                     "token_sacrificed","drain_opponents")),
    "Nadier's Nightblade":(
        ReactiveRule("391978f6-0bbc-41e8-9246-f7d0e21c7900",
                     "Whenever a token you control leaves the battlefield, each opponent loses 1 life and you gain 1 life.",
                     "token_left","drain_gain"),),
    "Vito, Thorn of the Dusk Rose":(
        ReactiveRule("7336a541-3ae9-4ab2-acb8-f574c0a5b3a9",
                     "Whenever you gain life, target opponent loses that much life.",
                     "life_gained","target_opponent_loses_amount"),),
}


@dataclass(frozen=True)
class ReactiveResolution:
    source_id: int
    source_name: str
    event: str
    operation: str
    quantity: int


class ReactiveTriggerEngine:
    """Emit registered response effects from actual kernel events only."""

    def __init__(self,zones,life,catalog):
        if life.kernel is not zones.kernel:
            raise ValueError("Reactive host mismatch")
        self.zones=zones
        self.life=life
        self.catalog=catalog
        kernel=zones.kernel
        self._token_cursor=len(getattr(kernel,"reviewed_token_events",()))
        self._move_cursor=len(kernel.moves)
        self._life_cursor=len(kernel.life_changes)
        self._event_cursor=len(kernel.events)
        self.resolutions=[]

    def _reviewed(self,source,event):
        row=self.catalog.get(source.card.name)
        if (source.zone!="battlefield" or not isinstance(row,dict)
                or row.get("oracle_id")!=source.card.card_id):
            return ()
        return tuple(rule for rule in RULES.get(source.card.name,())
                     if rule.oracle_id==source.card.card_id
                     and rule.excerpt in row.get("oracle_text","")
                     and rule.event==event)

    def _dispatch(self,event,actor,quantity):
        results=[]
        for source in sorted(tuple(self.zones.kernel.on_battlefield()),
                             key=lambda o:o.object_id):
            if source.controller!=actor:
                continue
            for idx,rule in enumerate(self._reviewed(source,event)):
                slot=AbilitySlot(rule.oracle_id,"front",
                    "reactive_"+rule.event+"_"+str(idx),"triggered",rule,
                    rule.excerpt,"pinned-reactive-v1",
                    frozenset({"physical_events","life_totals"}))
                reviewed=ComposedCard(rule.oracle_id,
                    self.catalog[source.card.name]["oracle_text"],(slot,),
                    (AbilityHandler(slot.key,"simplified",rule,
                        slot.source_revision,slot.prereqs,
                        ("No opponent priority, target selection policy uses first opponent",)),))
                dispatcher=AbilityDispatcher(
                    reviewed,"hybrid",frozenset({"physical_events","life_totals"}))
                def apply(operation):
                    controller=source.controller
                    if operation.operation=="drain_opponents":
                        self.life.each_opponent_loses(controller,quantity,source.object_id)
                    elif operation.operation=="drain_gain":
                        self.life.each_opponent_loses(controller,quantity,source.object_id)
                        self.life.gain(controller,quantity,source.object_id)
                    elif operation.operation=="target_opponent_loses_amount":
                        # Deterministic legal target; strategy may override
                        # selection later without changing this rules effect.
                        opponents=[seat for seat in sorted(self.life.kernel.life_totals)
                                   if seat!=controller]
                        if opponents:
                            self.life.lose(opponents[0],quantity,source.object_id)
                dispatcher.invoke(slot.slot_id,source.object_id,apply)
                results.append(ReactiveResolution(source.object_id,
                    source.card.name,event,rule.operation,quantity))
        return results

    def resolve(self):
        """Drain token/move/life event cursors; no invented future triggers."""
        kernel=self.zones.kernel
        outcomes=[]
        for _ in range(16):
            new_tokens=getattr(kernel,"reviewed_token_events",())[self._token_cursor:]
            new_moves=kernel.moves[self._move_cursor:]
            new_events=kernel.events[self._event_cursor:]
            new_life=kernel.life_changes[self._life_cursor:]
            self._token_cursor+=len(new_tokens)
            self._move_cursor+=len(new_moves)
            self._event_cursor+=len(new_events)
            self._life_cursor+=len(new_life)
            if not (new_tokens or new_moves or new_life):
                break
            for seat,oid in new_tokens:
                outcomes.extend(self._dispatch("token_created",seat,1))
            # The kernel's token_ceased event records the pre-move controller,
            # even when the old token ceased to exist as a game object.
            controllers={event.target_id:event.actor for event in new_events
                         if event.name=="token_ceased"}
            for move in new_moves:
                if move.old_zone!="battlefield" or move.object_id not in controllers:
                    continue
                seat=controllers[move.object_id]
                outcomes.extend(self._dispatch("token_left",seat,1))
                if move.reason=="sacrifice":
                    outcomes.extend(self._dispatch("token_sacrificed",seat,1))
            for change in new_life:
                if change.kind=="gain":
                    outcomes.extend(self._dispatch("life_gained",
                                                   change.seat,change.amount))
        else:
            raise RuntimeError("Reactive trigger cascade exceeded finite safety bound")
        self.resolutions.extend(outcomes)
        return tuple(outcomes)
