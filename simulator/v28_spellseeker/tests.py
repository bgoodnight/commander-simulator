import unittest
from spellseeker_table import SpellseekerTable,NAME,library_mana_value
from wizard_tutor_table import STEP

class SpellseekerTests(unittest.TestCase):
 def setUp(self):
  self.t=SpellseekerTable(seed=2801);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def library(self,name):return self.t.zones.move(self.give(name).object_id,'library')
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def test_spellseeker_finds_consider(self):
  self.library('Consider');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Consider')
  self.cast(NAME);self.assertIn('Consider',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_mana_value_x_is_zero_in_library(self):
  self.assertEqual(library_mana_value('Crackle with Power'),2);self.assertEqual(library_mana_value('Gitaxian Probe'),1)
 def test_high_cost_excluded_even_if_reduced(self):
  bad=self.library('Solve the Equation');self.t.tutor_policy=lambda r:bad
  with self.assertRaises(ValueError):self.cast(NAME)
 def test_optional_decline_does_not_shuffle(self):
  self.t.spellseeker_search_policy=lambda seat,oid:False;before=len(self.t.zones.operations)
  self.cast(NAME);self.assertFalse(any(x[0]=='shuffle' for x in self.t.zones.operations[before:]))
 def test_search_and_fail_to_find_shuffles(self):
  self.t.tutor_policy=lambda r:None;before=len(self.t.zones.operations);self.cast(NAME)
  self.assertTrue(any(x[0]=='shuffle' for x in self.t.zones.operations[before:]))
 def test_harmonic_doubles_wizard_enter_trigger(self):
  self.cast('Harmonic Prodigy');self.t.tutor_policy=lambda r:None;self.cast(NAME)
  self.assertEqual(sum(e[0]=='spellseeker' for e in self.t.tutor_events),2)
 def test_sapphire_reduces_blue_creature(self):
  self.cast('Sapphire Medallion');a=self.t.action_for_card(self.p,self.give(NAME))
  self.assertEqual((a.cost,a.parameters['U']),(2,1))
 def test_step_through_into_spellseeker_then_search(self):
  self.library(NAME);self.library('Consider');step=self.give(STEP);self.t.spell_stack.holder=0
  self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name==({'wizardcycling':NAME,'spellseeker':'Consider'}[r.kind]))
  choice=next(c for c in self.t.priority_choices(0) if c.kind=='wizardcycle' and c.source_id==step.object_id)
  self.t.commit_choice(0,choice);self.t.spell_stack.resolve();self.cast(NAME)
  self.assertIn('Consider',[c.name for c in self.p.hand]);self.t.assert_consistent()

 def test_trigger_survives_source_return_in_response(self):
  self.library('Consider');self.give('Capsize');used=[]
  self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Consider')
  def policy(seat,frames,choices):
   if seat==0 and frames and frames[-1].kind=='triggered' and not used:
    source=frames[-1].source_id
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Capsize' and c.action.target_object==source and not c.action.tags),None)
    if c:used.append(True);return c
   return None
  self.t.priority_policy=policy;self.cast(NAME)
  self.assertTrue(used);self.assertIn(NAME,[c.name for c in self.p.hand])
  self.assertIn('Consider',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_spellseeker_creature_is_not_cast_trigger(self):
  self.cast('Young Pyromancer');self.t.tutor_policy=lambda r:None;self.cast(NAME)
  self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),0)
 def test_unknown_mana_value_fails_closed(self):
  with self.assertRaises(NotImplementedError):library_mana_value('unknown')

if __name__=='__main__':unittest.main()
