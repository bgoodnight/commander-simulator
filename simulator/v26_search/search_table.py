"""Merchant Scroll and Solve the Equation on the v1.13 deck."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v25_personal_tutor'))
from personal_tutor_table import PersonalTutorTable
from medallion_table import COLORS
from rules import Cost
from simulation import Action
from commander_sim.legacy_tutor_ops import resolve_historical_search

MERCHANT='Merchant Scroll'
SOLVE='Solve the Equation'
SPELLS={MERCHANT:('named_merchant_scroll',Cost(generic=1,blue=1)),
        SOLVE:('named_solve_equation',Cost(generic=2,blue=1))}

class SearchTable(PersonalTutorTable):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for name,(effect,cost) in SPELLS.items():
            key='named:'+name
            self.zones.specs[key]=replace(self.zones.specs[key],kind=name,card_type='sorcery',effect=effect,
                mana_value=cost.total,colored_cost=MappingProxyType({'U':1,'R':0}),
                parameters=MappingProxyType({'coverage':'verified_subset'}))
            for obj in self.rules.objects.values():
                if obj.card.card_id==key:
                    obj.card=replace(obj.card,types=frozenset({'sorcery'}),cost=cost,coverage='verified_subset')
            self.register_effect(effect,self.resolve_search)
        self.rules._dirty()

    def action_for(self,player,card):
        if card.name not in SPELLS:return super().action_for(player,card)
        _,base=SPELLS[card.name]
        cost=self.rules.modified_cost(player.seat,frozenset({'sorcery'}),base)
        action=Action(player.seat,card.name,'sorcery',card.effect,cost.total,parameters={**card.parameters,'U':1,'R':0})
        return self.adjust_named_action_cost(action)

    def resolve_search(self,table,action):
        keys={MERCHANT:'merchant_scroll', SOLVE:'solve_equation'}
        if action.source not in keys:raise ValueError('Unknown search spell')
        return resolve_historical_search(self,action.actor,keys[action.source],printed_colors=COLORS)
