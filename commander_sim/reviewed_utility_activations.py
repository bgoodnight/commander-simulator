"""Shared activated utility templates for lands, rocks and graveyard sources.

Profiles declare source zone, mana/tap/life/additional costs, conditions and
destination effects. Exactly the same executor serves War Room, Barren Moor,
Leechridden Swamp, Mind Stone, Reassembling Skeleton, Phyrexian Reclamation.
It does not infer arbitrary Oracle abilities from names or type lines.
"""
from dataclasses import dataclass
from .physical_common_effects import CardQuantity, draw_physical_cards
from .reviewed_death_effects import capture_battlefield
from .graveyard_recipes import (
    GraveyardRecipe,eligible_graveyard_cards,resolve_graveyard_recipe)
from .reviewed_token_spells import TokenBlueprint,create_reviewed_token_batches

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
    draw_count: int = 1
    life_loss_after: int = 0
    tapped_subtype: str = ""
    tap_count: int = 0
    created_token: TokenBlueprint | None = None

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt
                or self.source_zone not in {"battlefield","hand","graveyard"}
                or self.operation not in {"draw","drain_opponents",
                    "creature_to_hand","self_to_battlefield_tapped",
                    "all_legendary_creatures_to_hand",
                    "exile_graveyard_token"}
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
                or (self.sacrifice and self.discard)
                or type(self.draw_count) is not int or not 1<=self.draw_count<=7
                or type(self.life_loss_after) is not int
                or not 0<=self.life_loss_after<=20
                or (self.draw_count!=1 or self.life_loss_after)
                    and self.operation!="draw"
                or type(self.tapped_subtype) is not str
                or type(self.tap_count) is not int
                or not 0<=self.tap_count<=7
                or bool(self.tapped_subtype)!=bool(self.tap_count)
                or self.tap_count and (self.operation!="draw"
                    or self.tap or self.source_zone!="battlefield")
                or (self.operation=="exile_graveyard_token")
                    !=(self.created_token is not None)
                or self.created_token is not None
                    and not isinstance(self.created_token,TokenBlueprint)):
            raise ValueError("Invalid reviewed utility activation")


RULES={
    "Hedron Archive":UtilityRule(
        "32263baa-d3f0-463f-92b3-4e9938476add",
        "{2}, {T}, Sacrifice this artifact: Draw two cards.",
        "battlefield","{2}","draw",tap=True,sacrifice=True,draw_count=2),
    "Commander's Sphere":UtilityRule(
        "0b67c4e2-f88b-4e01-85a1-9d5f5b8db13b",
        "Sacrifice this artifact: Draw a card.",
        "battlefield","","draw",sacrifice=True),
    "Infernal Idol":UtilityRule(
        "a0802918-e18a-4716-befb-96ae6667f2f3",
        "{1}{B}{B}, {T}, Sacrifice this artifact: You draw two cards and lose 2 life.",
        "battlefield","{1}{B}{B}","draw",tap=True,sacrifice=True,
        draw_count=2,life_loss_after=2),
    "Cryptbreaker":UtilityRule(
        "16f75a65-d067-4f79-81b9-833c373cf4d2",
        "Tap three untapped Zombies you control: You draw a card and lose 1 life.",
        "battlefield","","draw",life_loss_after=1,
        tapped_subtype="Zombie",tap_count=3),
    "Cemetery Reaper":UtilityRule(
        "70fa209f-5e79-44de-81ce-1d8d0d8c1006",
        "{2}{B}, {T}: Exile target creature card from a graveyard. Create a 2/2 black Zombie creature token.",
        "battlefield","{2}{B}","exile_graveyard_token",tap=True,
        tap_creature=True,created_token=TokenBlueprint(
            "Zombie",frozenset({"creature"}),frozenset({"Zombie"}),
            frozenset({"B"}),2,2)),
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
    created_token_ids: tuple[int,...] = ()
    tapped_cost_ids: tuple[int,...] = ()
    drawn_ids: tuple[int,...] = ()
    life_lost_after: int = 0


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
    elif rule.operation=="exile_graveyard_token":
        eligible=eligible_graveyard_cards(
            zones,seat,GraveyardRecipe("exile","any",frozenset({"creature"})))
        if target_id not in eligible:
            return None
    elif target_id is not None:
        raise ValueError("Unexpected utility target")
    if rule.operation=="all_legendary_creatures_to_hand":
        # A non-targeting 'all' effect has no optional target chosen at cast.
        # Collect before payment, and include all eligible owned cards.
        recipe=GraveyardRecipe("hand","own",frozenset({"creature"}),
             required_supertypes=rule.target_supertypes)
        batch=eligible_graveyard_cards(zones,seat,recipe)
    else:
        batch=()
    if rule.operation=="draw" and len(zones.ids(seat,"library"))<rule.draw_count:
        return None
    tap_cost_ids=()
    if rule.tap_count:
        options=sorted((o for o in kernel.on_battlefield()
                if o.controller==seat and not o.tapped
                and "creature" in o.types
                and rule.tapped_subtype in o.subtypes),
                key=lambda o:(not o.token,o.power,o.object_id))
        if len(options)<rule.tap_count:
            return None
        tap_cost_ids=tuple(o.object_id for o in options[:rule.tap_count])
    life_cost=len(colors) if rule.life_by_commander_colors else rule.life
    if life.total(seat)<=life_cost:
        return None
    excluded=tuple(((source_id,) if rule.tap else ()) + tap_cost_ids)
    if rule.mana:
        preview=mana_service.plan(
            seat,rule.mana,excluded_source_ids=excluded)
        if preview is None:
            return None
    before=capture_battlefield(kernel)
    move_index=len(kernel.moves)
    paid=(mana_service.pay(seat,rule.mana,excluded_source_ids=excluded)
          if rule.mana else None)
    if rule.mana and paid is None:
        raise AssertionError("Reviewed utility payment changed")
    if rule.tap:
        source.tapped=True
        kernel._dirty()
    for oid in tap_cost_ids:
        kernel.get(oid).tapped=True
    if tap_cost_ids:
        kernel._dirty()
    if life_cost:
        life.lose(seat,life_cost,source_id)
    moved=[]
    tokens=()
    drawn=()
    if rule.sacrifice:
        moved.append(zones.move(source_id,"graveyard","sacrifice"))
        if death_engine is not None:
            death_engine.resolve_deaths(before,move_index=move_index,turn=turn)
    if rule.discard:
        moved.append(zones.discard(seat,source_id))
    if rule.operation=="draw":
        out=draw_physical_cards(zones,seat,CardQuantity(rule.draw_count))
        if not out.complete:
            raise AssertionError("Reviewed utility draw preview invalidated")
        drawn=tuple(out.drawn_ids)
        moved.extend(drawn)
        if rule.life_loss_after:
            life.lose(seat,rule.life_loss_after,source_id)
    elif rule.operation=="exile_graveyard_token":
        removed=resolve_graveyard_recipe(
            zones,seat,(target_id,),
            GraveyardRecipe("exile","any",frozenset({"creature"})))
        moved.extend(item.new_id for item in removed)
        tokens=create_reviewed_token_batches(
            zones,seat,(rule.created_token,))
        moved.extend(tokens)
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
                          life_cost,tuple(paid.source_ids) if paid else (),tuple(tokens),
                          tuple(tap_cost_ids),tuple(drawn),
                          rule.life_loss_after if rule.operation=="draw" else 0)
