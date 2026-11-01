"""Personal Tutor on the canonical-deck table."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v24_reinforcements'))
from reinforcements_table import ReinforcementTable
from rules import Cost
from simulation import Action
from commander_sim.legacy_tutor_ops import resolve_historical_search

NAME='Personal Tutor'

class PersonalTutorTable(ReinforcementTable):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        key='named:'+NAME
        self.zones.specs[key]=replace(self.zones.specs[key],kind=NAME,card_type='sorcery',
             effect='named_personal_tutor',mana_value=1,colored_cost=MappingProxyType({'U':1,'R':0}),
             parameters=MappingProxyType({'coverage':'verified_subset'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id==key:
                obj.card=replace(obj.card,types=frozenset({'sorcery'}),cost=Cost(blue=1),coverage='verified_subset')
        self.rules._dirty();self.register_effect('named_personal_tutor',self.resolve_personal_tutor)

    def action_for(self,player,card):
        if card.name!=NAME:return super().action_for(player,card)
        cost=self.rules.modified_cost(player.seat,frozenset({'sorcery'}),Cost(blue=1))
        action=Action(player.seat,NAME,'sorcery',card.effect,cost.total,parameters={**card.parameters,'U':1,'R':0})
        return self.adjust_named_action_cost(action)

    def resolve_personal_tutor(self,table,action):
        return resolve_historical_search(self,action.actor,'personal_tutor')
