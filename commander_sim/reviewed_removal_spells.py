"""Source-pinned generic destruction and temporary stat-change spells.

All six cards are configuration over three reusable physical effects:
destroy a legally selected target, destroy creatures below a power threshold,
and apply an end-of-turn -X/-X modifier to a qualified set. The live kernel
performs lethal/toughness state-based moves; the reviewed death engine handles
subsequent triggers. No invented opponent permanents or global priority.
"""
from dataclasses import dataclass
from .generic_cast import ReviewedCreatureCast,cast_reviewed_spell
from .reviewed_death_effects import capture_battlefield
from .mana_costs import parse_fixed_mana_cost


@dataclass(frozen=True)
class RemovalRule:
    oracle_id: str
    oracle_text: str
    mana_cost: str
    spell_type: str
    operation: str
    target: str = "none"
    amount: int = 0
    x_life_cost: bool = False
    life_cost: str = ""
    def __post_init__(self):
        if (not self.oracle_id or not self.oracle_text
                or self.spell_type not in {"instant","sorcery"}
                or self.operation not in {"destroy","destroy_and_debuff",
                                          "debuff_same_name","debuff_all",
                                          "destroy_below_power"}
                or self.target not in {"none","creature","opponent_creature_or_enchantment",
                                       "own_creature"}
                or self.life_cost not in {"","two","target_mana_value"}):
            raise ValueError("Invalid registered removal recipe")


RULES={
    "Infernal Grasp":RemovalRule(
        "94f0a572-e91c-4b56-a5d1-6cbbeabd210d",
        "Destroy target creature. You lose 2 life.",
        "{1}{B}","instant","destroy","creature",life_cost="two"),
    "Feed the Swarm":RemovalRule(
        "5825997b-10d7-4a36-972c-a80ddd90b8ed",
        "Destroy target creature or enchantment an opponent controls. You lose life equal to that permanent's mana value.",
        "{1}{B}","sorcery","destroy",
        "opponent_creature_or_enchantment",life_cost="target_mana_value"),
    "Mandate of Abaddon":RemovalRule(
        "20582c7b-edd3-4189-98ec-8fabd39034b0",
        "Choose target creature you control. Destroy all creatures with power less than that creature's power.",
        "{3}{B}","sorcery","destroy_below_power","own_creature"),
    "Bile Blight":RemovalRule(
        "0dd95516-893d-477e-a38c-3cc37c6e7ae0",
        "Target creature and all other creatures with the same name as that creature get -3/-3 until end of turn.",
        "{B}{B}","instant","debuff_same_name","creature",amount=3),
    "Blight Grenade":RemovalRule(
        "ae24b863-974c-4efa-ab41-23cfa1906c54",
        "Destroy target creature.\nAll creatures get -3/-3 until end of turn.",
        "{4}{B}","sorcery","destroy_and_debuff","creature",amount=3),
    "Toxic Deluge":RemovalRule(
        "afaef788-34d1-460b-b884-9d7ae6ddeb18",
        "As an additional cost to cast this spell, pay X life.\nAll creatures get -X/-X until end of turn.",
        "{2}{B}","sorcery","debuff_all",amount=0,x_life_cost=True),
}


def reviewed_removal(name,raw):
    rule=RULES.get(name)
    if (rule is None or not isinstance(raw,dict)
            or rule.oracle_id!=raw.get("oracle_id")
            or rule.oracle_text!=raw.get("oracle_text")
            or rule.mana_cost!=raw.get("mana_cost")
            or raw.get("type_line","").split(" — ",1)[0].lower()!=rule.spell_type):
        return None
    return rule


def valid_removal_target(zones,seat,rule,target_id):
    if rule.target=="none":
        return target_id is None
    if target_id not in zones.kernel.objects:
        return False
    obj=zones.kernel.get(target_id)
    if obj.zone!="battlefield":
        return False
    if rule.target=="creature":
        types={"creature"}
    elif rule.target=="own_creature":
        types={"creature"}
        if obj.controller!=seat:
            return False
    else:
        types={"creature","enchantment"}
        if obj.controller==seat:
            return False
    return zones.kernel.legal_target(seat,target_id,frozenset(types))


