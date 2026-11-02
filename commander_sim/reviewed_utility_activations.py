"""Shared activated utility templates for lands, rocks and graveyard sources.

Profiles declare source zone, mana/tap/life/additional costs, conditions and
destination effects. Exactly the same executor serves War Room, Barren Moor,
Leechridden Swamp, Mind Stone, Reassembling Skeleton, Phyrexian Reclamation.
It does not infer arbitrary Oracle abilities from names or type lines.
"""
from dataclasses import dataclass
from .physical_common_effects import CardQuantity, draw_physical_cards
from .reviewed_death_effects import capture_battlefield
from .graveyard_recipes import GraveyardRecipe, resolve_graveyard_recipe

@dataclass(frozen=True)
class UtilityRule:
    oracle_id: str
    excerpt: str
    source_zone: str
    mana: str
    operation: str
    tap: bool = False
    sacrifice: bool = False
    discard: bool = False
    life: int = 0
    life_by_commander_colors: bool = False
    condition: str = "always"
    target_subtypes: frozenset[str] = frozenset()
    target_supertypes: frozenset[str] = frozenset()
    tap_creature: bool = False

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt
                or self.source_zone not in {"battlefield","hand","graveyard"}
                or self.operation not in {"draw","drain_opponents",
                    "creature_to_hand","self_to_battlefield_tapped",
                    "all_legendary_creatures_to_hand"}
                or self.condition not in {"always","two_black_permanents"}
                or not isinstance(self.target_subtypes,frozenset)
                or not isinstance(self.target_supertypes,frozenset)
                or any(not isinstance(x,str) or not x
                       for x in self.target_subtypes | self.target_supertypes)
                or type(self.tap_creature) is not bool
                or self.tap_creature and not self.tap
                or self.target_subtypes and self.operation!="creature_to_hand"
                or self.target_supertypes and self.operation not in {
                    "creature_to_hand","all_legendary_creatures_to_hand"}
                or self.source_zone=="graveyard" and any(
                    (self.tap,self.sacrifice,self.discard))
                or (self.sacrifice and self.discard)):
            raise ValueError("Invalid reviewed utility activation")


RULES={
    "War Room":UtilityRule(
        "71c52bf5-2a5d-488e-8b15-7ef290e4b77d",
        "{3}, {T}, Pay life equal to the number of colors in your commanders' color identity: Draw a card.",
        "battlefield","{3}","draw",tap=True,life_by_commander_colors=True),
    "Leechridden Swamp":UtilityRule(
        "d83c86c1-126d-49e9-9b13-9e55784c49c5",
        "{B}, {T}: Each opponent loses 1 life. Activate only if you control two or more black permanents.",
        "battlefield","{B}","drain_opponents",tap=True,condition="two_black_permanents"),
    "Mind Stone":UtilityRule(
        "c97361b5-af16-4a7b-af85-a429dbaf4ad2",
        "{1}, {T}, Sacrifice this artifact: Draw a card.",
        "battlefield","{1}","draw",tap=True,sacrifice=True),
    "Barren Moor":UtilityRule(
        "326ba371-124c-4949-a048-3a0c8962e567",
        "Cycling {B} ({B}, Discard this card: Draw a card.)",
        "hand","{B}","draw",discard=True),
    "Persistent Specimen":UtilityRule(
        "5f4ad578-f2c4-47f6-8080-8fbc17383f6f",
        "{2}{B}: Return this card from your graveyard to the battlefield tapped.",
        "graveyard","{2}{B}","self_to_battlefield_tapped"),
    "Lord of the Undead":UtilityRule(
        "7714af0e-41d9-4609-967f-27233b46055f",
        "{1}{B}, {T}: Return target Zombie card from your graveyard to your hand.",
        "battlefield","{1}{B}","creature_to_hand",tap=True,
        tap_creature=True,target_subtypes=frozenset({"Zombie"})),
    "Memorial to Folly":UtilityRule(
        "2bc38f14-0314-4351-8138-e2b8bf041404",
        "{2}{B}, {T}, Sacrifice this land: Return target creature card from your graveyard to your hand.",
        "battlefield","{2}{B}","creature_to_hand",tap=True,sacrifice=True),
    "Lychguard":UtilityRule(
        "e82daa7b-d9fd-48c4-b5b2-f3b1f6ef1a24",
        "{3}{B}, Sacrifice this creature: Return all legendary creature cards from your graveyard to your hand.",
        "battlefield","{3}{B}","all_legendary_creatures_to_hand",
        sacrifice=True,target_supertypes=frozenset({"legendary"})),
    "Reassembling Skeleton":UtilityRule(
        "9dbc3530-b278-4c8d-b2cc-a09dfac9d5e5",
        "{1}{B}: Return this card from your graveyard to the battlefield tapped.",
        "graveyard","{1}{B}","self_to_battlefield_tapped"),
    "Phyrexian Reclamation":UtilityRule(
        "647ca69e-cc01-4b2b-b376-bee2a98331e8",
        "{1}{B}, Pay 2 life: Return target creature card from your graveyard to your hand.",
        "battlefield","{1}{B}","creature_to_hand",life=2),
}


