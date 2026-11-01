"""Source-paid, already-reviewed tutor casts in the bounded physical kernel.

This is a reusable one-seat main-phase adapter, not priority/permission
coverage for an arbitrary spell. Only pinned normal instant/sorcery tutors
are admitted. Physical hand -> stack -> graveyard and target library moves
use the existing LiveZones and TemplateManaService, without mirrored state.
"""
from dataclasses import dataclass

from .effect_templates import tutor_matches
from .generic_cast import ReviewedCreatureCast, cast_reviewed_spell
from .reviewed_tutors import reviewed_tutor
from .template_search import execute_reviewed_search_to_destination


@dataclass(frozen=True)
class ReviewedTutorCast:
    source_name: str
    source_stack_id: int
    source_graveyard_id: int
    target_name: str
    target_old_id: int
    target_new_id: int
    target_destination: str
    paid_source_ids: tuple[int, ...]


def eligible_reviewed_tutor_targets(zones, seat, name, catalog):
    """Conservative pre-cast screen; effect is revalidated at resolution."""
    row=catalog.get(name)
    if row is None:
        return ()
    found=reviewed_tutor(name,row)
    if found is None:
        return ()
    template, _, kind=found
    if kind not in {"instant","sorcery"} or template.destination not in {
        "hand","library_top"}:
        return ()
    return tuple(oid for oid in zones.ids(seat,"library")
                 if (zones.kernel.get(oid).card.name in catalog
                     and tutor_matches(template,catalog[zones.kernel.get(oid).card.name])))


def cast_and_resolve_reviewed_tutor(zones, seat, source_id, catalog,
                                    commander_colors, mana_service, *,
                                    target_id, on_cast=None):
    """Commit a source-paid, main-phase-permitted reviewed tutor and search.

    Target is selected from actual live library IDs *before* payment.
    A rejected source/target causes no tap, cast, shuffle or zone mutation.
    The caller must enforce its own turn/priority window; this function
    does not grant instant timing, other spells, or target policies.
    """
    if source_id not in zones.ids(seat,"hand"):
        raise ValueError("Tutor must be in actor's physical hand")
    source=zones.kernel.get(source_id)
    card=catalog.get(source.card.name)
    if card is None or card.get("oracle_id")!=source.card.card_id:
        raise ValueError("Tutor source Oracle identity is not reviewed")
    found=reviewed_tutor(source.card.name,card)
    if found is None:
        raise ValueError("Tutor text/cost is not reviewed")
    template, mana_cost, kind=found
    if kind not in {"instant","sorcery"} or source.card.types!=frozenset({kind}):
        raise ValueError("Reviewed sorcery/instant tutor source required")
    valid=eligible_reviewed_tutor_targets(zones,seat,source.card.name,catalog)
    if type(target_id) is not int or target_id not in valid:
        raise ValueError("Tutor target is not eligible")
    if mana_service is None or mana_service.kernel is not zones.kernel:
        raise ValueError("A physical, matching mana service is required")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("Reviewed cast-event hook must be callable")
    review=ReviewedCreatureCast(source.card.card_id,mana_cost,True,
        ("Only the verified library-search effect is resolved",))
    committed=cast_reviewed_spell(zones,seat,source_id,review,commander_colors,
                                  mana_service=mana_service,spell_type=kind)
    if committed is None:
        return None
    if on_cast is not None:
        on_cast(committed.ticket)
    outcomes=[]
    def apply(kernel,ticket):
        outcomes.append(execute_reviewed_search_to_destination(
            zones,seat,ticket.object_id,target_id,catalog))
    graveyard_id=zones.resolve(committed.ticket,effect=apply)
    if len(outcomes)!=1:
        raise AssertionError("Tutor search must resolve exactly once")
    result=outcomes[0]
    return ReviewedTutorCast(source.card.name,committed.ticket.object_id,
                             graveyard_id,result.target_name,
                             result.target_old_id,result.target_new_id,
                             result.destination,committed.paid_source_ids)
