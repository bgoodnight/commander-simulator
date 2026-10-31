"""Narrow M2 ordinary-creature cast path on the EXISTING authoritative zones.

This is not a general caster or multi-deck pilot. A human-reviewed card
declaration must establish that the creature has no unmodeled effects that
matter at entry/cast. The host turn driver retains timing, priority, trigger,
and resolution responsibility. This action pays from real land object IDs.
"""
from dataclasses import dataclass

from .mana_kernel_bridge import plan_live_basic_payment
from .mana_costs import parse_fixed_mana_cost


@dataclass(frozen=True)
class ReviewedCreatureCast:
    card_id: str
    mana_cost: str
    # This assertion must come from a reviewed rules definition, never from
    # Scryfall type, a strategy role tag, or the mere presence of metadata.
    entry_and_cast_safe: bool = False
    unresolved_later_abilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommittedCreatureCast:
    ticket: object
    paid_source_ids: tuple[int, ...]
    unresolved_later_abilities: tuple[str, ...]


def cast_reviewed_creature(zones, seat, object_id, review, commander_colors):
    """Pay and put one reviewed ordinary creature on the live stack.

    All validation occurs before mutation. Spell resolution and priority are
    delegated to the current zones/stack driver. All selected mana sources
    must be currently controlled, untapped physical lands in this same kernel.
    Failure leaves the authoritative zones and sources unchanged.
    """
    if not isinstance(review, ReviewedCreatureCast) or not review.entry_and_cast_safe:
        raise ValueError('Missing reviewed entry/cast safety declaration')
    if not review.card_id or not review.mana_cost:
        raise ValueError('Incomplete reviewed creature declaration')
    if type(seat) is not int or not 0 <= seat < 4:
        raise ValueError('Invalid actor seat')
    if object_id not in zones.ids(seat, 'hand'):
        raise ValueError('Spell is not in the actor hand')
    kernel = zones.kernel
    obj = kernel.get(object_id)
    card = obj.card
    if (obj.owner != seat or obj.controller != seat or obj.zone != 'hand'
            or card.card_id != review.card_id or card.coverage == 'unimplemented'
            or card.types != frozenset({'creature'})):
        raise ValueError('Not a reviewed ordinary creature')
    # The reviewed declaration is the actual printed cost, while the kernel
    # definition remains responsible for characteristics and safe effects.
    parse_fixed_mana_cost(review.mana_cost)
    payment = plan_live_basic_payment(kernel, seat, review.mana_cost, commander_colors)
    if payment is None:
        return None
    # Revalidate every object before payment. Single-threaded execution is
    # assumed; no callback occurs between revalidation, payment and cast.
    for oid in payment.source_ids:
        source = kernel.get(oid)
        if (source.controller != seat or source.zone != 'battlefield'
                or source.tapped or 'land' not in source.types):
            raise ValueError('Stale source payment')
    for oid in payment.source_ids:
        kernel.get(oid).tapped = True
    kernel._dirty()
    try:
        ticket = zones.cast(seat, object_id)
    except Exception:
        # The preflight checks above should prevent cast rejection. On an
        # unexpected failure restore source taps; never report a paid cast.
        for oid in payment.source_ids:
            kernel.get(oid).tapped = False
        kernel._dirty()
        raise
    return CommittedCreatureCast(ticket, payment.source_ids,
                                 review.unresolved_later_abilities)
