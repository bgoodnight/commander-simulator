"""Phyrexian Altar, with explicitly bounded blue/red mana production."""
from dataclasses import dataclass,replace
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v29_step_cycling'))
from step_cycling import StepCyclingTable
from resources import Resources,Ability,SourcePayment,U,R,spend
from rules import Cost,Event
from simulation import Action
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from commander_sim.legacy_common_ops import (SacrificeRequirement,
    legal_sacrifice_victims, sacrifice_physical_object)

NAME='Phyrexian Altar'
ALTAR_SACRIFICE=SacrificeRequirement(frozenset({'artifact'}),frozenset({'creature'}))

@dataclass(frozen=True)
class AltarAbility(Ability):
    altar_id:int=0
    token:bool=False

class AltarResources(Resources):
    def sources(self,seat,ready=True):
        base=dict(super().sources(seat,ready))
        altars=sorted(o.object_id for o in self.kernel.on_battlefield() if o.controller==seat and o.card.name==NAME and 'artifact' in o.types)
        if not altars:return tuple(base.items())
        altar=altars[0]
        # A sacrificed Altar could invalidate later activations. Until the
        # general planner tracks cross-source dependencies, omit all Altars.
        eligible=set(legal_sacrifice_victims(self.kernel,seat,altar,ALTAR_SACRIFICE))-set(altars)
        for obj in sorted(self.kernel.on_battlefield(),key=lambda o:not o.token):
            if obj.object_id not in eligible:continue
            modes=tuple(AltarAbility(output,sacrifice=True,altar_id=altar,token=obj.token) for output in (U,R))
            base[obj.object_id]=base.get(obj.object_id,())+modes
        return tuple(base.items())

    def activate(self,seat,activation,defer_sba=False):
        ability=activation.ability
        if not isinstance(ability,AltarAbility):return super().activate(seat,activation,defer_sba)
        victim=self.kernel.objects.get(activation.source_id);altar=self.kernel.objects.get(ability.altar_id)
        eligible=legal_sacrifice_victims(self.kernel,seat,ability.altar_id,ALTAR_SACRIFICE)
        if (victim is None or altar is None or altar.card.name!=NAME
            or activation.source_id not in eligible or ability.output not in (U,R) or ability.cost!=Cost()
            or not ability.sacrifice or ability.life or ability.damage or self.table.players[seat].eliminated_round is not None
            or activation.remaining_before_output not in spend(self.pool(seat),ability.cost)):
            raise ValueError('Illegal Altar mana ability')
        victim_name=victim.card.name
        sacrifice_physical_object(self.table,seat,ability.altar_id,victim.object_id,ALTAR_SACRIFICE)
        self.kernel.mana_pools[seat]=tuple(activation.remaining_before_output[i]+ability.output[i] for i in range(3))
        self.kernel._dirty();self.kernel.events.append(Event('mana_added',seat,ability.altar_id,amount=1))
        self.activations.append(dict(seat=seat,source_id=ability.altar_id,source=NAME,output=ability.output,
            activation_cost=(0,0,0),life_paid=0,damage=0,sacrifice=True,sacrificed_id=activation.source_id,sacrificed=victim_name))
        self.table.note(f'    MANA P{seat}: {NAME} #{ability.altar_id} sacrifices {victim_name} #{activation.source_id} -> {ability.output}.')

class AltarTable(StepCyclingTable):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.resources=AltarResources(self)
        for player in self.players:
            player.resources=self.resources;player.payment_policy=SourcePayment(self.resources)
        key='named:'+NAME
        self.zones.specs[key]=replace(self.zones.specs[key],kind=NAME,card_type='artifact',effect='named_phyrexian_altar',
            mana_value=3,colored_cost=MappingProxyType({'U':0,'R':0}),parameters=MappingProxyType({'coverage':'partial'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id==key:obj.card=replace(obj.card,types=frozenset({'artifact'}),cost=Cost(3),coverage='verified_subset')
        self.rules._dirty();self.register_effect('named_phyrexian_altar',self.resolve_altar)

    def action_for(self,player,card):
        if card.name!=NAME:return super().action_for(player,card)
        cost=self.rules.modified_cost(player.seat,frozenset({'artifact'}),Cost(3))
        return self.adjust_named_action_cost(Action(player.seat,NAME,'artifact',card.effect,cost.total,parameters={**card.parameters,'U':0,'R':0}))

    def resolve_altar(self,table,action):
        self.add_permanent(self.players[action.actor],'utility',0,NAME)
