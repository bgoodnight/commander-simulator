"""Cyclonic Rift: targeted and overloaded instant modes."""
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v31_premium_deck'))
from premium_table import PremiumTable
from priority import Choice
from rules import Cost
from simulation import Action

RIFT='Cyclonic Rift'
PERMANENT_TYPES={'creature','artifact','enchantment','planeswalker','battle'}

class RiftTable(PremiumTable):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  key='named:'+RIFT
  self.zones.specs[key]=replace(self.zones.specs[key],kind=RIFT,card_type='instant',effect='named_cyclonic_rift',
   mana_value=2,colored_cost=MappingProxyType({'U':1,'R':0}),parameters=MappingProxyType({'coverage':'verified_subset'}))
  for obj in self.rules.objects.values():
   if obj.card.card_id==key:obj.card=replace(obj.card,types=frozenset({'instant'}),cost=Cost(1,1),coverage='verified_subset')
  self.rules._dirty();self.register_effect('named_cyclonic_rift',self.resolve_rift)
 def adjust_named_action_cost(self,action):
  if action.source!=RIFT:return super().adjust_named_action_cost(action)
  n=sum(o.card.name=='Sapphire Medallion' for o in self.rules.controlled(action.actor))
  action.cost=max(action.parameters.get('U',0)+action.parameters.get('R',0),action.cost-n)
  return action
 def rift_target_legal(self,seat,oid):
  obj=self.rules.objects.get(oid)
  return bool(obj and obj.controller!=seat and 'land' not in obj.types and self.rules.legal_target(seat,oid,PERMANENT_TYPES))
 def rift_action(self,player,card,overload=False,target=None):
  if type(overload) is not bool:raise ValueError('Overload choice must be boolean')
  cost=self.rules.modified_cost(player.seat,frozenset({'instant'}),Cost(6 if overload else 1,1))
  a=Action(player.seat,RIFT,'instant',card.effect,cost.total,parameters={**card.parameters,'U':1,'R':0,'overload':overload},tags=('overload',) if overload else ())
  a=self.adjust_named_action_cost(a)
  if not overload:
   if target is None:target=next((o.object_id for o in self.rules.on_battlefield() if self.rift_target_legal(player.seat,o.object_id)),None)
   if target in self.rules.objects:a.target_object=target;a.target=self.rules.get(target).controller
  elif target is not None:raise ValueError('Overloaded Rift has no target')
  return a
 def action_for(self,player,card):
  if card.name==RIFT:return self.rift_action(player,card)
  return super().action_for(player,card)
 def expected_action(self,player,card,announced=None):
  if card.name==RIFT:
   tags=announced.tags if announced else ()
   if tags not in ((),('overload',)):raise ValueError('Unknown Rift casting mode')
   return self.rift_action(player,card,overload=bool(tags))
  return super().expected_action(player,card,announced)
 def targets_legal(self,action):
  if action.effect!='named_cyclonic_rift':return super().targets_legal(action)
  if action.parameters.get('overload') is True:return action.target_object is None
  if action.parameters.get('overload') is not False:return False
  return self.rift_target_legal(action.actor,action.target_object)
 def resolve_rift(self,table,action):
  if action.parameters['overload']:
   ids=[o.object_id for o in self.rules.on_battlefield() if o.controller!=action.actor and 'land' not in o.types and o.types & PERMANENT_TYPES]
  else:ids=[action.target_object]
  for oid in ids:
   if oid in self.rules.objects:self.world.move(oid,'hand','bounce')
  self.rule_events.append(('cyclonic_rift',action.actor,action.parameters['overload'],tuple(ids)))
 def priority_choices(self,seat):
  choices=[c for c in super().priority_choices(seat) if c.kind!='spell' or c.action.source!=RIFT]
  player=self.players[seat]
  for card in player.hand:
   if card.name!=RIFT:continue
   for obj in tuple(self.rules.on_battlefield()):
    if self.rift_target_legal(seat,obj.object_id):
     a=self.rift_action(player,card,target=obj.object_id)
     if self.can_pay(player,a):choices.append(Choice('spell',action=a))
   a=self.rift_action(player,card,overload=True)
   if self.can_pay(player,a):choices.append(Choice('spell',action=a))
  return tuple(choices)
