"""Physical escape granted by an Oracle-pinned Underworld Breach.

Escape is a permission and an additional exile cost, not a predefined combo.
Only independently reviewed *effects* may resolve in the bounded runner.
The reusable cost/permission layer can serve other supported nonland spells.
"""
from dataclasses import dataclass

from .reviewed_token_spells import reviewed_token_spell, create_reviewed_token_batches

BREACH_ORACLE="27e0948b-9916-473b-8d8c-a51bdfbc7457"
BREACH_TEXT=(
    "Each nonland card in your graveyard has escape. The escape cost is equal "
    "to the card's mana cost plus exile three other cards from your graveyard. "
    "(You may cast cards from your graveyard for their escape cost.)\n"
    "At the beginning of the end step, sacrifice this enchantment."
)


@dataclass(frozen=True)
class BreachReview:
    oracle_id:str
    oracle_text:str


BREACH_REVIEWS={"Underworld Breach":BreachReview(BREACH_ORACLE,BREACH_TEXT)}


def reviewed_breach(name,raw):
    """Exact pinned permission; only a verified normal enchantment may supply it."""
    return bool(name=="Underworld Breach" and isinstance(raw,dict)
        and raw.get("oracle_id")==BREACH_ORACLE
        and raw.get("oracle_text")==BREACH_TEXT
        and raw.get("mana_cost")=="{1}{R}"
        and raw.get("type_line")=="Enchantment"
        and raw.get("layout")=="normal")


def breach_sources(zones,seat,catalog):
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid player seat")
    return tuple(sorted(obj.object_id for obj in zones.kernel.objects.values()
        if obj.zone=="battlefield" and obj.controller==seat
        and obj.card.card_id==BREACH_ORACLE
        and reviewed_breach(obj.card.name,catalog.get(obj.card.name))))


def escape_candidates(zones,seat,source_id,catalog,mana_service):
    """Legal available exile fodder and cost preview; no state changes.

    Caller decides whether to exile available other cards; this never searches
    a library, fabricates cards, or treats casting a spell as its resolution.
    """
    if source_id not in zones.ids(seat,"graveyard"):
        return ()
    if not breach_sources(zones,seat,catalog):
        return ()
    source=zones.kernel.get(source_id)
    raw=catalog.get(source.card.name)
    if (source.owner!=seat or "land" in source.types
            or not isinstance(raw,dict)
            or source.card.card_id!=raw.get("oracle_id")):
        return ()
    fodder=tuple(i for i in zones.ids(seat,"graveyard") if i!=source_id)
    if len(fodder)<3:
        return ()
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("Required shared physical mana service")
    cost=raw.get("mana_cost")
    if not isinstance(cost,str) or not cost:
        return ()
    return fodder if mana_service.plan_spell(seat,cost,source) is not None else ()


@dataclass(frozen=True)
class EscapeCast:
    source_old_id:int
    stack_id:int
    graveyard_id:int
    exiled_other_ids:tuple[int,...]
    paid_source_ids:tuple[int,...]
    created_token_ids:tuple[int,...]
    card_name:str


def cast_reviewed_escape_token_spell(
        zones,seat,source_id,catalog,mana_service,*,exile_ids,
        sorcery_window=False,on_cast=None):
    """Source-pay and physically cast a reviewed token sorcery using escape.

    The spell returns to graveyard on resolution (unlike flashback); other
    exiled cards remain in exile. The caller's pilot chooses exactly three
    OTHER real graveyard cards to pay the additional escape cost.
    """
    if sorcery_window is not True:
        raise ValueError("Sorcery-speed permission is required")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("Cast notification must be callable")
    if type(exile_ids) not in (tuple,list) or len(exile_ids)!=3 or len(set(exile_ids))!=3:
        raise ValueError("Escape requires exactly three distinct other cards")
    source=zones.kernel.get(source_id)
    raw=catalog.get(source.card.name)
    review=reviewed_token_spell(source.card.name,raw)
    if (review is None or source.card.card_id!=review.oracle_id
            or source.types!=frozenset({"sorcery"})
            or source.card.coverage=="unimplemented"):
        raise ValueError("Unreviewed spell resolution cannot be escaped")
    available=escape_candidates(zones,seat,source_id,catalog,mana_service)
    if not available or not set(exile_ids)<=set(available):
        raise ValueError("Escape mana, permission or other-card costs unavailable")
    paid=mana_service.pay_spell(seat,review.mana_cost,source)
    if paid is None:
        raise AssertionError("Escape mana preview changed")
    for oid in exile_ids:
        zones.move(oid,"exile","resolve")
    ticket=zones.cast(seat,source_id,reviewed_origin="graveyard")
    if on_cast is not None:
        on_cast(ticket)
    created=[]
    def resolve(kernel,ticket):
        created.extend(create_reviewed_token_batches(zones,seat,review.batches))
    new_id=zones.resolve(ticket,effect=resolve)
    return EscapeCast(source_id,ticket.object_id,new_id,tuple(exile_ids),
                      paid.source_ids,tuple(created),source.card.name)


def sacrifice_breach_at_end_step(zones,seat,catalog):
    """Breach's mandatory end-step ability sacrifices all reviewed sources."""
    moved=[]
    for oid in breach_sources(zones,seat,catalog):
        if oid in zones.ids(seat,"battlefield"):
            new_id=zones.move(oid,"graveyard","sacrifice")
            moved.append((oid,new_id))
    return tuple(moved)
