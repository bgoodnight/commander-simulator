"""Printed spell color metadata and Sapphire Medallion's generic reduction."""
from pathlib import Path
from dataclasses import replace
from types import MappingProxyType
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v22_consider'))
from consider_table import ConsiderTable
from simulation import Action
from rules import Cost

COLORS=json.loads(Path(__file__).with_name('CARD_COLORS.json').read_text())['colors']

class MedallionTable(ConsiderTable):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        key='named:Sapphire Medallion'
        self.zones.specs[key]=replace(self.zones.specs[key],kind='Sapphire Medallion',card_type='artifact',
            effect='named_medallion',mana_value=2,colored_cost=MappingProxyType({'U':0,'R':0}),
            parameters=MappingProxyType({'coverage':'verified_subset'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id==key:obj.card=replace(obj.card,types=frozenset({'artifact'}),cost=Cost(generic=2),coverage='verified_subset')
        self.rules._dirty();self.register_effect('named_medallion',self.resolve_medallion)

    def adjust_named_action_cost(self,action):
        # Printed colors only; color-changing effects are outside this milestone.
        if 'U' not in COLORS.get(action.source,()):return action
        n=sum(o.card.name=='Sapphire Medallion' for o in self.rules.controlled(action.actor))
        floor=action.parameters.get('U',0)+action.parameters.get('R',0)
        action.cost=max(floor,action.cost-n)
        return action

    def action_for(self,player,card):
        if card.name=='Sapphire Medallion':
            return Action(player.seat,card.name,'artifact',card.effect,2,parameters={**card.parameters,'U':0,'R':0})
        action=super().action_for(player,card)
        # v11 card actions call the cost hook while they are constructed.
        if card.name in ('Abrade','Capsize','Arcane Adaptation'):return action
        return self.adjust_named_action_cost(action)

    def resolve_medallion(self,table,action):
        self.add_permanent(self.players[action.actor],'combo_piece',0,action.source)
