"""Reviewed graveyard flashback using the same physical stack, payment and effects.

All supported spells have one typed alternative-cost permission and reuse
existing token/draw/discard operations. Countering an active flashback stack
object exiles it via IndexedKernel replacement rather than incorrectly
returning it to the graveyard. Other permission sources and copied spells
still require independent stack review.
"""
from dataclasses import dataclass

from .ability_composition import (
    AbilitySlot,AbilityHandler,ComposedCard,AbilityDispatcher)
from .physical_common_effects import CardQuantity,draw_physical_cards
from .reviewed_token_spells import (
    reviewed_token_spell,create_reviewed_token_batches)


@dataclass(frozen=True)
class FlashbackReview:
    oracle_id: str
    excerpt: str
    alternate_cost: str
    operation: str

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt or not self.alternate_cost
                or self.operation not in {"token_batches","draw_discard_two"}):
            raise ValueError("Invalid reviewed flashback declaration")


FLASHBACK={
    "Strike It Rich":FlashbackReview(
        "c34c17c7-3827-49a2-be25-67f44fdfe150",
        "Flashback {2}{R}","{2}{R}","token_batches"),
    "Moan of the Unhallowed":FlashbackReview(
        "ce87e5ed-2562-4563-9a5b-bd53c04ec4a5",
        "Flashback {5}{B}{B}","{5}{B}{B}","token_batches"),
    "Army of the Damned":FlashbackReview(
        "75d667ec-86f4-4850-a3b6-e7a9fc7053b0",
        "Flashback {7}{B}{B}{B}","{7}{B}{B}{B}","token_batches"),
    "Faithless Looting":FlashbackReview(
        "3d6fa57a-aa53-4b5c-b8af-a7612c823117",
        "Flashback {2}{R}","{2}{R}","draw_discard_two"),
}


def reviewed_flashback(name,metadata):
    review=FLASHBACK.get(name)
    if (review is None or not isinstance(metadata,dict)
            or metadata.get("oracle_id")!=review.oracle_id
            or metadata.get("type_line")!="Sorcery"
            or metadata.get("layout")!="normal"
            or review.excerpt not in metadata.get("oracle_text","")):
        return None
    if review.operation=="token_batches" and reviewed_token_spell(name,metadata) is None:
        return None
    if review.operation=="draw_discard_two" and (
            "Draw two cards, then discard two cards." not in metadata["oracle_text"]):
        return None
    return review


@dataclass(frozen=True)
class FlashbackResult:
    source_old_id: int
    stack_id: int
    exiled_id: int
    card_name: str
    mana_source_ids: tuple[int,...]
    created_token_ids: tuple[int,...]
    drawn_ids: tuple[int,...]
    discarded_old_ids: tuple[int,...]


def cast_reviewed_flashback(zones,seat,source_id,catalog,mana_service,*,
                            sorcery_window=False,on_cast=None,
                            discard_choice=None):
    """Pay alternate cost, physically cast from graveyard, resolve to exile."""
    if sorcery_window is not True:
        raise ValueError("Flashback sorcery window not verified")
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid flashback caster seat")
    if source_id not in zones.ids(seat,"graveyard"):
        raise ValueError("Flashback source must be a graveyard card")
    source=zones.kernel.get(source_id)
    metadata=catalog.get(source.card.name)
    review=reviewed_flashback(source.card.name,metadata)
    if (review is None or source.card.card_id!=review.oracle_id
            or source.owner!=seat or source.types!=frozenset({"sorcery"})):
        raise ValueError("Unreviewed flashback permission/source identity")
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("Matching physical mana source service required")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("Cast-trigger host callback must be callable")
    if discard_choice is not None and not callable(discard_choice):
        raise TypeError("Discard choice must be a host policy")
    if review.operation=="draw_discard_two" and len(zones.ids(seat,"library"))<2:
        raise NotImplementedError("Empty-library draw loss requires full host")
    plan=mana_service.plan_spell(seat,review.alternate_cost,source)
    if plan is None:
        return None
    slot=AbilitySlot(review.oracle_id,"front","flashback","keyword",
        review,review.excerpt,"pinned-oracle-m1",
        frozenset({"graveyard_cast","paid_mana","stack_exile_replacement"}))
    card=ComposedCard(review.oracle_id,metadata["oracle_text"],(slot,),
        (AbilityHandler(slot.key,"exact",review,slot.source_revision,
                        slot.prereqs),))
    dispatcher=AbilityDispatcher(card,"strict",slot.prereqs)
    def apply(operation):
        payment=mana_service.pay_spell(seat,operation.alternate_cost,source)
        if payment is None:
            raise AssertionError("Flashback payment preview changed")
        ticket=zones.cast(seat,source_id,reviewed_origin="graveyard",
                          exile_on_stack_exit=True)
        if on_cast is not None:
            on_cast(ticket)
        produced=[]
        drawn=[]
        discarded=[]
        def resolve(kernel,ticket):
            if operation.operation=="token_batches":
                recipe=reviewed_token_spell(source.card.name,metadata)
                produced.extend(create_reviewed_token_batches(
                    zones,seat,recipe.batches))
            elif operation.operation=="draw_discard_two":
                answer=draw_physical_cards(zones,seat,CardQuantity(2))
                if not answer.complete:
                    raise AssertionError("Flashback library preview changed")
                drawn.extend(answer.drawn_ids)
                choice=(tuple(drawn) if discard_choice is None else
                        tuple(discard_choice(zones,seat,tuple(drawn))))
                if (len(choice)!=2 or len(set(choice))!=2
                        or any(oid not in zones.ids(seat,"hand") for oid in choice)):
                    raise ValueError("Illegal reviewed discard choice")
                for oid in choice:
                    zones.discard(seat,oid)
                    discarded.append(oid)
            else:
                raise NotImplementedError("Unsupported flashback effect")
        exiled=zones.resolve(ticket,effect=resolve,spell_destination="exile")
        if zones.kernel.get(exiled).zone!="exile":
            raise AssertionError("Flashback did not exile resolved card")
        return FlashbackResult(source_id,ticket.object_id,exiled,
            source.card.name,payment.source_ids,tuple(produced),
            tuple(drawn),tuple(discarded))
    return dispatcher.invoke(slot.slot_id,source_id,apply)
