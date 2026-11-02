"""Shared physical graveyard-target spells and temporary death-return effects.

All operations use authoritative LiveZones and reviewed source Oracle IDs.
The host supplies legal targets and interrupt windows, never fictitious cards.
"""
from dataclasses import dataclass

from .generic_cast import ReviewedCreatureCast,cast_reviewed_spell
from .physical_common_effects import CounterPlacement,put_reviewed_counters
from .graveyard_recipes import (
    GraveyardRecipe, eligible_graveyard_cards, resolve_graveyard_recipe)


@dataclass(frozen=True)
class ZoneSpellRule:
    oracle_id:str
    excerpt:str
    cost:str
    operation:str
    spell_type:str="instant"

    def __post_init__(self):
        if (not self.oracle_id or not self.excerpt or not self.cost
                or self.operation not in {"opponent_graveyard_theft",
                                          "return_when_dies"}
                or self.spell_type not in {"instant","sorcery"}):
            raise ValueError("Unknown source-reviewed zone spell")


RULES={
    "Nurgle's Conscription":ZoneSpellRule(
        "967f0c23-7af2-4e86-9ebc-dc2f8856c7c5",
        "Put target creature card from an opponent's graveyard onto the battlefield tapped under your control, then exile that player's graveyard.",
        "{4}{B}","opponent_graveyard_theft"),
    "Undying Malice":ZoneSpellRule(
        "8b061702-1bc3-45aa-a758-446b25034801",
        "Until end of turn, target creature gains \"When this creature dies, return it to the battlefield tapped under its owner's control with a +1/+1 counter on it.\"",
        "{B}","return_when_dies"),
}


def reviewed_zone_spell(name,raw):
    rule=RULES.get(name)
    return (rule if rule is not None and isinstance(raw,dict)
            and raw.get("oracle_id")==rule.oracle_id
            and rule.excerpt in raw.get("oracle_text","") else None)


@dataclass(frozen=True)
class ZoneSpellOutcome:
    name:str
    operation:str
    target_id:int
    moved_ids:tuple[int,...]
    paid_source_ids:tuple[int,...]


class ZoneSpellEngine:
    def __init__(self,zones,life,catalog,mana,death_engine):
        if (zones.kernel is not life.kernel or zones.kernel is not mana.kernel
                or death_engine.zones is not zones):
            raise ValueError("Zone spells require one physical kernel")
        self.zones=zones
        self.life=life
        self.catalog=catalog
        self.mana=mana
        self.death_engine=death_engine
        self.pending_returns={}  # old battlefield ID -> expiry phase key
        self._handled=set()
        self.events=[]

    def valid_target(self,seat,rule,target_id):
        kernel=self.zones.kernel
        target=kernel.objects.get(target_id)
        if target is None or "creature" not in target.types:
            return False
        if rule.operation=="opponent_graveyard_theft":
            return (target.zone=="graveyard"
                    and target.owner!=seat
                    and target_id in self.zones.ids(target.owner,"graveyard"))
        if rule.operation=="return_when_dies":
            return (target.zone=="battlefield"
                    and kernel.legal_target(seat,target_id,
                                            frozenset({"creature"})))
        return False

    def cast(self,seat,source_id,target_id,*,turn,on_cast=None,
             expires_at_seat=None):
        kernel=self.zones.kernel
        if source_id not in self.zones.ids(seat,"hand"):
            raise ValueError("Zone spell source must be a hand card")
        source=kernel.get(source_id)
        rule=reviewed_zone_spell(source.card.name,self.catalog.get(source.card.name))
        if rule is None or source.card.card_id!=rule.oracle_id:
            raise ValueError("Unknown reviewed graveyard spell")
        if not self.valid_target(seat,rule,target_id):
            return None
        if self.mana.plan_spell(seat,rule.cost,source) is None:
            return None
        review=ReviewedCreatureCast(rule.oracle_id,rule.cost,True)
        committed=cast_reviewed_spell(
            self.zones,seat,source_id,review,frozenset({"B"}),
            mana_service=self.mana,spell_type=rule.spell_type)
        if committed is None:
            return None
        if on_cast is not None:
            on_cast(committed.ticket)
        # Reviewed resolution is supplied explicitly. The stack host must
        # not infer a spell effect from an instant card name.
        self.zones.resolve(committed.ticket,lambda kernel,ticket:None)
        moved=[]
        if rule.operation=="opponent_graveyard_theft":
            target=kernel.get(target_id)
            victim_owner=target.owner
            stolen=resolve_graveyard_recipe(
                self.zones,seat,(target_id,),
                GraveyardRecipe("battlefield","opponent",
                                frozenset({"creature"}),
                                controller_on_entry="actor",enter_tapped=True))
            moved.extend(item.new_id for item in stolen)
            remaining=tuple(self.zones.ids(victim_owner,"graveyard"))
            exiled=resolve_graveyard_recipe(
                self.zones,seat,remaining,GraveyardRecipe("exile","opponent"))
            moved.extend(item.new_id for item in exiled)
        elif rule.operation=="return_when_dies":
            self.pending_returns[target_id]=(
                turn,seat if expires_at_seat is None else expires_at_seat)
        result=ZoneSpellOutcome(
            source.card.name,rule.operation,target_id,tuple(moved),
            tuple(committed.paid_source_ids))
        self.events.append(result)
        return result

    def observe_deaths(self,before,changes,*,turn):
        outcomes=[]
        kernel=self.zones.kernel
        for move in changes:
            old=move.object_id
            if old in self._handled or old not in self.pending_returns:
                continue
            self._handled.add(old)
            self.pending_returns.pop(old,None)
            if (move.new_zone!="graveyard" or move.new_object_id is None
                    or old not in before):
                continue
            original_owner=before[old].owner
            restored=resolve_graveyard_recipe(
                self.zones,original_owner,(move.new_object_id,),
                GraveyardRecipe("battlefield","own",
                                frozenset({"creature"}),enter_tapped=True,
                                enter_counters=("+1/+1",1)))[0].new_id
            outcome=ZoneSpellOutcome(
                "temporary_death_return","return_when_dies",old,(restored,),())
            outcomes.append(outcome)
        self.events.extend(outcomes)
        return tuple(outcomes)

    def expire(self,turn,*,active_seat):
        """Expiry after the *actual* current player's cleanup boundary."""
        expired=[oid for oid,(t,seat) in self.pending_returns.items()
                 if t==turn and seat==active_seat]
        for oid in expired:
            self.pending_returns.pop(oid,None)
        return tuple(expired)
