"""Execute small source-inferred spell recipes on the real physical kernel.

The importer authorizes only exact self-contained printed sentences; no
unreviewed targets, optional modes or additional costs are invented.
"""
from dataclasses import dataclass

from .generic_cast import ReviewedCreatureCast, cast_reviewed_spell
from .physical_common_effects import CardQuantity, draw_physical_cards
from .reviewed_token_spells import TokenBlueprint,create_reviewed_token_batches
from .provisional_import import provisional_profile
from .library_actions import (resolve_library_actions,
    required_library_cards_for_draws, LibraryAction)


@dataclass(frozen=True)
class ProvisionalSpellOutcome:
    name: str
    operation: str
    count: int
    drawn_ids: tuple[int,...]
    created_token_ids: tuple[int,...]
    paid_source_ids: tuple[int,...]
    resolved_zone_id: int
    fidelity: str = "provisional_partial"
    library_steps: tuple[dict, ...] = ()
    discarded_ids: tuple[int, ...] = ()
    surveilled_ids: tuple[int, ...] = ()
    bottomed_ids: tuple[int, ...] = ()
    returned_ids: tuple[int, ...] = ()


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
    draw_need = (required_library_cards_for_draws(profile.library_actions)
                 if profile.library_actions else
                 profile.amount if profile.mode in {"draw","draw_lose"} else 0)
    if len(zones.ids(seat,"library")) < draw_need:
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
    created=[]
    library_outcomes=[]
    def apply_effect(kernel,ticket):
        if profile.library_actions or profile.mode in {"draw","draw_lose"}:
            actions = profile.library_actions or (LibraryAction("draw",profile.amount),)
            library_outcome=resolve_library_actions(zones,seat,actions)
            library_outcomes.append(library_outcome)
            drawn.extend(library_outcome.drawn_ids)
        if profile.mode=="draw_lose":
            life.lose(seat,profile.life_amount,object_id)
        elif profile.mode=="create_creature_tokens":
            tokens=TokenBlueprint(
                profile.token_subtype,frozenset({"creature"}),
                frozenset({profile.token_subtype}),
                frozenset({profile.token_color}) if profile.token_color else frozenset(),
                profile.token_power,profile.token_toughness,
                profile.amount,profile.token_tapped)
            created.extend(create_reviewed_token_batches(zones,seat,(tokens,)))
        elif profile.mode=="gain_life":
            life.gain(seat,profile.amount,object_id)
        elif profile.mode=="opponent_loss":
            life.each_opponent_loses(seat,profile.amount,object_id)
    resolved=zones.resolve(commit.ticket,effect=apply_effect)
    library = library_outcomes[0] if library_outcomes else None
    return ProvisionalSpellOutcome(
        obj.card.name,profile.mode,profile.amount,tuple(drawn),
        tuple(created),tuple(commit.paid_source_ids),resolved,
        library_steps=library.steps if library else (),
        discarded_ids=library.discarded_ids if library else (),
        surveilled_ids=library.milled_ids if library else (),
        bottomed_ids=library.bottomed_ids if library else (),
        returned_ids=library.returned_ids if library else ())
