"""Lindblum's Mage Siege Adventure and its triggered Wizard token."""
from dataclasses import replace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v33_reiterate'))
from reiterate_table import ReiterateTable
from spellseeker_table import SeekerStack
from priority import Choice
from zones import CastTicket
from rules import Cost,Event,Ability,CardDefinition
from simulation import Action

LAND='Lindblum, Industrial Regency';SPELL='Mage Siege'
WIZARD=CardDefinition('mage_siege_wizard','Wizard',frozenset({'creature'}),frozenset({'Wizard'}),
 base_power=0,base_toughness=1,colors=frozenset({'B'}),abilities=(
 Ability('triggered',event='spell_cast',op='mage_siege_damage',condition='controller_cast_noncreature'),))

class AdventureStack(SeekerStack):
 trigger_operations=SeekerStack.trigger_operations|{'mage_siege_damage'}

class AdventureTable(ReiterateTable):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.spell_stack=AdventureStack(self)
  self.adventure_exiled=set();self.adventure_tickets={}
  self.register_effect('named_mage_siege',self.resolve_mage_siege)
 def copy_target_legal(self,frame_id):
  frame=self.spell_stack.get(frame_id)
  if frame and frame.kind=='spell' and frame.action.effect=='named_mage_siege':return True
  return super().copy_target_legal(frame_id)
 def adventure_cost(self,seat):
  return self.rules.modified_cost(seat,frozenset({'instant'}),Cost(2,red=1))
 def adventure_available(self,seat,oid):
  obj=self.rules.objects.get(oid)
  return bool(obj and obj.owner==seat and obj.zone=='hand' and obj.card.name==LAND
   and self.resources.plan(seat,self.adventure_cost(seat)) is not None)
 def priority_choices(self,seat):
  choices=list(super().priority_choices(seat))
  for oid in self.zones.ids(seat,'hand'):
   if self.adventure_available(seat,oid):choices.append(Choice('adventure',source_id=oid))
  if seat==self.active_seat and self.phase=='main' and not self.spell_stack.frames and getattr(self.players[seat],'_land_turn',None)!=self.safe_runner.turn:
   for oid in self.zones.ids(seat,'exile'):
    if oid in self.adventure_exiled and self.rules.get(oid).card.name==LAND:choices.append(Choice('adventure_land',source_id=oid))
  return tuple(choices)
 def choose_priority(self,seat,choices):
  selected=super().choose_priority(seat,choices)
  if selected is not None:return selected
  normal=seat==self.active_seat and self.phase=='main' and not self.spell_stack.frames
  if normal:
   land=next((c for c in choices if c.kind=='adventure_land'),None)
   if land:return land
   if self.main_actions<12:return next((c for c in choices if c.kind=='adventure'),None)
  return None
 def commit_choice(self,seat,choice):
  if choice.kind=='adventure':return self.cast_adventure(seat,choice.source_id)
  if choice.kind=='adventure_land':return self.play_adventure_land(seat,choice.source_id)
  return super().commit_choice(seat,choice)
 def cast_adventure(self,seat,oid):
  s=self.spell_stack
  if s.resolving or s.running and s.holder!=seat:raise ValueError('No priority')
  if not s.running and (seat!=self.active_seat or self.phase!='main' or s.frames or s.pending):raise ValueError('No priority')
  if not self.adventure_available(seat,oid):raise ValueError('Adventure unavailable or unpayable')
  player=self.players[seat];cost=self.adventure_cost(seat)
  action=Action(seat,SPELL,'instant','named_mage_siege',cost.total,parameters={'U':0,'R':1})
  self.safe_runner.check((seat,SPELL,player.mana,tuple(c.object_id for c in player.hand)),stack_depth=1)
  self.resources.pay(seat,cost)
  if seat==self.active_seat and not s.frames:self.main_actions+=1
  new=self.zones.move(oid,'stack');obj=self.rules.get(new);original=obj.card
  obj.card=replace(original,name=SPELL,types=frozenset({'instant'}),subtypes=frozenset({'Adventure'}),cost=Cost(2,red=1),coverage='verified_subset')
  self.rules._dirty()
  ticket=CastTicket(new,seat,frozenset({'instant'}),SPELL);self.zones._pending[new]=ticket
  self._spells[id(action)]=ticket;self.adventure_tickets[id(action)]=original
  player.cards_cast+=1;player.mana_spent+=cost.total;self.counts['casts']+=1
  if player is self.details:player.coverage['supported']+=1
  self.note(f'  P{seat} casts Mage Siege as Adventure for {cost.total}.')
  self.emit('spell_cast',action);s.resolve(action)
  if not player.alive:self.eliminate(player,'empty_library')
  self._world_actions+=1;self.assert_consistent();return True
 def play_adventure_land(self,seat,oid):
  s=self.spell_stack;player=self.players[seat];obj=self.rules.objects.get(oid)
  if (not obj or obj.owner!=seat or obj.zone!='exile' or oid not in self.adventure_exiled or obj.card.name!=LAND
   or seat!=self.active_seat or self.phase!='main' or s.frames or s.pending or s.resolving
   or s.running and s.holder!=seat or getattr(player,'_land_turn',None)==self.safe_runner.turn):raise ValueError('Adventure land unavailable')
  choices=self.entry_choices(player,oid);new=self.enter_land(player,oid,cause='land_play',choices=choices)
  player._land_turn=self.safe_runner.turn;self.adventure_exiled.discard(oid)
  self.emit('land_played',controller=seat,round=self.round_num,object_id=new)
  return True
 def resolve_mage_siege(self,table,action):
  self.add_creature(self.players[action.actor],0,1,'Wizard',token=True,definition=WIZARD)
  self.note('    MAGE SIEGE: create a 0/1 black Wizard token.')
 def resolve_trigger(self,item):
  if item.op!='mage_siege_damage':return super().resolve_trigger(item)
  actor=self.players[item.controller]
  targets={p.seat:1 for p in self.rivals(actor)}
  self.damage_many(targets,actor,'mage_siege_wizard')
 def emit(self,name,action=None,**payload):
  if action is not None and id(action) in getattr(self,'adventure_tickets',{}) and name in ('spell_resolved','spell_countered'):
   original=self.adventure_tickets.pop(id(action));ticket=self._spells.get(id(action))
   if ticket and ticket.object_id in self.rules.objects:
    self.rules.get(ticket.object_id).card=original;self.rules._dirty()
    if name=='spell_resolved':
     self._spells.pop(id(action));new=self.zones.move(ticket.object_id,'exile')
     self.zones._pending.pop(ticket.object_id,None);self.adventure_exiled.add(new)
     self.rules.events.append(Event(name,action.actor,ticket.object_id,spell_types=ticket.spell_types))
     self.note('    Mage Siege resolves: Lindblum is exiled on Adventure.')
  return super().emit(name,action,**payload)
