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
        seat=action.actor; ids=self.zones.ids(seat,'library')
        if action.source==MERCHANT:
            # An unknown printed color cannot safely be treated as nonblue.
            candidates=[oid for oid in ids if 'instant' in self.rules.get(oid).types]
            if any(self.rules.get(oid).card.name not in COLORS for oid in candidates):
                raise NotImplementedError('Merchant Scroll requires known instant colors')
            eligible=tuple(oid for oid in candidates if 'U' in COLORS[self.rules.get(oid).card.name])
            request_kind='merchant_scroll'
        elif action.source==SOLVE:
            eligible=tuple(oid for oid in ids if self.rules.get(oid).types & {'instant','sorcery'})
            request_kind='solve_equation'
        else:raise ValueError('Unknown search spell')
        request=self.selection.request(request_kind,seat,eligible)
        ranked=sorted(request.cards,key=lambda c:-self.selection.score(seat,c))
        default=ranked[0].object_id if ranked else None
        policy=getattr(self,'tutor_policy',None)
        chosen=policy(request) if policy else default
        if chosen is not None and chosen not in eligible:raise ValueError('Search must choose an eligible card or fail to find')
        name=self.rules.get(chosen).card.name if chosen is not None else None
        new_id=self.zones.move(chosen,'hand') if chosen is not None else None
        self.zones.shuffle(seat)
        self.tutor_events.append((request_kind,seat,new_id,name))
        self.note(f'    {action.source.upper()} P{seat}: revealed {name}, put into hand, then shuffled.')
