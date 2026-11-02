"""Execute small source-inferred spell recipes on the real physical kernel.

The importer authorizes only exact self-contained printed sentences; no
unreviewed targets, optional modes or additional costs are invented.
"""
from dataclasses import dataclass

from .generic_cast import ReviewedCreatureCast, cast_reviewed_spell
from .physical_common_effects import CardQuantity, draw_physical_cards
from .provisional_import import provisional_profile


@dataclass(frozen=True)
class ProvisionalSpellOutcome:
    name: str
    operation: str
    count: int
    drawn_ids: tuple[int,...]
    paid_source_ids: tuple[int,...]
    resolved_zone_id: int
    fidelity: str = "provisional_partial"


def cast_provisional_spell(zones, life, seat, object_id, catalog, colors,
                           mana_service, *, on_cast=None):
    """Source-pay and resolve an exactly recognized spell with bounded effects.

    None means an unpayable or non-survivable spell; it never commits an
    unsupported partial payment. The original source is still physically
    moved hand -> stack -> graveyard.
    """
    kernel=zones.kernel
    if life.kernel is not kernel or mana_service.kernel is not kernel:
        raise ValueError("Provisional spell services must share kernel")
    if object_id not in zones.ids(seat,"hand"):
        raise ValueError("Provisional spell must be in actor hand")
    obj=kernel.get(object_id)
    raw=catalog.get(obj.card.name)
    profile=provisional_profile(raw)
    if (profile is None or profile.kind!="simple_spell"
            or obj.card.card_id!=profile.oracle_id
            or obj.card.types not in (frozenset({"instant"}),
                                       frozenset({"sorcery"}))):
        raise ValueError("Source-unverified or unsupported spell")
    if (profile.mode in {"draw","draw_lose"}
            and len(zones.ids(seat,"library"))<profile.amount):
        return None
    if profile.life_amount and life.total(seat)<=profile.life_amount:
        return None
    review=ReviewedCreatureCast(
        profile.oracle_id,profile.mana_cost,True,profile.omissions)
    commit=cast_reviewed_spell(
        zones,seat,object_id,review,colors,mana_service=mana_service,
        spell_type=next(iter(obj.card.types)))
    if commit is None:return None
    if on_cast is not None:
        on_cast(commit.ticket)
    drawn=[]
    def apply_effect(kernel,ticket):
        if profile.mode in {"draw","draw_lose"}:
            outcome=draw_physical_cards(
                zones,seat,CardQuantity(profile.amount))
            if not outcome.complete:
                raise AssertionError("Provisional draw feasibility changed")
            drawn.extend(outcome.drawn_ids)
        if profile.mode=="draw_lose":
            life.lose(seat,profile.life_amount,object_id)
        elif profile.mode=="gain_life":
            life.gain(seat,profile.amount,object_id)
        elif profile.mode=="opponent_loss":
            life.each_opponent_loses(seat,profile.amount,object_id)
    resolved=zones.resolve(commit.ticket,effect=apply_effect)
    return ProvisionalSpellOutcome(
        obj.card.name,profile.mode,profile.amount,tuple(drawn),
        tuple(commit.paid_source_ids),resolved)
