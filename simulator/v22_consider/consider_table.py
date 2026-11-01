"""Consider: surveil one, then draw, in the canonical-deck table."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v21_early_mana'))
from mana_table import EarlyManaTable
from rules import Cost
from simulation import Action
from commander_sim.legacy_common_ops import DrawDiscard, apply_draw_discard

class ConsiderTable(EarlyManaTable):
    def __init__(self,*args,**kwargs):
        self.consider_events=[]
        super().__init__(*args,**kwargs)
        key='named:Consider'
        spec=self.zones.specs[key]
        self.zones.specs[key]=replace(spec,kind='Consider',card_type='instant',effect='named_consider',
                                     mana_value=1,colored_cost=MappingProxyType({'U':1,'R':0}),
                                     parameters=MappingProxyType({'coverage':'verified_subset'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id==key:
                obj.card=replace(obj.card,types=frozenset({'instant'}),cost=Cost(blue=1),coverage='verified_subset')
        self.rules._dirty()
        self.register_effect('named_consider',self.resolve_consider)

    def action_for(self,player,card):
        if card.name!='Consider':return super().action_for(player,card)
        cost=self.rules.modified_cost(player.seat,frozenset({'instant'}),Cost(blue=1))
        return Action(player.seat,card.name,'instant',card.effect,cost.total,
                      parameters={**card.parameters,'U':1,'R':0})

    def resolve_consider(self,table,action):
        seat=action.actor;player=self.players[seat]
        ids=self.zones.ids(seat,'library');top=ids[-1] if ids else None
        policy=getattr(self,'consider_policy',None)
        to_graveyard=policy(seat,top) if policy and top is not None else False
        if type(to_graveyard) is not bool:raise ValueError('Consider surveil choice must be boolean')
        if top is not None and to_graveyard:self.zones.move(top,'graveyard','resolve')
        self.consider_events.append((seat,top,to_graveyard))
        self.note(f'    CONSIDER P{seat}: surveil card #{top}, move to graveyard={to_graveyard}; draw one.')
        apply_draw_discard(self,seat,DrawDiscard(draw=1))
        if not player.alive:self.eliminate(player,'empty_library')
