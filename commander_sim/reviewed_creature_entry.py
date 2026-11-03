"""Pinned creature-entry predicates and reusable triggered physical actions.

The caller supplies a completed resolution window. The engine consumes the
existing LiveZones operation log, not a shadow battlefield or guessed ETBs.
Rules are typed data; the dispatcher is independent of individual card names.
This bounded bridge does not implement simultaneous trigger ordering/priority.
"""
from dataclasses import dataclass

from .physical_common_effects import (
    CounterPlacement, put_reviewed_counters,
    TemporaryCreatureChange, change_reviewed_creature_stats)


@dataclass(frozen=True)
class CreatureEntryRule:
    oracle_id: str
    oracle_text: str
    trigger_subtype: str = ""
    trigger_color: str = ""
    another: bool = False
    source_controller_only: bool = True
    operation: str = "counter_self"
    amount: int = 1
    exclude_subtype: str = ""

    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text
                or self.operation not in {"counter_self","opponent_drain","temporary_debuff"}
                or type(self.amount) is not int or self.amount<=0
                or type(self.another) is not bool
                or type(self.source_controller_only) is not bool):
            raise ValueError("Invalid source-pinned creature-entry recipe")


RULES = {
    "Champion of the Perished": CreatureEntryRule(
        "f3654fbd-16a5-4953-84ac-534e8421032f",
        "Whenever another Zombie you control enters, put a +1/+1 counter on this creature.",
        trigger_subtype="Zombie",another=True),
    "Ayara, First of Locthwain": CreatureEntryRule(
        "388168b3-ec68-4af2-b88c-6a5ec88c15f6",
        "Whenever Ayara or another black creature you control enters, each opponent loses 1 life and you gain 1 life.\n{T}, Sacrifice another black creature: Draw a card.",
        trigger_color="B",operation="opponent_drain"),
    "Noxious Ghoul": CreatureEntryRule(
        "602e421e-afab-4488-8a52-af66b4fdce4b",
        "Whenever this creature or another Zombie enters, all non-Zombie creatures get -1/-1 until end of turn.",
        trigger_subtype="Zombie",source_controller_only=False,
        operation="temporary_debuff",exclude_subtype="Zombie"),
}


def reviewed_creature_entry_rule(name,raw):
    rule=RULES.get(name)
    if (rule is None or not isinstance(raw,dict)
            or raw.get("oracle_id")!=rule.oracle_id
            or raw.get("oracle_text")!=rule.oracle_text
            or "Creature" not in raw.get("type_line","").split(" — ",1)[0]):
        return None
    return rule


@dataclass(frozen=True)
class CreatureEntryResolution:
    source_id: int
    entrant_id: int
    source_name: str
    operation: str
    amount: int


class ReviewedCreatureEntryEngine:
    """Consume physical ETBs once, using current source identity and provenance.

    This bounded implementation must be drained immediately after an action's
    resolution. It intentionally does NOT infer the identity of departed
    entrants, reconstruct triggers of sources that left, or invent stack timing.
    """
    def __init__(self,zones,life,catalog,*,death_engine=None):
        if life.kernel is not zones.kernel:
            raise ValueError("Entrants and life must use the same kernel")
        self.zones=zones
        self.life=life
        self.catalog=catalog
        self.death_engine=death_engine
        self.cursor=len(zones.entry_operations)
        self.history=[]

    @staticmethod
    def _entrant(op):
        if op[0]=="add" and len(op)==4 and op[3]=="battlefield":
            return op[2]
        if len(op)>=6 and op[5]=="battlefield" and op[4]!="battlefield":
            return op[3]
        return None

    def resolve(self,*,turn=1):
        kernel=self.zones.kernel
        incoming=self.zones.entry_operations[self.cursor:]
        self.cursor=len(self.zones.entry_operations)
        outcomes=[]
        for op in incoming:
            entrant_id=self._entrant(op)
            if entrant_id is None:
                continue
            entrant=kernel.objects.get(entrant_id)
            if entrant is None or entrant.zone!="battlefield" or "creature" not in entrant.types:
                # Departed entrants need LKI and timed resolution, not guesses.
                continue
            for source in sorted(tuple(kernel.on_battlefield()),key=lambda o:o.object_id):
                rule=reviewed_creature_entry_rule(
                    source.card.name,self.catalog.get(source.card.name))
                if (rule is None or source.card.card_id!=rule.oracle_id
                        or source.object_id>entrant_id
                        or (rule.another and source.object_id==entrant_id)
                        or (rule.source_controller_only
                            and source.controller!=entrant.controller)
                        or (rule.trigger_subtype and
                            rule.trigger_subtype not in kernel.subtypes(entrant_id))
                        or (rule.trigger_color and
                            (entrant.card.colors is None
                             or rule.trigger_color not in entrant.card.colors))):
                    continue
                if rule.operation=="counter_self":
                    put_reviewed_counters(kernel,source.controller,source.object_id,
                        CounterPlacement("+1/+1",rule.amount))
                    kernel.check_state_based()
                elif rule.operation=="opponent_drain":
                    self.life.each_opponent_loses(
                        source.controller,rule.amount,source.object_id)
                    self.life.gain(source.controller,rule.amount,source.object_id)
                elif rule.operation=="temporary_debuff":
                    affected=tuple(body.object_id
                        for body in tuple(kernel.on_battlefield())
                        if "creature" in body.types
                        and (not rule.exclude_subtype or
                             rule.exclude_subtype not in kernel.subtypes(body.object_id)))
                    change_reviewed_creature_stats(
                        self.zones,affected,
                        TemporaryCreatureChange(-rule.amount,-rule.amount),
                        death_engine=self.death_engine,turn=turn)
                record=CreatureEntryResolution(
                    source.object_id,entrant_id,source.card.name,
                    rule.operation,rule.amount)
                outcomes.append(record)
                self.history.append(record)
        return tuple(outcomes)
