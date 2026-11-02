"""Source-paid physical Commander casting from command zone with shared tax.

Permission is granted only for a card with separately reviewed, safe ordinary
entry. Card-specific abilities are resolved by the existing shared engines.
This component never casts an unsupported commander by name or inferred text.
"""
from dataclasses import dataclass
from .mana_costs import parse_fixed_mana_cost
from .reviewed_cost_reduction import cost_symbols
from .composed_abilities import ABILITIES

@dataclass(frozen=True)
class CommanderCast:
    card_name: str
    physical_id: int
    paid_source_ids: tuple[int,...]
    commander_tax: int
    previous_casts: int


def commander_cost(kernel, source, catalog):
    if (source.zone!="command" or "commander" not in source.card.supertypes
            or "creature" not in source.types):
        return None
    raw=catalog.get(source.card.name,{})
    if raw.get("oracle_id")!=source.card.card_id or raw.get("layout")!="normal":
        return None
    # Composed ability profiles are independent proof of reviewed safe entry
    # for Mortarion. Future commanders can be admitted using the same body gate.
    rules=ABILITIES.get(source.card.name,())
    if not rules or not all(r.oracle_id==source.card.card_id
                            and r.oracle_excerpt in raw.get("oracle_text","")
                            for r in rules):
        return None
    parsed=parse_fixed_mana_cost(raw.get("mana_cost"))
    count=getattr(kernel,"reviewed_commander_cast_counts",{}).get(source.card.card_id,0)
    from .mana_costs import FixedManaCost
    return cost_symbols(FixedManaCost(parsed.generic+2*count,parsed.colored))


def cast_commander(zones,seat,source_id,catalog,mana_service,*,on_cast=None):
    kernel=zones.kernel
    source=kernel.get(source_id)
    if source.owner!=seat or source.controller!=seat:
        raise ValueError("Commander actor mismatch")
    cost=commander_cost(kernel,source,catalog)
    if cost is None:
        raise ValueError("Unreviewed commander handoff from command zone")
    planned=mana_service.plan_spell(seat,cost,source)
    if planned is None:
        return None
    paid=mana_service.pay_spell(seat,cost,source)
    if paid is None:
        raise AssertionError("Reviewed commander mana plan invalidated")
    before=getattr(kernel,"reviewed_commander_cast_counts",{}).get(source.card.card_id,0)
    ticket=zones.cast(seat,source_id)
    if on_cast is not None:
        on_cast(ticket)
    result=zones.resolve(ticket)
    counts=getattr(kernel,"reviewed_commander_cast_counts",{})
    counts[source.card.card_id]=before+1
    kernel.reviewed_commander_cast_counts=counts
    return CommanderCast(source.card.name,result,tuple(paid.source_ids),2*before,before)
