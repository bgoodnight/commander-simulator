"""Reviewed Necron unearth: common costs, haste, exile replacement, expiry.

The *existing IndexedKernel* owns physical graveyard/battlefield/exile IDs
and its unearth replacement map. Only externally authorized sorcery-speed
activations are accepted, and cards with unimplemented mandatory ETB effects
fail closed rather than entering without their triggered abilities.
"""
from dataclasses import dataclass,replace

from .ability_composition import (
    AbilitySlot,AbilityHandler,ComposedCard,AbilityDispatcher)


@dataclass(frozen=True)
class UnearthReview:
    oracle_id: str
    cost: str
    excerpt: str
    etb_requires_review: bool = False

    def __post_init__(self):
        if (not self.oracle_id or not self.cost or not self.excerpt
                or type(self.etb_requires_review) is not bool):
            raise ValueError("Invalid pinned unearth ability")


UNEARTH={
    "Chronomancer":UnearthReview("b7e9e455-423f-4102-b166-05cc766c1319",
        "{2}{B}","Unearth {2}{B}"),
    "Lokhust Heavy Destroyer":UnearthReview("a4e097b8-8b9e-439b-bd98-a489bbcf3464",
        "{5}{B}{B}{B}","Unearth {5}{B}{B}{B}",True),
    "Royal Warden":UnearthReview("feac0c4e-2ea8-457e-b86f-8e1164daaa33",
        "{3}{B}","Unearth {3}{B}",True),
    "Skorpekh Lord":UnearthReview("d3f0ebf8-0620-431f-8a90-dd681cbe7eab",
        "{2}{B}","Unearth {2}{B}"),
    "Tomb Blade":UnearthReview("4b9146c8-df52-4761-a46b-865a265eccb3",
        "{6}{B}{B}","Unearth {6}{B}{B}"),
    "Canoptek Tomb Sentinel":UnearthReview("9ecc7928-bb41-4e38-ab81-6b7b58ce07ad",
        "{7}","Unearth {7}",True),
    "Hexmark Destroyer":UnearthReview("05c6d9e9-01ac-4a44-a43b-4f61d2df831d",
        "{4}{B}{B}","Unearth {4}{B}{B}"),
    "Triarch Praetorian":UnearthReview("ce949dbb-08ee-4c59-a48e-cdd5ce30b13d",
        "{4}{B}","Unearth {4}{B}",True),
}


@dataclass(frozen=True)
class UnearthOutcome:
    source_old_id: int
    permanent_id: int
    card_name: str
    paid_source_ids: tuple[int,...]
    expires_at: str = "next_end_step"


def reviewed_unearth(name,raw):
    row=UNEARTH.get(name)
    if (row is None or not isinstance(raw,dict)
            or raw.get("oracle_id")!=row.oracle_id
            or row.excerpt not in raw.get("oracle_text","")
            or "Creature" not in raw.get("type_line","")):
        return None
    return row


def activate_reviewed_unearth(zones,seat,old_id,catalog,mana_service,*,
                               sorcery_window=False):
    """Pay reviewed printed unearth cost and return ONE physical card.

    No stack is constructed for an activated ability in this bounded pilot;
    priority, responses and ETB trigger chains need the multiplayer host.
    """
    if sorcery_window is not True:
        raise ValueError("Unearth may only activate in verified sorcery window")
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid seat")
    if old_id not in zones.ids(seat,"graveyard"):
        raise ValueError("Unearth source is not in actor graveyard")
    source=zones.kernel.get(old_id)
    meta=catalog.get(source.card.name)
    review=reviewed_unearth(source.card.name,meta)
    if (review is None or source.owner!=seat
            or "creature" not in source.types
            or source.card.card_id!=review.oracle_id):
        raise ValueError("Unreviewed unearth permission")
    if review.etb_requires_review:
        raise NotImplementedError("Printed ETB effect needs a reviewed stack handler")
    if (mana_service is None or mana_service.kernel is not zones.kernel
            or not hasattr(zones.kernel,"unearth_pending")):
        raise ValueError("Matching physical resource/kernel service required")
    plan=mana_service.plan(seat,review.cost)
    if plan is None:
        return None
    slot=AbilitySlot(review.oracle_id,"front","unearth","activated",review,
         review.excerpt,"pinned-oracle-m1",
         frozenset({"graveyard_permission","exile_replacement","paid_mana"}))
    card=ComposedCard(review.oracle_id,meta["oracle_text"],(slot,),
        (AbilityHandler(slot.key,"exact",review,slot.source_revision,
         slot.prereqs),))
    dispatcher=AbilityDispatcher(card,"strict",slot.prereqs)
    def perform(operation):
        paid=mana_service.pay(seat,operation.cost)
        if paid is None:
            raise AssertionError("Reviewed unearth payment preview invalidated")
        # An activated ability resolves into battlefield without casting.
        permanent_id=zones.move(old_id,"battlefield","resolve")
        live=zones.kernel.get(permanent_id)
        original=live.card
        live.card=replace(original,keywords=original.keywords|frozenset({"haste"}))
        zones.kernel.unearth_pending[permanent_id]=original
        zones.kernel._dirty()
        return UnearthOutcome(old_id,permanent_id,source.card.name,paid.source_ids)
    return dispatcher.invoke(slot.slot_id,old_id,perform)


def expire_reviewed_unearth(zones):
    """Exile remaining unearthed instances at their next end step.

    The kernel already redirects other earlier exits to exile instead of
    graveyard, so expiring again cannot create a second physical object.
    """
    pending=dict(zones.kernel.unearth_pending)
    results=[]
    for permanent_id in sorted(pending):
        obj=zones.kernel.objects.get(permanent_id)
        if obj is None or obj.zone!="battlefield":
            raise AssertionError("Unearth replacement map contains stale object")
        next_id=zones.move(permanent_id,"exile","exile")
        results.append((permanent_id,next_id))
    return tuple(results)
