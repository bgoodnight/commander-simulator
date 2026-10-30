"""Step Through's sorcery and battlefield 'whenever you cycle' triggers."""
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v28_spellseeker'))
from spellseeker_table import SpellseekerTable
from wizard_tutor_table import STEP
from priority import Choice
from rules import Cost, Event
from simulation import Action

class StepCyclingTable(SpellseekerTable):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        key='named:'+STEP
        self.zones.specs[key]=replace(self.zones.specs[key],kind=STEP,card_type='sorcery',effect='named_step_through',
            mana_value=5,colored_cost=MappingProxyType({'U':2,'R':0}),parameters=MappingProxyType({'coverage':'verified_subset'}))
        for obj in self.rules.objects.values():
            if obj.card.card_id==key:obj.card=replace(obj.card,types=frozenset({'sorcery'}),cost=Cost(3,2),coverage='verified_subset')
        self.rules._dirty();self.register_effect('named_step_through',self.resolve_step_through)

    def legal_step_targets(self,seat):
        return tuple(o.object_id for o in self.rules.on_battlefield() if self.rules.legal_target(seat,o.object_id,{'creature'}))

    def action_for(self,player,card):
        if card.name!=STEP:return super().action_for(player,card)
        cost=self.rules.modified_cost(player.seat,frozenset({'sorcery'}),Cost(3,2))
        a=Action(player.seat,STEP,'sorcery',card.effect,cost.total,parameters={**card.parameters,'U':2,'R':0})
        a=self.adjust_named_action_cost(a)
        options=sorted(self.legal_step_targets(player.seat),key=lambda oid:self.rules.get(oid).controller==player.seat)
        a.step_targets=tuple(options[:2])
        return a

    def step_action(self,player,card,targets):
        a=self.action_for(player,card);a.step_targets=tuple(targets);return a

    def targets_legal(self,action):
        if action.effect!='named_step_through':return super().targets_legal(action)
        targets=getattr(action,'step_targets',())
        if not isinstance(targets,tuple) or len(targets)!=2 or len(set(targets))!=2:return False
        legal=self.legal_step_targets(action.actor)
        if id(action) in self._spells:return any(oid in legal for oid in targets)
        return all(oid in legal for oid in targets)

    def resolve_step_through(self,table,action):
        for oid in action.step_targets:
            if oid in self.legal_step_targets(action.actor):
                self.world.move(oid,'hand','bounce')

    def priority_choices(self,seat):
        choices=[c for c in super().priority_choices(seat) if c.kind!='spell' or c.action.source!=STEP]
        if seat==self.active_seat and self.phase=='main' and not self.spell_stack.frames:
            for card in self.players[seat].hand:
                if card.name!=STEP:continue
                a=self.action_for(self.players[seat],card)
                if self.can_pay(self.players[seat],a):
                    for pair in combinations(self.legal_step_targets(seat),2):
                        candidate=replace(a);candidate.step_targets=pair;choices.append(Choice('spell',action=candidate))
        return tuple(choices)

    def emit(self,name,action=None,**payload):
        result=super().emit(name,action,**payload)
        if name=='cycled':
            event=Event('cycled',payload['controller'],payload['source_id'])
            self._apply_pending(self.rules.triggers(event))
        return result
