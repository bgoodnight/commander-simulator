"""Typed artifact-departure event effects on the authoritative physical kernel.

The host supplies pre-move last-known battlefield facts. This is not an
Oracle-text parser or a universal replacement/priority system. Duplicated
delivery of a physical zone-change event never repeats its triggered effect.
"""
from dataclasses import dataclass
from types import MappingProxyType

from .physical_common_effects import CounterPlacement, put_reviewed_counters


@dataclass(frozen=True)
class ArtifactDepartureRule:
    oracle_id: str
    oracle_text: str
    counters_per_artifact: int

    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text
                or type(self.counters_per_artifact) is not int
                or self.counters_per_artifact < 1):
            raise ValueError("Invalid reviewed artifact departure trigger")


RULES = {
    "Shard of the Void Dragon": ArtifactDepartureRule(
        "d04d2434-121e-4420-abfc-fa21ad5577c3",
        "Flying\nSpear of the Void Dragon — Whenever this creature attacks, each opponent sacrifices a nonland permanent of their choice.\nMatter Absorption — Whenever an artifact is put into a graveyard from the battlefield or is put into exile from the battlefield, put two +1/+1 counters on this creature.",
        2),
}


@dataclass(frozen=True)
class ArtifactDepartureOutcome:
    source_id: int
    moved_artifact_old_ids: tuple[int, ...]
    counters_added: int


class ReviewedArtifactDepartureEngine:
    """Consume validated battlefield-to-graveyard/exile moves exactly once."""
    def __init__(self, zones, catalog):
        self.zones = zones
        self.catalog = catalog
        self._handled = set()
        self.history = []

    def resolve(self, before, *, move_index):
        kernel = self.zones.kernel
        if not isinstance(before, MappingProxyType):
            raise TypeError("Pre-event last-known battlefield facts required")
        if type(move_index) is not int or not 0 <= move_index <= len(kernel.moves):
            raise ValueError("Invalid artifact departure event boundary")
        changes = []
        for move in kernel.moves[move_index:]:
            if (move.old_zone != "battlefield"
                    or move.new_zone not in {"graveyard", "exile"}
                    or move.object_id in self._handled):
                continue
            fact = before.get(move.object_id)
            if fact is None:
                raise ValueError("Departure missing its battlefield LKI")
            if "artifact" in fact.types:
                changes.append(move.object_id)
        if not changes:
            return ()
        # An old instance can enter a different zone only once. Mark before
        # running triggers so later chained moves cannot count it again.
        self._handled.update(changes)
        outcomes = []
        for source in tuple(kernel.on_battlefield()):
            rule = RULES.get(source.card.name)
            raw = self.catalog.get(source.card.name)
            if (rule is None or source.card.card_id != rule.oracle_id
                    or not isinstance(raw, dict)
                    or raw.get("oracle_id") != rule.oracle_id
                    or raw.get("oracle_text") != rule.oracle_text
                    or "creature" not in source.types):
                continue
            amount = len(changes) * rule.counters_per_artifact
            put_reviewed_counters(
                kernel, source.controller, source.object_id,
                CounterPlacement("+1/+1", amount))
            result = ArtifactDepartureOutcome(
                source.object_id, tuple(changes), amount)
            self.history.append(result)
            outcomes.append(result)
        if outcomes:
            kernel.check_state_based()
        return tuple(outcomes)