def reviewed_utility(name,raw):
    rule=RULES.get(name)
    if (rule is None or not isinstance(raw,dict)
            or raw.get("oracle_id")!=rule.oracle_id
            or rule.excerpt not in raw.get("oracle_text","")):
        return None
    return rule


@dataclass(frozen=True)
class UtilityOutcome:
    source_name: str
    operation: str
    new_object_ids: tuple[int,...]
    life_paid: int
    paid_source_ids: tuple[int,...]


def activate_utility(zones,life,seat,source_id,catalog,mana_service,colors,
                     *,target_id=None,death_engine=None,turn=1,
                     tap_ready=False):
    kernel=zones.kernel
    if life.kernel is not kernel or mana_service.kernel is not kernel:
        raise ValueError("Utility source and payment hosts must match")
    source=kernel.get(source_id)
    rule=reviewed_utility(source.card.name,catalog.get(source.card.name))
    if (rule is None or source.card.card_id!=rule.oracle_id
            or source.controller!=seat or source.zone!=rule.source_zone
            or rule.tap and source.tapped):
        raise ValueError("Unreviewed or unavailable utility activation")
    # Creature tap abilities require the turn driver to verify summoning
    # sickness. Noncreature mana rocks/lands do not use this authorization.
    if rule.tap_creature and (not "creature" in source.types
                              or tap_ready is not True):
        return None
    if rule.condition=="two_black_permanents":
        count=sum("B" in (obj.card.colors or ())
                  for obj in kernel.on_battlefield() if obj.controller==seat)
        if count<2:
            return None
    if rule.operation=="creature_to_hand":
        if target_id not in zones.ids(seat,"graveyard"):
            return None
        target=kernel.get(target_id)
        if ("creature" not in target.types
                or not rule.target_subtypes<=target.subtypes
                or not rule.target_supertypes<=target.card.supertypes):
            raise ValueError("Graveyard target does not meet printed restrictions")
    elif target_id is not None:
        raise ValueError("Unexpected utility target")
    if rule.operation=="all_legendary_creatures_to_hand":
        # A non-targeting 'all' effect has no optional target chosen at cast.
        # Collect before payment, and include all eligible owned cards.
        recipe=GraveyardRecipe("hand","own",frozenset({"creature"}),
             required_supertypes=rule.target_supertypes)
        from .graveyard_recipes import eligible_graveyard_cards
        batch=eligible_graveyard_cards(zones,seat,recipe)
    else:
        batch=()
    if rule.operation=="draw" and not zones.ids(seat,"library"):
        return None
    life_cost=len(colors) if rule.life_by_commander_colors else rule.life
    if life.total(seat)<=life_cost:
        return None
    excluded=(source_id,) if rule.tap else ()
    preview=mana_service.plan(seat,rule.mana,excluded_source_ids=excluded)
    if preview is None:
        return None
    before=capture_battlefield(kernel)
    move_index=len(kernel.moves)
    paid=mana_service.pay(seat,rule.mana,excluded_source_ids=excluded)
    if paid is None:
        raise AssertionError("Reviewed utility payment changed")
    if rule.tap:
        source.tapped=True
        kernel._dirty()
    if life_cost:
        life.lose(seat,life_cost,source_id)
    moved=[]
    if rule.sacrifice:
        moved.append(zones.move(source_id,"graveyard","sacrifice"))
        if death_engine is not None:
            death_engine.resolve_deaths(before,move_index=move_index,turn=turn)
    if rule.discard:
        moved.append(zones.discard(seat,source_id))
    if rule.operation=="draw":
        out=draw_physical_cards(zones,seat,CardQuantity(1))
        if not out.complete:
            raise AssertionError("Reviewed utility draw preview invalidated")
        moved.extend(out.drawn_ids)
    elif rule.operation=="drain_opponents":
        life.each_opponent_loses(seat,1,source_id)
    elif rule.operation=="creature_to_hand":
        restored=resolve_graveyard_recipe(
            zones,seat,(target_id,),
            GraveyardRecipe("hand","own",frozenset({"creature"}),
                            required_subtypes=rule.target_subtypes,
                            required_supertypes=rule.target_supertypes))
        moved.extend(item.new_id for item in restored)
    elif rule.operation=="all_legendary_creatures_to_hand":
        restored=resolve_graveyard_recipe(
            zones,seat,batch,
            GraveyardRecipe("hand","own",frozenset({"creature"}),
                            required_supertypes=rule.target_supertypes))
        moved.extend(item.new_id for item in restored)
    elif rule.operation=="self_to_battlefield_tapped":
        restored=resolve_graveyard_recipe(
            zones,seat,(source_id,),
            GraveyardRecipe("battlefield","own",frozenset({"creature"}),
                            enter_tapped=True))
        moved.extend(item.new_id for item in restored)
    return UtilityOutcome(source.card.name,rule.operation,tuple(moved),
                          life_cost,tuple(paid.source_ids))
