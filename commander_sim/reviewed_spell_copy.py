"""Reviewed instant/sorcery copy effects on pending physical spell tickets.

A spell copy is not a second card and is never *cast*. Its effect resolves
separately and can trigger Magecraft, while the original remains pending.
This initial reviewed slice covers Reiterate copying an untargeted, pinned
token-producing spell. It does not pretend to model the general stack.
"""
from dataclasses import dataclass

from .mana_costs import FixedManaCost, parse_fixed_mana_cost
from .reviewed_cost_reduction import cost_symbols
from .reviewed_token_spells import reviewed_token_spell,create_reviewed_token_batches
from .reviewed_buyback import BuybackReview,buyback_total_cost

REITERATE=BuybackReview(
    "38394ee3-6726-4f91-bc25-36bce0c6aab9",
    "Buyback {3} (You may pay an additional {3} as you cast this spell. "
    "If you do, put this card into your hand as it resolves.)\n"
    "Copy target instant or sorcery spell. You may choose new targets for the copy.",
    "{1}{R}{R}",3,"copy_spell",
)
REVIEWED_COPY_SPELLS={"Reiterate":REITERATE}


def reviewed_copy_spell(name,raw):
    r=REVIEWED_COPY_SPELLS.get(name)
    if (r is None or not isinstance(raw,dict)
        or raw.get("oracle_id")!=r.oracle_id
        or raw.get("oracle_text")!=r.oracle_text
        or raw.get("mana_cost")!=r.mana_cost
        or raw.get("type_line")!="Instant"
        or raw.get("layout")!="normal"):
        return None
    return r


def verified_copy_target(zones,ticket,catalog):
    """Only an active reviewed untargeted spell may be copied by this slice."""
    if zones._pending.get(ticket.object_id)!=ticket:
        return None
    obj=zones.kernel.objects.get(ticket.object_id)
    if obj is None or obj.zone!="stack" or "sorcery" not in obj.types:
        return None
    raw=catalog.get(obj.card.name)
    review=reviewed_token_spell(obj.card.name,raw)
    if review is None or obj.card.card_id!=review.oracle_id:
        return None
    return review


@dataclass(frozen=True)
class CopyOutcome:
    copier_old_id:int
    copier_destination_id:int
    copier_destination:str
    copy_effect_source_id:int
    original_target_stack_id:int
    copied_card_name:str
    created_token_ids:tuple[int,...]
    mana_source_ids:tuple[int,...]
    bought_back:bool


def cast_reiterate_copy(zones,seat,copier_id,target_ticket,catalog,
                        mana_service,*,buyback=False,casting_window=False,
                        on_cast=None,on_copy=None):
    """Pay and cast real Reiterate; resolve one effect-level stack copy.

    The host supplies the correct priority/target window. This operation
    verifies both sources before payment, then resolves Reiterate (possibly
    to hand) while keeping its original target spell on the physical stack.
    Targeted or unknown spell effects must be handled by later rule modules.
    """
    if casting_window is not True or type(buyback) is not bool:
        raise ValueError("Reviewed instant timing and buyback choice required")
    if type(seat) is not int or not 0<=seat<zones.seats:
        raise ValueError("Invalid caster seat")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("Invalid cast callback")
    if on_copy is not None and not callable(on_copy):
        raise TypeError("Invalid copy callback")
    if copier_id not in zones.ids(seat,"hand"):
        raise ValueError("Reiterate must be in caster hand")
    source=zones.kernel.get(copier_id)
    if (source.owner!=seat or source.card.card_id!=REITERATE.oracle_id
        or source.types!=frozenset({"instant"})
        or source.card.coverage=="unimplemented"
        or reviewed_copy_spell(source.card.name,catalog.get(source.card.name)) is None):
        raise ValueError("Unsupported copy-spell source")
    target=verified_copy_target(zones,target_ticket,catalog)
    if target is None:
        raise ValueError("Target spell lacks a current verified copyable effect")
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("Mismatched physical mana service")
    cost=buyback_total_cost(REITERATE,buyback)
    if mana_service.plan_spell(seat,cost,source) is None:
        return None
    paid=mana_service.pay_spell(seat,cost,source)
    if paid is None:
        raise AssertionError("Copy-spell payment invalidated")
    ticket=zones.cast(seat,copier_id)
    if on_cast is not None:
        on_cast(ticket)
    created=[]
    original_name=zones.kernel.get(target_ticket.object_id).card.name
    def resolve(kernel,copy_ticket):
        # The target might no longer be present if a future host resolves
        # responses in this window. A copy never resurrects a missing target.
        if verified_copy_target(zones,target_ticket,catalog) is None:
            return
        from .early_game_runner import _load_live_kernel
        _load_live_kernel()
        from rules import Event
        kernel.events.append(Event(
            "spell_copied",seat,copy_ticket.object_id,
            target_id=target_ticket.object_id,
            spell_types=frozenset({"sorcery"}),
            metadata=(("original_spell_id",target_ticket.object_id),
                      ("copied_card_name",original_name))))
        if on_copy is not None:
            on_copy(target_ticket)
        created.extend(create_reviewed_token_batches(zones,seat,target.batches))
    destination="hand" if buyback else "graveyard"
    after=zones.resolve(ticket,effect=resolve,spell_destination=destination)
    return CopyOutcome(copier_id,after,destination,ticket.object_id,
        target_ticket.object_id,original_name,tuple(created),
        paid.source_ids,buyback)
