"""Typed source-paid graveyard spells using one physical transfer executor.

A declarative rule pins the printed Oracle text/cost and selects legal physical
graveyard targets. Effects are composed from the existing spell-cast, graveyard
transfer, library-draw and sacrifice/death primitives. This bounded adapter
does not authorize flashback, opponent priority or hidden replacement rules.
"""
from dataclasses import dataclass

from .generic_cast import ReviewedCreatureCast, cast_reviewed_spell
from .graveyard_recipes import (
    GraveyardRecipe, eligible_graveyard_cards, resolve_graveyard_recipe,
    select_bounded_graveyard_batch)
from .physical_common_effects import CardQuantity, draw_physical_cards
from .reviewed_death_effects import capture_battlefield


@dataclass(frozen=True)
class GraveyardSpellRule:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    destination: str
    ownership: str
    allowed_types_any: frozenset[str]
    target_count: int = 1
    controller_on_entry: str = "owner"
    enter_tapped: bool = False
    conditional_draw_subtype: str = ""
    sacrifice_creature: bool = False
    shuffle_source_into_library: bool = False
    limitations: tuple[str,...] = ()

    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text or not self.mana_cost
                or not isinstance(self.allowed_types_any,frozenset)
                or not self.allowed_types_any
                or type(self.target_count) is not int
                or not 1<=self.target_count<=2
                or type(self.sacrifice_creature) is not bool
                or type(self.shuffle_source_into_library) is not bool
                or type(self.enter_tapped) is not bool
                or self.destination not in {"hand","battlefield"}):
            raise ValueError("Invalid source-pinned graveyard spell recipe")
        self.target_recipe()

    def target_recipe(self):
        return GraveyardRecipe(
            self.destination,self.ownership,self.allowed_types_any,
            controller_on_entry=self.controller_on_entry,
            enter_tapped=self.enter_tapped)


RULES={
    "Cemetery Recruitment":GraveyardSpellRule(
        "07792d72-d5db-41b9-871c-e720e12ce659",
        "Return target creature card from your graveyard to your hand. If it's a Zombie card, draw a card.",
        "{1}{B}","hand","own",frozenset({"creature"}),
        conditional_draw_subtype="Zombie"),
    "Dread Return":GraveyardSpellRule(
        "352b64d2-2ae5-44ee-a64f-94932ef545d3",
        "Return target creature card from your graveyard to the battlefield.\nFlashback—Sacrifice three creatures. (You may cast this card from your graveyard for its flashback cost. Then exile it.)",
        "{2}{B}{B}","battlefield","own",frozenset({"creature"}),
        limitations=("Sacrifice-three-creatures flashback alternate-cost permission unavailable",)),
    "Beacon of Unrest":GraveyardSpellRule(
        "aef874fa-93c0-4f86-8b0d-dc24ec51467d",
        "Put target artifact or creature card from a graveyard onto the battlefield under your control. Shuffle Beacon of Unrest into its owner's library.",
        "{3}{B}{B}","battlefield","any",frozenset({"artifact","creature"}),
        controller_on_entry="actor",shuffle_source_into_library=True),
    "Victimize":GraveyardSpellRule(
        "240e85d3-e495-4877-8609-4b4056c402f7",
        "Choose two target creature cards in your graveyard. Sacrifice a creature. If you do, return the chosen cards to the battlefield tapped.",
        "{2}{B}","battlefield","own",frozenset({"creature"}),
        target_count=2,enter_tapped=True,sacrifice_creature=True),
}


def reviewed_graveyard_spell(name,raw):
    rule=RULES.get(name)
    return (rule if (rule is not None and isinstance(raw,dict)
        and raw.get("layout")=="normal"
        and raw.get("oracle_id")==rule.oracle_id
        and raw.get("oracle_text")==rule.oracle_text
        and raw.get("mana_cost")==rule.mana_cost
        and raw.get("type_line")=="Sorcery") else None)


@dataclass(frozen=True)
class GraveyardSpellOutcome:
    card_name: str
    source_stack_id: int
    source_resolved_id: int
    target_ids: tuple[int,...]
    moved_ids: tuple[int,...]
    sacrificed_old_id: int | None
    paid_source_ids: tuple[int,...]
    drawn_ids: tuple[int,...]
    limitations: tuple[str,...]


