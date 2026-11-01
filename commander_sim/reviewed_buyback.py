"""Reviewed buyback costs resolve original spell to physical hand.

Buyback is an additional generic cost, not a second spell or a copied card.
This initial execution reviews only Whispers of the Muse's untargeted draw.
Other buyback spells need their own reviewed effects and target legality.
"""
from dataclasses import dataclass

from .mana_costs import FixedManaCost, parse_fixed_mana_cost
from .reviewed_cost_reduction import cost_symbols
from .physical_common_effects import CardQuantity, draw_physical_cards

@dataclass(frozen=True)
class BuybackReview:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    buyback_generic: int
    operation: str

BUYBACK = {
    "Whispers of the Muse": BuybackReview(
        "a4a8af4e-8686-45ba-94fd-ccf6cc8adaae",
        "Buyback {5} (You may pay an additional {5} as you cast this spell. "
        "If you do, put this card into your hand as it resolves.)\nDraw a card.",
        "{U}",5,"draw_one"),
}

def reviewed_buyback(name,raw):
    row=BUYBACK.get(name)
    if (row is None or not isinstance(raw,dict)
        or raw.get("oracle_id") != row.oracle_id
        or raw.get("oracle_text") != row.oracle_text
        or raw.get("mana_cost") != row.mana_cost
        or raw.get("type_line") != "Instant"
        or raw.get("layout") != "normal"):
        return None
    return row


def buyback_total_cost(review, paid_buyback):
    if not isinstance(review,BuybackReview) or type(paid_buyback) is not bool:
        raise ValueError("Reviewed buyback and explicit choice are required")
    base=parse_fixed_mana_cost(review.mana_cost)
    return cost_symbols(FixedManaCost(
        base.generic + (review.buyback_generic if paid_buyback else 0),
        base.colored))


@dataclass(frozen=True)
class BuybackOutcome:
    source_old_id: int
    stack_id: int
    destination_id: int
    destination: str
    bought_back: bool
    paid_source_ids: tuple[int,...]
    drawn_ids: tuple[int,...]
    card_name: str


def cast_reviewed_buyback(zones,seat,source_id,catalog,mana_service,*,
                           buyback=False,casting_window=False,on_cast=None):
    """Pay once, cast real card, resolve and return to hand iff buyback paid.

    A host supplies a legal instant-casting window, rather than this operation
    inventing priority or targets. A one-card library draw is prevalidated.
    """
    if casting_window is not True:
        raise ValueError("Valid instant casting window required")
    if type(buyback) is not bool:
        raise ValueError("Buyback selection must be Boolean")
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid seat")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("Cast hook must be callable")
    if source_id not in zones.ids(seat,"hand"):
        raise ValueError("Spell must originate in player's hand")
    source=zones.kernel.get(source_id)
    raw=catalog.get(source.card.name)
    row=reviewed_buyback(source.card.name,raw)
    if (row is None or source.card.card_id!=row.oracle_id
        or source.owner!=seat or source.types!=frozenset({"instant"})
        or source.card.coverage=="unimplemented"):
        raise ValueError("Unreviewed buyback spell")
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("Mana service and physical kernel must agree")
    if not zones.ids(seat,"library"):
        raise NotImplementedError("Full empty-library draw loss not yet modeled")
    cost=buyback_total_cost(row,buyback)
    if mana_service.plan_spell(seat,cost,source) is None:
        return None
    payment=mana_service.pay_spell(seat,cost,source)
    if payment is None:
        raise AssertionError("Buyback payment preview changed")
    ticket=zones.cast(seat,source_id)
    if on_cast is not None:
        on_cast(ticket)
    drawn=[]
    def resolve(kernel,ticket):
        result=draw_physical_cards(zones,seat,CardQuantity(1))
        if not result.complete:
            raise AssertionError("Reviewed draw failed after prevalidation")
        drawn.extend(result.drawn_ids)
    destination="hand" if buyback else "graveyard"
    moved=zones.resolve(ticket,effect=resolve,spell_destination=destination)
    return BuybackOutcome(
        source_id,ticket.object_id,moved,destination,buyback,
        payment.source_ids,tuple(drawn),source.card.name)
