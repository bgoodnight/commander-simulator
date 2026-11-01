"""Named sacrifice activations composed from one source/target/cost/effect path.

The existing IndexedKernel/LiveZones own cards, taps and mana pools. This
bounded no-priority adapter requires explicit tap-readiness authorization
from a turn driver and explicitly reviewed source Oracle text. Other printed
abilities (ETB, escape, protection, proliferate, etc.) remain unsupported.
"""
from dataclasses import dataclass,replace

from .ability_composition import (
    AbilitySlot, AbilityHandler, ComposedCard, AbilityDispatcher)
from .kernel_life import KernelLife
from .physical_common_effects import (
    CardQuantity, draw_physical_cards, CounterPlacement, put_reviewed_counters,
    scry_physical_cards)
from .reviewed_death_effects import capture_battlefield
from .reviewed_token_spells import TokenBlueprint,create_reviewed_token_batches


_ZOMBIE=TokenBlueprint("Zombie",frozenset({"creature"}),
    frozenset({"Zombie"}),frozenset({"B"}),2,2)


@dataclass(frozen=True)
class SacrificeMode:
    oracle_id: str
    excerpt: str
    action: str
    sacrifice_other: bool = False
    tap: bool = False
    black_cost: int = 0
    victim_color: str = ""
    life_cost: int = 0

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt or
            self.action not in {"zombies_by_power","self_counter",
                "draw","colorless_mana","black_mana_by_value","scry",
                "wither_draw"} or
            type(self.sacrifice_other) is not bool or
            type(self.tap) is not bool or
            type(self.black_cost) is not int or self.black_cost<0 or
            self.victim_color not in {"","B"} or
            type(self.life_cost) is not int or self.life_cost<0):
            raise ValueError("Invalid reviewed sacrifice parameters")


SACRIFICE_MODES={
    "Ghoulcaller Gisa":SacrificeMode(
        "0dd894cb-1968-471c-af08-ea7ec5ce8428",
        "{B}, {T}, Sacrifice another creature: Create X 2/2 black Zombie creature tokens, where X is the sacrificed creature's power.",
        "zombies_by_power",True,True,1),
    "Carrion Feeder":SacrificeMode(
        "a1cc5e37-b09a-4b7f-afd5-77c1c35aa425",
        "Sacrifice a creature: Put a +1/+1 counter on this creature.",
        "self_counter"),
    "Ayara, First of Locthwain":SacrificeMode(
        "388168b3-ec68-4af2-b88c-6a5ec88c15f6",
        "{T}, Sacrifice another black creature: Draw a card.",
        "draw",True,True,0,"B"),
    "Ashnod's Altar":SacrificeMode(
        "4d18bcba-a346-445e-a182-6cc30b7e066d",
        "Sacrifice a creature: Add {C}{C}.",
        "colorless_mana"),
    "Viscera Seer":SacrificeMode(
        "f82a4e85-526d-4456-b700-7760043a31be",
        "Sacrifice a creature: Scry 1.",
        "scry"),
    "Woe Strider":SacrificeMode(
        "3adbd963-e85d-4569-963a-4472594f06f9",
        "Sacrifice another creature: Scry 1.",
        "scry",True),
    "Yawgmoth, Thran Physician":SacrificeMode(
        "a1e232c0-dc38-47be-a5a0-f68bc1d86a29",
        "Pay 1 life, Sacrifice another creature: Put a -1/-1 counter on up to one target creature and draw a card.",
        "wither_draw",True,False,0,"",1),
    "Illuminor Szeras":SacrificeMode(
        "10f274f9-9044-447b-81c9-d4906ad9e6be",
        "Secrets of the Soul — {T}, Sacrifice another creature: Add an amount of {B} equal to the sacrificed creature's mana value.",
        "black_mana_by_value",True,True),
}


def reviewed_sacrifice_artifact(name,raw):
    """Reviewed no-ETB artifacts eligible for one generic physical cast."""
    return bool(name=="Ashnod's Altar"
        and raw.get("layout")=="normal"
        and raw.get("type_line")=="Artifact"
        and raw.get("oracle_id")==SACRIFICE_MODES[name].oracle_id
        and raw.get("oracle_text")==SACRIFICE_MODES[name].excerpt)


@dataclass(frozen=True)
class SacrificeResult:
    source_id: int
    source_name: str
    victim_old_id: int
    victim_new_id: int | None
    operation: str
    token_ids: tuple[int,...] = ()
    drawn_ids: tuple[int,...] = ()
    death_trigger_count: int = 0
    mana_added: tuple[str,...] = ()
    scry_bottomed: tuple[int,...] = ()


