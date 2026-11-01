"""Reiterate and bounded, nonphysical instant/sorcery stack copies."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v32_cyclonic_rift'))
from rift_table import RiftTable,RIFT
from spellseeker_table import SeekerStack
from priority import Choice
from rules import Cost,Event
from simulation import Action
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from commander_sim.legacy_spell_copy import prepare_reviewed_spell_copy,commit_reviewed_spell_copy
import integrated as v6

NAME='Reiterate'
# Only effects with representable modes, targets and copy-safe resolution.
COPY_EFFECTS={'named_cyclonic_rift','named_capsize','named_consider','named_selection',
              'named_fabricate','named_mystical_tutor','named_merchant_scroll',
              'named_solve_equation','named_personal_tutor'}

class ReiterateTable(RiftTable):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.spell_stack=SeekerStack(self);self.copy_actions=set();self.copy_counter_types={}
  key='named:'+NAME
  self.zones.specs[key]=replace(self.zones.specs[key],kind=NAME,card_type='instant',effect='named_reiterate',
   mana_value=3,colored_cost=MappingProxyType({'U':0,'R':2}),parameters=MappingProxyType({'coverage':'partial'}))
  for obj in self.rules.objects.values():
   if obj.card.card_id==key:obj.card=replace(obj.card,types=frozenset({'instant'}),cost=Cost(1,red=2),coverage='verified_subset')
  self.rules._dirty();self.register_effect('named_reiterate',self.resolve_reiterate)
 def copy_target_legal(self,frame_id):
  frame=self.spell_stack.get(frame_id)
  return bool(frame and frame.kind=='spell' and frame.action.card_type in ('instant','sorcery') and (frame.action.effect in COPY_EFFECTS or frame.action.effect=='counter' and frame.action.source in v6.COUNTERS))
 def reiterate_action(self,player,card,buyback=False,target=None):
  if type(buyback) is not bool:raise ValueError('Buyback choice must be boolean')
  cost=self.rules.modified_cost(player.seat,frozenset({'instant'}),Cost(4 if buyback else 1,red=2))
  a=Action(player.seat,NAME,'instant',card.effect,cost.total,parameters={**card.parameters,'U':0,'R':2,'buyback':buyback},tags=('buyback',) if buyback else ())
  if target is not None:a.target_object=target
  return a
 def action_for(self,player,card):
  if card.name==NAME:return self.reiterate_action(player,card)
  return super().action_for(player,card)
 def expected_action(self,player,card,announced=None):
  if card.name==NAME:
   tags=announced.tags if announced else ()
   if tags not in ((),('buyback',)):raise ValueError('Unknown Reiterate casting mode')
   return self.reiterate_action(player,card,buyback=bool(tags))
  return super().expected_action(player,card,announced)
 def counter_allowed(self,action,target):
  allowed=self.copy_counter_types.get(id(action))
  if allowed is None:return super().counter_allowed(action,target)
  return target.kind=='spell' and (target.action.card_type in allowed or 'noncreature' in allowed and target.action.card_type!='creature')
 def targets_legal(self,action):
  if action.effect=='named_reiterate':return self.copy_target_legal(action.target_object)
  return super().targets_legal(action)
 def priority_choices(self,seat):
  choices=[c for c in super().priority_choices(seat) if c.kind!='spell' or c.action.source!=NAME]
  player=self.players[seat]
  for card in player.hand:
   if card.name!=NAME:continue
   for frame in self.spell_stack.frames:
    if not self.copy_target_legal(frame.frame_id):continue
    for buyback in (False,True):
     action=self.reiterate_action(player,card,buyback=buyback,target=frame.frame_id)
     if self.can_pay(player,action):choices.append(Choice('spell',action=action))
  return tuple(choices)
 def choose_priority(self,seat,choices):
  selected=super().choose_priority(seat,choices)
  if selected is not None:return selected
  candidates=[c for c in choices if c.kind=='spell' and c.action.source==NAME and
              (f:=self.spell_stack.get(c.action.target_object)) is not None and f.controller==seat]
  return next((c for c in candidates if c.action.parameters['buyback']),None) or next(iter(candidates),None)
 def is_virtual_spell(self,action):return id(action) in self.copy_actions
 def stack_action_active(self,action):
  return self.is_virtual_spell(action) or super().stack_action_active(action)
 def resolve_reiterate(self,table,action):
  original=self.spell_stack.get(action.target_object)
  if not original or not self.copy_target_legal(original.frame_id):raise AssertionError('Illegal copy target after check')
  copied=prepare_reviewed_spell_copy(self,original.action,action.actor,
    allowed_effects=frozenset({'named_cyclonic_rift','named_capsize'}),
    counter_types=v6.COUNTERS)
  commit_reviewed_spell_copy(self,copied,action.actor,Event,v6.COUNTERS)
 def emit(self,name,action=None,**payload):
  if name=='spell_resolved' and action is not None and action.source==NAME and action.parameters.get('buyback'):
   ticket=self._spells.pop(id(action),None)
   if ticket and ticket.object_id in self.rules.objects:
    self.zones.move(ticket.object_id,'hand');self.zones._pending.pop(ticket.object_id,None)
    self.rules.events.append(Event(name,action.actor,ticket.object_id,spell_types=ticket.spell_types))
    self.note('    Reiterate buyback returns to hand.')
  result=super().emit(name,action,**payload)
  if action is not None and name in ('spell_resolved','spell_countered'):
   self.copy_actions.discard(id(action));self.copy_counter_types.pop(id(action),None)
  return result
 def fizzle_spell(self,action):
  result=super().fizzle_spell(action);self.copy_actions.discard(id(action));self.copy_counter_types.pop(id(action),None);return result
