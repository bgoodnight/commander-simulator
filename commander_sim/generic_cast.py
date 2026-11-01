"""Narrow, source-backed reviewed permanent casting on authoritative live zones.

The SAME physical-object casting path handles ordinary reviewed creatures
and mana rocks. Identity, timing/fidelity and mandatory effects are gated;
the caller still owns turn legality, priority, triggers and resolution.
"""
from dataclasses import dataclass

from .mana_kernel_bridge import plan_live_basic_payment
from .mana_costs import parse_fixed_mana_cost


@dataclass(frozen=True)
class ReviewedCreatureCast:
    card_id: str
    mana_cost: str
    entry_and_cast_safe: bool = False
    unresolved_later_abilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommittedCreatureCast:
    ticket: object
    paid_source_ids: tuple[int, ...]
    unresolved_later_abilities: tuple[str, ...]


def _cast_reviewed_card(zones, seat, object_id, review, commander_colors, *,
                        mana_service=None, card_type="creature"):
    """Commit a reviewed creature or artifact's cost and cast into SAME zones.

    For legacy basic-only calls there is no floating mana. With the optional
    reviewed template service, unused rock production stays in the kernel pool
    until that turn's main-phase boundary. No unreviewed printed abilities
    execute by entering the battlefield.
    """
    if card_type not in {"creature", "artifact", "enchantment", "instant", "sorcery"}:
        raise ValueError("Unreviewed spell/permanent type")
    if not isinstance(review, ReviewedCreatureCast) or not review.entry_and_cast_safe:
        raise ValueError("Missing reviewed entry/cast safety declaration")
    if not review.card_id or not review.mana_cost:
        raise ValueError("Incomplete reviewed permanent declaration")
    if type(seat) is not int or not 0 <= seat < 4:
        raise ValueError("Invalid actor seat")
    if object_id not in zones.ids(seat, "hand"):
        raise ValueError("Spell is not in actor hand")
    kernel = zones.kernel
    obj = kernel.get(object_id)
    card = obj.card
    if (obj.owner != seat or obj.controller != seat or obj.zone != "hand"
            or card.card_id != review.card_id or card.coverage == "unimplemented"
            or (card.types != frozenset({card_type}) if card_type in {"instant", "sorcery"}
                else card_type not in card.types or not card.types <= {"artifact", "creature", "enchantment"})):
        raise ValueError("Not an approved reviewed permanent")
    parse_fixed_mana_cost(review.mana_cost)
    if mana_service is not None and mana_service.kernel is not kernel:
        raise ValueError("Mana service must use SAME game kernel")
    if mana_service is None:
        preview = plan_live_basic_payment(kernel, seat, review.mana_cost, commander_colors)
        if preview is None:
            return None
        source_ids = preview.source_ids
        for oid in source_ids:
            source = kernel.get(oid)
            if (source.controller != seat or source.zone != "battlefield"
                    or source.tapped or "land" not in source.types):
                raise ValueError("Stale source payment")
        for oid in source_ids:
            kernel.get(oid).tapped = True
        kernel._dirty()
        old_pool = None
    else:
        previous = mana_service.plan(seat, review.mana_cost)
        if previous is None:
            return None
        old_pool = mana_service.floating(seat)
        paid = mana_service.pay(seat, review.mana_cost)
        source_ids = paid.source_ids
    try:
        ticket = zones.cast(seat, object_id)
    except Exception:
        # Any unexpected cast rejection must leave land taps and mana pool as
        # before the attempted spell (single-threaded synchronous host).
        for oid in source_ids:
            kernel.get(oid).tapped = False
        if mana_service is not None:
            kernel.mana_pools[seat] = old_pool
        kernel._dirty()
        raise
    return CommittedCreatureCast(ticket, source_ids,
                                 review.unresolved_later_abilities)


def cast_reviewed_permanent(zones, seat, object_id, review, commander_colors, *,
                            mana_service=None, permanent_type="creature"):
    """Backward-compatible permanent cast: does not resolve printed abilities."""
    if permanent_type not in {"creature", "artifact", "enchantment"}:
        raise ValueError("Expected an approved permanent type")
    return _cast_reviewed_card(
        zones, seat, object_id, review, commander_colors,
        mana_service=mana_service, card_type=permanent_type)


def cast_reviewed_spell(zones, seat, object_id, review, commander_colors, *,
                        mana_service=None, spell_type="sorcery"):
    """Pay, tap real sources and put one reviewed instant/sorcery on stack.

    Caller must still provide a separately reviewed effect when it resolves.
    No spell casts are authorized from card name or raw Oracle text.
    """
    if spell_type not in {"instant", "sorcery"}:
        raise ValueError("Expected instant or sorcery")
    return _cast_reviewed_card(
        zones, seat, object_id, review, commander_colors,
        mana_service=mana_service, card_type=spell_type)


def cast_reviewed_creature(zones, seat, object_id, review, commander_colors, *,
                           mana_service=None):
    """Backward-compatible creature API; rock-aware when service supplied."""
    return cast_reviewed_permanent(zones, seat, object_id, review,
                                    commander_colors, mana_service=mana_service,
                                    permanent_type="creature")