def activate_reviewed_sacrifice(
    zones, life:KernelLife, source_id, victim_id, catalog, *,
    mana_service=None, turn=1, tap_ready=False, target_id=None,
    scry_to_bottom=False, death_engine=None):
    """Apply an already-authorized named activated ability to physical cards.

    The host must supply tap_ready=True only when the source has controlled
    since turn start (or has haste); this API does not guess summoning
    sickness. Costs are screened before mutation. All per-card variation
    lives in SacrificeMode, not custom action handlers.
    """
    kernel=zones.kernel
    if life.kernel is not kernel:
        raise ValueError("Life totals must belong to the same physical kernel")
    source=kernel.objects.get(source_id)
    victim=kernel.objects.get(victim_id)
    if source is None or victim is None:
        raise ValueError("Missing source/victim physical object")
    mode=SACRIFICE_MODES.get(source.card.name)
    raw=catalog.get(source.card.name)
    if (mode is None or raw is None
        or raw.get("oracle_id")!=mode.oracle_id
        or source.card.card_id!=mode.oracle_id
        or mode.excerpt not in raw.get("oracle_text","")):
        raise ValueError("Unreviewed source ability")
    if (source.zone!="battlefield" or victim.zone!="battlefield"
            or source.controller!=victim.controller
            or "creature" not in victim.types
            or mode.sacrifice_other and source_id==victim_id
            or mode.victim_color and
            (victim.card.colors is None
             or mode.victim_color not in victim.card.colors)):
        raise ValueError("Illegal reviewed sacrifice cost")
    if mode.tap and (source.tapped or tap_ready is not True):
        raise ValueError("Source is tapped or tap/summoning-sickness readiness unverified")
    if mode.action=="wither_draw" and target_id is not None:
        target=kernel.objects.get(target_id)
        if (target is None or target.zone!="battlefield"
                or "creature" not in target.types
                or not kernel.legal_target(source.controller,target_id,
                                           frozenset({"creature"}))):
            raise ValueError("Illegal target for -1/-1 counter")
    if type(scry_to_bottom) is not bool:
        raise ValueError("Scry choice must be explicit Boolean")
    if mode.action in {"draw","wither_draw"} and not zones.ids(source.controller,"library"):
        raise NotImplementedError("Empty-library draw needs full state-based loss handling")
    if mode.life_cost and life.total(source.controller)<mode.life_cost:
        raise ValueError("Cannot pay reviewed life activation cost")
    if mode.action=="black_mana_by_value":
        victim_raw=catalog.get(victim.card.name)
        mana_value=0 if victim.token else (None if victim_raw is None else victim_raw.get("cmc"))
        if (type(mana_value) not in (int,float) or mana_value<0
                or int(mana_value)!=mana_value):
            raise ValueError("Sacrificed creature mana value is unreviewed")
        mana_value=int(mana_value)
    else:
        mana_value=0
    if mode.action in {"colorless_mana","black_mana_by_value"} or mode.black_cost:
        if mana_service is None or mana_service.kernel is not kernel:
            raise ValueError("Matching authoritative mana service required")
    paid=None
    if mode.black_cost:
        paid=mana_service.plan(source.controller,
                               "{B}"*mode.black_cost)
        if paid is None:
            return None
    pre=capture_battlefield(kernel)
    move_index=len(kernel.moves)
    victim_power=max(0,victim.power)
    slot=AbilitySlot(mode.oracle_id,"front","sacrifice_activation",
                     "activated",mode,mode.excerpt,"pinned-oracle-m1",
                     frozenset({"physical_sacrifice","reviewed_costs"}))
    card=ComposedCard(mode.oracle_id,raw["oracle_text"],(slot,),
        (AbilityHandler(slot.key,"exact",mode,slot.source_revision,
                        frozenset({"physical_sacrifice","reviewed_costs"})),))
    dispatcher=AbilityDispatcher(card,"strict",
        frozenset({"physical_sacrifice","reviewed_costs"}))
    def execute(operation):
        if paid is not None:
            executed=mana_service.pay(source.controller,"{B}"*operation.black_cost)
            if executed is None:
                raise AssertionError("Mana cost preview invalidated before commit")
        if operation.tap:
            kernel.get(source_id).tapped=True
            kernel._dirty()
        if operation.life_cost:
            life.lose(source.controller,operation.life_cost,source_id)
        movement=zones.move(victim_id,"graveyard","sacrifice")
        if victim_id in kernel.objects or len(kernel.moves) == move_index:
            raise AssertionError("Sacrifice movement did not occur")
        created=()
        drawn=()
        added=()
        bottomed=()
        if operation.action=="zombies_by_power" and victim_power:
            created=create_reviewed_token_batches(
                zones,source.controller,(replace(_ZOMBIE,count=victim_power),))
        elif operation.action=="self_counter":
            if source_id in kernel.objects and kernel.get(source_id).zone=="battlefield":
                put_reviewed_counters(kernel,source.controller,source_id,
                    CounterPlacement("+1/+1"))
        elif operation.action in {"draw","wither_draw"}:
            if operation.action=="wither_draw" and target_id is not None:
                put_reviewed_counters(kernel,source.controller,target_id,
                    CounterPlacement("-1/-1",1,frozenset({"creature"}),False))
            answer=draw_physical_cards(zones,source.controller,CardQuantity(1))
            if not answer.complete:
                raise AssertionError("Reviewed draw preview invalidated")
            drawn=answer.drawn_ids
        elif operation.action=="scry":
            seen=zones.ids(source.controller,"library")
            bottom=(seen[-1],) if seen and scry_to_bottom else ()
            answer=scry_physical_cards(
                zones,source.controller,1,bottom_ids=bottom)
            bottomed=answer.bottomed_ids
        elif operation.action in {"colorless_mana","black_mana_by_value"}:
            added=("C","C") if operation.action=="colorless_mana" else (
                ("B",)*mana_value)
            pool=list(mana_service.floating(source.controller))
            colors="WUBRGC"
            for color in added:
                pool[colors.index(color)]+=1
            kernel.mana_pools[source.controller]=tuple(pool)
            kernel._dirty()
        else:
            raise NotImplementedError("Unreviewed sacrifice operation")
        return movement,tuple(created),tuple(drawn),tuple(added),tuple(bottomed)
    move,created,drawn,added,bottomed=dispatcher.invoke(slot.slot_id,source_id,execute)
    triggers=()
    if death_engine is not None:
        if death_engine.zones is not zones or death_engine.life is not life:
            raise ValueError("Death engine must share source kernel state")
        triggers=death_engine.resolve_deaths(pre,move_index=move_index,turn=turn)
    return SacrificeResult(source_id,source.card.name,victim_id,
        move,mode.action,created,drawn,len(triggers),added,bottomed)
