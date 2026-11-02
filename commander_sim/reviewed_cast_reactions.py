"""Source-pinned reusable permanent subscriptions to verified spell casts."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CastReaction:
    oracle_id:str
    excerpt:str
    predicate:str
    operation:str
    count:int=1
    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt or self.count<1
                or self.predicate not in {"black_spell"}
                or self.operation not in {"self_counter"}):
            raise ValueError("Unsupported cast reaction")


RULES={
    "K'rrik, Son of Yawgmoth":CastReaction(
        "cbe3a4e7-5dbe-4f58-8ee6-a1762b65acfd",
        "Whenever you cast a black spell, put a +1/+1 counter on K'rrik.",
        "black_spell","self_counter")
}


@dataclass(frozen=True)
class CastReactionResult:
    source_id:int
    operation:str
    quantity:int


def resolve_cast_reactions(zones,seat,catalog,*,source_spell):
    """Use actual currently committed spell source, not guessed color tags."""
    from .physical_common_effects import CounterPlacement,put_reviewed_counters
    if (source_spell.zone!="stack" or source_spell.controller!=seat
            or "spell_cast" not in [event.name for event in zones.kernel.events[-3:]]):
        raise ValueError("Expected an actual cast source still on stack")
    results=[]
    colors=source_spell.card.colors or frozenset()
    for source in sorted(tuple(zones.kernel.on_battlefield()),
                         key=lambda o:o.object_id):
        rule=RULES.get(source.card.name)
        meta=catalog.get(source.card.name)
        if (source.controller!=seat or rule is None or not isinstance(meta,dict)
                or meta.get("oracle_id")!=rule.oracle_id
                or rule.excerpt not in meta.get("oracle_text","")
                or source.card.card_id!=rule.oracle_id):
            continue
        matches=(rule.predicate=="black_spell" and "B" in colors)
        if matches:
            put_reviewed_counters(zones.kernel,seat,source.object_id,
                                  CounterPlacement("+1/+1",rule.count))
            results.append(CastReactionResult(
                source.object_id,rule.operation,rule.count))
    return tuple(results)
