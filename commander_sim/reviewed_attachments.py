"""Reusable physical attachments, static auras and paid upkeep/recursion.

The kernel owns objects and zones. This module owns only relationships
(source object id -> target id) and derives transient modifiers from live
pinned source rules. A card leaving play removes its static benefit.
"""
from dataclasses import dataclass
from dataclasses import replace

from .reviewed_death_effects import capture_battlefield
from .physical_common_effects import CardQuantity, draw_physical_cards
from .reviewed_token_spells import TokenBlueprint,create_reviewed_token_batches


@dataclass(frozen=True)
class AttachmentRule:
    oracle_id:str
    excerpt:str
    equip_cost:str=""
    power:int=0
    toughness:int=0
    keywords:frozenset[str]=frozenset()
    scope:str="attached"  # attached / own_creatures / opponent_aura
    death_draw:int=0
    upkeep_sacrifice:bool=False
    recursion_cost:str=""
    death_return_token:bool=False


RULES={
    "Basilisk Collar":AttachmentRule(
        "f5f4dd28-f4ae-4d39-b9b8-6ebfd63c93fe",
        "Equipped creature has deathtouch and lifelink.","{2}",
        keywords=frozenset({"deathtouch","lifelink"})),
    "Swiftfoot Boots":AttachmentRule(
        "c8b143ad-43ec-4e0d-a440-e348daa31391",
        "Equipped creature has hexproof and haste.","{1}",
        keywords=frozenset({"hexproof","haste"})),
    "Skullclamp":AttachmentRule(
        "65986c1b-8e51-4604-b685-d82fa7d1263a",
        "Equipped creature gets +1/-1.","{1}",
        power=1,toughness=-1,death_draw=2),
    "Eldrazi Monument":AttachmentRule(
        "c7ee1b21-d02e-49ef-95d6-d6dbf2f886ae",
        "Creatures you control get +1/+1 and have flying and indestructible.",
        power=1,toughness=1,keywords=frozenset({"flying","indestructible"}),
        scope="own_creatures",upkeep_sacrifice=True),
    "Whip of Erebos":AttachmentRule(
        "53987a39-c18c-4c13-b1ea-fd1b2a369f9e",
        "Creatures you control have lifelink.",
        keywords=frozenset({"lifelink"}),scope="own_creatures",
        recursion_cost="{2}{B}{B}"),
    "Nurgle's Rot":AttachmentRule(
        "1b01dcff-0639-4ed0-bd9e-f28429cb803d",
        "Enchant creature an opponent controls",
        scope="opponent_aura",death_return_token=True),
}


def reviewed_attachment(name,raw):
    rule=RULES.get(name)
    if (rule is None or not isinstance(raw,dict)
            or raw.get("oracle_id")!=rule.oracle_id
            or rule.excerpt not in raw.get("oracle_text","")):
        return None
    return rule


@dataclass(frozen=True)
class AttachmentEvent:
    operation:str
    source_id:int
    target_id:int|None=None
    moved_ids:tuple[int,...]=()
    paid_source_ids:tuple[int,...]=()


