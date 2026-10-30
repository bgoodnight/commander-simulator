"""Ral's Reinforcements creates blue/red Elementals on the shared battlefield."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v23_medallion'))
from medallion_table import MedallionTable
from rules import Cost,CardDefinition
from simulation import Action

NAME="Ral's Reinforcements"
RAL_TOKEN=CardDefinition('ral_elemental_1_1','Elemental',frozenset({'creature'}),frozenset({'Elemental'}),
                         base_power=1,base_toughness=1,colors=frozenset({'U','R'}))

class ReinforcementTable(MedallionTable):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        key='named:'+NAME
        self.zones.specs[key]=replace(self.zones.specs[key],kind=NAME,card_type='sorcery',
             effect='named_reinforcements',mana_value=2,colored_cost=MappingProxyType({'U':0,'R':1}),
             parameters=MappingProxyType({'coverage':'verified_subset'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id==key:
                obj.card=replace(obj.card,types=frozenset({'sorcery'}),cost=Cost(generic=1,red=1),coverage='verified_subset')
        self.rules._dirty();self.register_effect('named_reinforcements',self.resolve_reinforcements)

    def action_for(self,player,card):
        if card.name!=NAME:return super().action_for(player,card)
        cost=self.rules.modified_cost(player.seat,frozenset({'sorcery'}),Cost(generic=1,red=1))
        action=Action(player.seat,NAME,'sorcery',card.effect,cost.total,parameters={**card.parameters,'U':0,'R':1})
        return self.adjust_named_action_cost(action)

    def resolve_reinforcements(self,table,action):
        player=self.players[action.actor]
        for _ in range(2):self.add_creature(player,1,1,'Elemental',token=True,definition=RAL_TOKEN)
        self.note(f'    REINFORCEMENTS P{action.actor}: two blue/red Elementals created.')
