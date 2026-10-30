"""Personal Tutor on the canonical-deck table."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v24_reinforcements'))
from reinforcements_table import ReinforcementTable
from rules import Cost
from simulation import Action

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
        seat=action.actor
        eligible=tuple(oid for oid in self.zones.ids(seat,'library') if 'sorcery' in self.rules.get(oid).types)
        request=self.selection.request('personal_tutor',seat,eligible)
        ranked=sorted(request.cards,key=lambda c:-self.selection.score(seat,c))
        default=ranked[0].object_id if ranked else None
        policy=getattr(self,'tutor_policy',None)
        chosen=policy(request) if policy else default
        if chosen is not None and chosen not in eligible:raise ValueError('Personal Tutor must choose a sorcery in library or fail to find')
        name=self.rules.get(chosen).card.name if chosen is not None else None
        self.zones.shuffle(seat)
        if chosen is not None:
            order=self.zones.order[seat,'library'];order.remove(chosen);order.append(chosen);self.rules._dirty()
        self.tutor_events.append(('personal_tutor',seat,chosen,name))
        self.note(f'    PERSONAL TUTOR P{seat}: revealed {name}; shuffled, then placed on top.')