class AttachmentEngine:
    def __init__(self,zones,life,catalog,mana_service,death_engine):
        if (life.kernel is not zones.kernel
                or mana_service.kernel is not zones.kernel
                or death_engine.zones is not zones):
            raise ValueError("Attachment services must share physical kernel")
        self.zones=zones
        self.life=life
        self.catalog=catalog
        self.mana=mana_service
        self.death_engine=death_engine
        self.attached={}  # physical live source ID -> physical live target ID
        self._applied=[]  # (target ID, immutable Modifier identity)
        self._seen_deaths=set()
        self.events=[]

    def _rule(self,obj):
        r=reviewed_attachment(obj.card.name,self.catalog.get(obj.card.name))
        return r if r is not None and obj.card.card_id==r.oracle_id else None

    def _legal_target(self,source,target,rule):
        if ("creature" not in target.types or target.zone!="battlefield"
                or target.controller==(source.controller
                                      if rule.scope=="opponent_aura" else -1)
                and rule.scope=="opponent_aura"):
            return False
        if rule.scope!="opponent_aura" and target.controller!=source.controller:
            return False
        return self.zones.kernel.legal_target(
            source.controller,target.object_id,frozenset({"creature"}))

    def bind(self,source_id,target_id,*,sorcery_window=True,already_paid=False):
        """Equip or place an Aura using a real, explicitly selected target."""
        if sorcery_window is not True:
            raise ValueError("Attachment requires reviewed main-phase window")
        k=self.zones.kernel
        source=k.objects.get(source_id)
        target=k.objects.get(target_id)
        if source is None or target is None or source.zone!="battlefield":
            return None
        rule=self._rule(source)
        if rule is None or rule.scope not in {"attached","opponent_aura"}:
            raise ValueError("Not an approved physical attachment")
        if not self._legal_target(source,target,rule):
            return None
        paid=()
        if rule.equip_cost:
            if self.mana.plan(source.controller,rule.equip_cost) is None:
                return None
            result=self.mana.pay(source.controller,rule.equip_cost)
            if result is None:
                return None
            paid=tuple(result.source_ids)
        elif rule.scope!="opponent_aura" or not already_paid:
            raise ValueError("Aura attachment requires verified spell cast")
        self.attached[source_id]=target_id
        self.sync()
        event=AttachmentEvent("attached",source_id,target_id,paid_source_ids=paid)
        self.events.append(event)
        return event

    def sync(self,*,turn=1):
        """Recalculate live source modifiers and process state-based deaths."""
        from simulator.v7_rules.rules import Modifier
        kernel=self.zones.kernel
        before=capture_battlefield(kernel)
        start=len(kernel.moves)
        changed=False
        for oid,modifier in self._applied:
            obj=kernel.objects.get(oid)
            if obj is not None:
                for j,active in enumerate(obj.modifiers):
                    if active is modifier:
                        obj.modifiers.pop(j);changed=True;break
        self._applied.clear()
        self.attached={
            s:t for s,t in self.attached.items()
            if s in kernel.objects and t in kernel.objects
            and kernel.get(s).zone=="battlefield"
            and kernel.get(t).zone=="battlefield"}
        for source in sorted(tuple(kernel.on_battlefield()),
                             key=lambda o:o.object_id):
            rule=self._rule(source)
            if rule is None:
                continue
            if rule.scope=="own_creatures":
                targets=[o for o in kernel.on_battlefield()
                         if o.controller==source.controller
                         and "creature" in o.types]
            elif rule.scope=="attached" and source.object_id in self.attached:
                targets=[kernel.get(self.attached[source.object_id])]
            else:
                targets=[]
            if not (rule.power or rule.toughness or rule.keywords):
                continue
            for target in targets:
                modifier=Modifier(rule.power,rule.toughness,rule.keywords)
                target.modifiers.append(modifier)
                self._applied.append((target.object_id,modifier))
                changed=True
        if changed:
            kernel._dirty()
            kernel.check_state_based()
            if len(kernel.moves)>start:
                self.death_engine.resolve_deaths(
                    before,move_index=start,turn=turn)
        return tuple(self.attached.items())

    def observe_deaths(self,before,changes,*,turn):
        """Resolve equipment/Aura linked death triggers from pre-death IDs."""
        from .reviewed_token_spells import TokenBlueprint
        result=[]
        for move in changes:
            old=move.object_id
            if old in self._seen_deaths:
                continue
            for source_id,target_id in tuple(self.attached.items()):
                if target_id!=old or source_id not in before:
                    continue
                fact=before[source_id]
                rule=reviewed_attachment(fact.name,self.catalog.get(fact.name))
                if rule is None or rule.oracle_id!=fact.oracle_id:
                    continue
                if rule.death_draw:
                    outcome=draw_physical_cards(
                        self.zones,fact.controller,CardQuantity(rule.death_draw))
                    if not outcome.complete:
                        raise NotImplementedError("Empty library draw loss not modeled")
                    result.append(AttachmentEvent(
                        "attachment_death_draw",source_id,old,
                        tuple(outcome.drawn_ids)))
                elif rule.death_return_token:
                    # An Aura with no enchanted object first falls off into
                    # graveyard, then its actual death trigger returns it.
                    aura=self.zones.kernel.objects.get(source_id)
                    if aura is not None and aura.zone=="battlefield":
                        gy=self.zones.move(source_id,"graveyard","state_based")
                        returned=self.zones.move(gy,"hand","resolve")
                        plague=TokenBlueprint(
                            "Plaguebearer of Nurgle",frozenset({"creature"}),
                            frozenset({"Demon"}),frozenset({"B"}),1,3)
                        ids=create_reviewed_token_batches(
                            self.zones,fact.controller,(plague,))
                        result.append(AttachmentEvent(
                            "aura_death_return",source_id,old,
                            (returned,*ids)))
            self._seen_deaths.add(old)
        self.attached={s:t for s,t in self.attached.items()
                       if t not in self._seen_deaths}
        self.events.extend(result)
        return tuple(result)

    def upkeep(self,seat,*,turn):
        """Pay reviewed upkeep sacrifice for all controlled sources."""
        k=self.zones.kernel
        outcomes=[]
        for source in sorted(tuple(k.on_battlefield()),key=lambda o:o.object_id):
            rule=self._rule(source)
            if (source.controller!=seat or rule is None
                    or not rule.upkeep_sacrifice):
                continue
            bodies=[o for o in k.on_battlefield()
                    if o.controller==seat and "creature" in o.types]
            before=capture_battlefield(k)
            start=len(k.moves)
            if bodies:
                # Generic board value choice: sacrifice an expendable token
                # instead of your commander or a valuable engine piece.
                chosen=min(bodies,key=lambda o:(
                    0 if o.token else 1,
                    1 if "commander" in o.card.supertypes else 0,
                    o.power+o.toughness,o.object_id))
                self.zones.move(chosen.object_id,"graveyard","sacrifice",
                                commander_choice=True)
                outcomes.append(AttachmentEvent(
                    "upkeep_sacrifice_creature",source.object_id,
                    chosen.object_id))
            else:
                self.zones.move(source.object_id,"graveyard","sacrifice")
                outcomes.append(AttachmentEvent(
                    "upkeep_sacrifice_source",source.object_id))
            self.death_engine.resolve_deaths(before,move_index=start,turn=turn)
        if outcomes:
            self.sync(turn=turn)
            self.events.extend(outcomes)
        return tuple(outcomes)

    def resurrect(self,source_id,grave_id,*,turn,sorcery_window=True):
        """Generic tapped-source reanimation with haste and next-step exile.

        Uses the existing kernel's already-tested unearth-style replacement
        map, not a second zone state or hardcoded controller override.
        """
        if sorcery_window is not True:
            raise ValueError("Reanimation requires sorcery window")
        k=self.zones.kernel
        source=k.objects.get(source_id)
        dead=k.objects.get(grave_id)
        if source is None or dead is None or source.zone!="battlefield":
            return None
        rule=self._rule(source)
        if (rule is None or not rule.recursion_cost or source.tapped
                or dead.owner!=source.controller or dead.zone!="graveyard"
                or "creature" not in dead.types):
            return None
        if self.mana.plan(source.controller,rule.recursion_cost) is None:
            return None
        paid=self.mana.pay(source.controller,rule.recursion_cost)
        if paid is None:
            return None
        source.tapped=True
        k._dirty()
        new_id=self.zones.move(grave_id,"battlefield","resolve")
        live=k.get(new_id)
        original=live.card
        live.card=replace(original,keywords=original.keywords|frozenset({"haste"}))
        k.unearth_pending[new_id]=original
        k._dirty()
        self.sync(turn=turn)
        event=AttachmentEvent("resurrect_temporary",source_id,new_id,
                              (new_id,),tuple(paid.source_ids))
        self.events.append(event)
        return event