@dataclass(frozen=True)
class RemovalResult:
    card_name: str
    source_graveyard_id: int
    target_id: int | None
    affected_ids: tuple[int,...]
    destroyed_count: int
    x_life_paid: int


def cast_removal(zones,life,seat,spell_id,catalog,colors,mana_service, *,
                 target_id=None,x=0,death_engine=None,turn=1,on_cast=None):
    if spell_id not in zones.ids(seat,"hand"):
        raise ValueError("Spell not in hand")
    source=zones.kernel.get(spell_id)
    rule=reviewed_removal(source.card.name,catalog.get(source.card.name))
    if (rule is None or source.card.card_id!=rule.oracle_id
            or not valid_removal_target(zones,seat,rule,target_id)):
        raise ValueError("Unreviewed/illegal removal source or target")
    if type(x) is not int or x<0 or (x and not rule.x_life_cost):
        raise ValueError("Illegal X cost")
    if rule.x_life_cost and x>=life.total(seat):
        return None
    if mana_service.plan_spell(seat,rule.mana_cost,source) is None:
        return None
    # Target's mana value is pinned card metadata (token mana value is 0).
    target=zones.kernel.get(target_id) if target_id is not None else None
    target_value=0
    if target is not None and rule.life_cost=="target_mana_value":
        raw=catalog.get(target.card.name)
        if target.token:
            target_value=0
        elif raw is None or raw.get("oracle_id")!=target.card.card_id:
            raise ValueError("Unreviewed target mana value")
        else:
            cmc=raw.get("cmc")
            if type(cmc) not in (int,float) or cmc<0:
                raise ValueError("Unreviewed target mana value")
            target_value=int(cmc)
    before=capture_battlefield(zones.kernel)
    move_index=len(zones.kernel.moves)
    committed=cast_reviewed_spell(
        zones,seat,spell_id,ReviewedCreatureCast(
            rule.oracle_id,rule.mana_cost,True,
            ("Limited no-opponent-priority removal resolution",)),
        colors,mana_service=mana_service,spell_type=rule.spell_type)
    if committed is None:
        return None
    if rule.x_life_cost and x:
        life.lose(seat,x,spell_id)
    if on_cast is not None:
        on_cast(committed.ticket)
    affected=[]
    def resolve(kernel,ticket):
        from simulator.v7_rules.rules import Modifier
        creatures=tuple(o for o in kernel.on_battlefield()
                        if "creature" in o.types)
        if rule.operation in {"destroy","destroy_and_debuff"}:
            if target_id in kernel.objects:
                kernel.destroy(target_id)
                affected.append(target_id)
        if rule.operation=="destroy_below_power":
            # Target power and creatures are evaluated on resolution.
            threshold=kernel.get(target_id).power
            for body in creatures:
                if body.object_id!=target_id and body.power<threshold:
                    kernel.destroy(body.object_id)
                    affected.append(body.object_id)
        if rule.operation in {"debuff_all","debuff_same_name","destroy_and_debuff"}:
            n=x if rule.x_life_cost else rule.amount
            if rule.operation=="debuff_same_name":
                name=target.card.name
                eligible=[o for o in creatures if o.card.name==name]
            else:
                eligible=creatures
            for obj in eligible:
                if obj.object_id in kernel.objects and obj.zone=="battlefield":
                    kernel.add_modifier(obj.object_id,Modifier(-n,-n,
                        expires_at="end_turn"))
                    affected.append(obj.object_id)
            kernel.check_state_based()
        # all deaths are resolved after spell leaves stack
    grave_id=zones.resolve(committed.ticket,effect=resolve)
    if death_engine is not None:
        death_engine.resolve_deaths(before,move_index=move_index,turn=turn)
    deaths=sum(move.old_zone=="battlefield" and move.new_zone=="graveyard"
               for move in zones.kernel.moves[move_index:])
    if rule.life_cost=="two":
        life.lose(seat,2,spell_id)
    if rule.life_cost=="target_mana_value":
        life.lose(seat,target_value,spell_id)
    return RemovalResult(source.card.name,grave_id,target_id,
                         tuple(affected),deaths,x)
