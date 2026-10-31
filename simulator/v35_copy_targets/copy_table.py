"""Additional copied-spell target handling for Reiterate."""
from dataclasses import replace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v34_mage_siege'))
from adventure_table import AdventureTable
from rules import Event
import integrated as v6

EXTRA={'named_step_through','named_abrade','named_reiterate'}

class CopyTable(AdventureTable):
 def copy_target_legal(self,frame_id):
  frame=self.spell_stack.get(frame_id)
  if frame and frame.kind=='spell' and frame.action.card_type in ('instant','sorcery') and frame.action.effect in EXTRA:return True
  return super().copy_target_legal(frame_id)
 def targets_legal(self,action):
  if action.effect=='named_step_through' and id(action) in self.copy_actions:
   targets=getattr(action,'step_targets',())
   if not isinstance(targets,tuple) or len(targets)!=2 or len(set(targets))!=2:return False
   legal=self.legal_step_targets(action.actor)
   return any(oid in legal for oid in targets)
  return super().targets_legal(action)
 def resolve_reiterate(self,table,action):
  frame=self.spell_stack.get(action.target_object)
  if not frame or not self.copy_target_legal(frame.frame_id):raise AssertionError('Illegal copy target')
  original=frame.action;copied=replace(original,actor=action.actor)
  policy=getattr(self,'copy_target_policy',None)
  if original.effect=='named_step_through':
   old=getattr(original,'step_targets',())
   chosen=tuple(policy(action.actor,original)) if policy else old
   if len(chosen)!=2 or len(set(chosen))!=2:raise ValueError('Copy requires two distinct targets')
   legal=self.legal_step_targets(action.actor)
   if any(new!=prior and new not in legal for new,prior in zip(chosen,old)):raise ValueError('Illegal changed copy target')
   copied.step_targets=chosen
  elif policy and original.target_object is not None:
   chosen=policy(action.actor,original)
   if chosen!=original.target_object:
    if original.effect=='counter':
     target=self.spell_stack.get(chosen);allowed=v6.COUNTERS[original.source]
     if not target or target.kind!='spell' or not (target.action.card_type in allowed or 'noncreature' in allowed and target.action.card_type!='creature'):raise ValueError('Illegal copied counterspell target')
     copied=replace(copied,target_object=chosen,target=target.controller)
    elif original.effect=='named_reiterate':
     if not self.copy_target_legal(chosen):raise ValueError('Illegal copied Reiterate target')
     copied=replace(copied,target_object=chosen)
    elif original.effect in {'named_cyclonic_rift','named_capsize','named_abrade'}:
     if chosen not in self.rules.objects:raise ValueError('Invalid copy target')
     trial=replace(copied,target_object=chosen,target=self.rules.get(chosen).controller)
     if not self.targets_legal(trial):raise ValueError('Illegal copy target')
     copied=trial
    else:raise ValueError('Retargeting not implemented for this spell')
  self.copy_actions.add(id(copied))
  if copied.effect=='counter':self.copy_counter_types[id(copied)]=v6.COUNTERS[copied.source]
  self.spell_stack.spell(copied,None)
  event=Event('spell_copied',action.actor,spell_types=frozenset({copied.card_type}))
  self.rules.events.append(event);self._apply_pending(self.rules.triggers(event))
  self.note(f'    COPY P{action.actor}: {copied.source} copied onto stack (not cast).')