def choose_graveyard_spell_targets(zones, seat, rule, catalog):
    """Pure bounded policy: highest verified CMC legal targets, stable IDs."""
    if not isinstance(rule,GraveyardSpellRule):
        raise TypeError("Expected graveyard spell descriptor")
    selected=select_bounded_graveyard_batch(
        zones,seat,rule.target_recipe(),catalog,
        max_count=rule.target_count)
    return selected if len(selected)==rule.target_count else ()


def _eligible_victims(zones,seat):
    return tuple(o.object_id for o in zones.kernel.on_battlefield()
                 if o.controller==seat and "creature" in o.types
                 and "commander" not in o.card.supertypes)


def cast_reviewed_graveyard_spell(
        zones,life,seat,source_id,catalog,colors,mana_service, *,
        target_ids, sacrifice_id=None, death_engine=None, turn=1,
        on_cast=None):
    """Pay, cast, and resolve a pinned spell using actual target IDs.

    Targets and mandatory sacrifice permissions are established before mana
    commitment. The existing kernel supplies zones/object IDs and triggers;
    this bounded host does not implement opponent stack responses.
    """
    if source_id not in zones.ids(seat,"hand"):
        raise ValueError("Graveyard spell source must be in hand")
    source=zones.kernel.get(source_id)
    rule=reviewed_graveyard_spell(source.card.name,catalog.get(source.card.name))
    if (rule is None or source.card.card_id!=rule.oracle_id
            or source.types!=frozenset({"sorcery"})):
        raise ValueError("Unreviewed graveyard spell identity or type")
    if (life.kernel is not zones.kernel
            or mana_service.kernel is not zones.kernel):
        raise ValueError("Source-paid graveyard spell requires one kernel")
    if on_cast is not None and not callable(on_cast):
        raise TypeError("Cast event callback must be callable")
    targets=tuple(target_ids)
    if (len(targets)!=rule.target_count
            or len(set(targets))!=rule.target_count):
        raise ValueError("Incorrect number of graveyard spell targets")
    legal=set(eligible_graveyard_cards(zones,seat,rule.target_recipe()))
    if not set(targets)<=legal:
        raise ValueError("Illegal printed graveyard target")
    if rule.sacrifice_creature:
        if sacrifice_id not in _eligible_victims(zones,seat):
            return None
    elif sacrifice_id is not None:
        raise ValueError("Unexpected creature sacrifice target")
    if rule.conditional_draw_subtype:
        must_draw=any(rule.conditional_draw_subtype in
                      zones.kernel.get(oid).subtypes for oid in targets)
        if must_draw and not zones.ids(seat,"library"):
            return None
    cost=ReviewedCreatureCast(rule.oracle_id,rule.mana_cost,True,
                              rule.limitations)
    commit=cast_reviewed_spell(
        zones,seat,source_id,cost,colors,
        mana_service=mana_service,spell_type="sorcery")
    if commit is None:
        return None
    if on_cast is not None:
        on_cast(commit.ticket)
    affected=[]
    drawn=[]
    before=capture_battlefield(zones.kernel)
    move_index=len(zones.kernel.moves)

    def apply(kernel,ticket):
        if rule.sacrifice_creature:
            zones.move(sacrifice_id,"graveyard","sacrifice")
        selected=resolve_graveyard_recipe(
            zones,seat,targets,rule.target_recipe())
        affected.extend(item.new_id for item in selected)
        if rule.conditional_draw_subtype:
            chosen_names=tuple(
                kernel.get(oid).card.name for oid in affected)
            if any(rule.conditional_draw_subtype in
                   kernel.get(oid).subtypes for oid in affected):
                result=draw_physical_cards(zones,seat,CardQuantity(1))
                if not result.complete:
                    raise AssertionError("Verified conditional draw became unavailable")
                drawn.extend(result.drawn_ids)

    resolved=zones.resolve(commit.ticket,effect=apply)
    if rule.shuffle_source_into_library:
        resolved=zones.move(resolved,"library","resolve")
        zones.shuffle(source.owner)
    if death_engine is not None and rule.sacrifice_creature:
        death_engine.resolve_deaths(before,move_index=move_index,turn=turn)
    return GraveyardSpellOutcome(
        source.card.name,commit.ticket.object_id,resolved,targets,
        tuple(affected),sacrifice_id,tuple(commit.paid_source_ids),
        tuple(drawn),rule.limitations)
