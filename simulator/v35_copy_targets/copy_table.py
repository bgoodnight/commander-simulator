"""Additional copied-spell target handling for Reiterate."""
from dataclasses import replace
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v34_mage_siege'))
from adventure_table import AdventureTable
from rules import Event
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from commander_sim.legacy_spell_copy import prepare_reviewed_spell_copy,commit_reviewed_spell_copy
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
  copied=prepare_reviewed_spell_copy(self,frame.action,action.actor,
    allowed_effects=frozenset({'named_step_through','counter','named_reiterate',
      'named_cyclonic_rift','named_capsize','named_abrade'}),
    counter_types=v6.COUNTERS)
  commit_reviewed_spell_copy(self,copied,action.actor,Event,v6.COUNTERS,reuse_event=True)
