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
    "Chronomancer":UnearthReview("9833e3bd-6e7f-41b7-bf7e-ffb74ff17844",
        "{2}{B}","Unearth {2}{B}"),
    "Lokhust Heavy Destroyer":UnearthReview("fd03f20a-d365-48fb-8b2a-ad4b502a0045",
        "{5}{B}{B}{B}","Unearth {5}{B}{B}{B}",True),
    "Royal Warden":UnearthReview("0192ba05-6144-4fec-a803-462ecdf64195",
        "{3}{B}","Unearth {3}{B}",True),
    "Skorpekh Lord":UnearthReview("c40e8d52-d4cc-4502-8b51-a5612dbe1ada",
        "{2}{B}","Unearth {2}{B}"),
    "Tomb Blade":UnearthReview("c857de66-f4e0-4e97-ad01-fac623af8225",
        "{6}{B}{B}","Unearth {6}{B}{B}"),
    "Canoptek Tomb Sentinel":UnearthReview("678b3fb5-aa9f-4268-9433-2a89dd37b927",
        "{7}","Unearth {7}",True),
    "Hexmark Destroyer":UnearthReview("b3329240-c812-45ea-a7f8-4d79cd4ed515",
        "{4}{B}{B}","Unearth {4}{B}{B}"),
    "Triarch Praetorian":UnearthReview("52aa5a79-db0e-4eaa-b2df-e41674c47794",
        "{4}{B}","Unearth {4}{B}",True),
}


@dataclass(frozen=True)
class UnearthOutcome:
    source_old_id: int
    permanent_id: int
    card_name: str
    paid_source_ids: tuple[int,...]
    expires_at: str = "next_end_step"
    enter_result: object | None = None


def reviewed_unearth(name,raw):
    row=UNEARTH.get(name)
    if (row is None or not isinstance(raw,dict)
            or raw.get("oracle_id")!=row.oracle_id
            or row.excerpt not in raw.get("oracle_text","")
            or "Creature" not in raw.get("type_line","")):
        return None
    return row


def activate_reviewed_unearth(zones,seat,old_id,catalog,mana_service,*,
                               sorcery_window=False,life=None,
                               enter_choice=None,death_engine=None,turn=1):
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
        if life is None or life.kernel is not zones.kernel:
            raise NotImplementedError("Printed ETB effect needs reviewed life/stack host")
        if source.card.name=="Triarch Praetorian" and len(zones.ids(seat,"library"))<2:
            raise NotImplementedError("Triarch mandatory draw needs loss/SBA host")
        if source.card.name=="Lokhust Heavy Destroyer":
            if not isinstance(enter_choice,dict) or seat not in enter_choice:
                raise ValueError("Lokhust mandatory per-player choices are required")
        if source.card.name=="Canoptek Tomb Sentinel" and enter_choice is not None:
            target=zones.kernel.objects.get(enter_choice)
            if (target is None or target.zone!="battlefield"
                    or "land" in target.types):
                raise ValueError("Illegal preselected nonland exile target")
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
        result=None
        if operation.etb_requires_review:
            from .reviewed_enter_effects import execute_reviewed_enter
            selected=enter_choice
            if source.card.name=="Lokhust Heavy Destroyer":
                selected={seat_id:(permanent_id if selection=="source" else selection)
                          for seat_id,selection in enter_choice.items()}
            result=execute_reviewed_enter(
                zones,life,permanent_id,catalog,
                choice=selected,death_engine=death_engine,turn=turn)
        return UnearthOutcome(old_id,permanent_id,source.card.name,
                              paid.source_ids,enter_result=result)
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
