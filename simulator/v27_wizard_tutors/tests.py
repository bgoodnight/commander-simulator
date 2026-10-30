import unittest
from wizard_tutor_table import WizardTutorTable,FABRICATE,STEP,WIZARDCYCLING

class WizardTutorTests(unittest.TestCase):
 def setUp(self):
  self.t=WizardTutorTable(seed=2701);self.t.active_seat=0;self.t.phase='main';self.t.spell_stack.holder=0;self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def library(self,name):return self.t.zones.move(self.give(name).object_id,'library')
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def cycle(self):
  oid=self.give(STEP).object_id
  self.t.spell_stack.holder=0
  c=next(c for c in self.t.priority_choices(0) if c.kind=='wizardcycle' and c.source_id==oid)
  self.t.commit_choice(0,c);return oid
 def test_fabricate_finds_artifact_to_hand(self):
  self.library('Phyrexian Altar');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Phyrexian Altar')
  self.cast(FABRICATE);self.assertIn('Phyrexian Altar',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_fabricate_rejects_nonartifact(self):
  bad=self.library('Ponder');self.t.tutor_policy=lambda r:bad
  with self.assertRaises(ValueError):self.cast(FABRICATE)
 def test_fabricate_fails_to_find_and_shuffles(self):
  self.t.tutor_policy=lambda r:None;before=len(self.t.zones.operations);self.cast(FABRICATE)
  self.assertTrue(any(x[0]=='shuffle' for x in self.t.zones.operations[before:]))
 def test_wizardcycling_finds_spellseeker(self):
  self.library('Spellseeker');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Spellseeker')
  oid=self.cycle();self.assertNotIn(oid,self.t.rules.objects);self.assertIn(STEP,self.p.graveyard)
  self.assertEqual(self.t.spell_stack.frames[-1].kind,'activated')
  self.t.spell_stack.resolve();self.assertIn('Spellseeker',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_wizardcycling_rejects_nonwizard(self):
  bad=self.library('Young Pyromancer');self.t.tutor_policy=lambda r:bad;self.cycle()
  with self.assertRaises(ValueError):self.t.spell_stack.resolve()
 def test_wizardcycling_is_not_a_spell(self):
  self.cast('Young Pyromancer');before=self.t.spell_stack.spells_resolved;self.cycle();self.t.spell_stack.resolve()
  self.assertEqual(self.t.spell_stack.spells_resolved,before)
  self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),0)
 def test_wizardcycling_available_on_opponents_turn(self):
  self.give(STEP);self.t.active_seat=1;self.assertTrue(any(c.kind=='wizardcycle' for c in self.t.priority_choices(0)))
 def test_counter_ability_still_pays_discard(self):
  self.cycle();f=self.t.spell_stack.frames[-1];self.assertIsNotNone(self.t.spell_stack.counter(f.frame_id,{'activated'},1))
  self.t.spell_stack.resolve();self.assertIn(STEP,self.p.graveyard);self.assertFalse(any(x[0]=='wizardcycling' for x in self.t.tutor_events))
 def test_unpayable_cycle_is_not_offered(self):
  self.give(STEP);self.t.rules.mana_pools[0]=(0,0,0)
  self.assertFalse(any(c.kind=='wizardcycle' for c in self.t.priority_choices(0)))
 def test_spell_mode_remains_unsupported(self):
  c=self.give(STEP);self.assertEqual(c.effect,'unsupported')
 def test_fabricate_sapphire_reduction(self):
  self.cast('Sapphire Medallion');a=self.t.action_for_card(self.p,self.give(FABRICATE));self.assertEqual((a.cost,a.parameters['U']),(2,1))

 def test_added_wizard_type_is_searchable(self):
  from dataclasses import replace
  from rules import Ability
  perm=self.t.add_permanent(self.p,'type_effect',0,'fixture adaptation')
  obj=self.t.rules.get(perm.id)
  obj.card=replace(obj.card,abilities=(Ability('static',op='add_creature_subtype',args=(('subtype','Wizard'),)),))
  self.t.rules._dirty();self.library('Young Pyromancer')
  self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Young Pyromancer')
  self.cycle();self.t.spell_stack.resolve()
  self.assertIn('Young Pyromancer',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_cycling_not_discounted_by_medallion(self):
  self.cast('Sapphire Medallion');self.t.rules.mana_pools[0]=(1,0,0);self.give(STEP)
  self.assertFalse(any(c.kind=='wizardcycle' for c in self.t.priority_choices(0)))
 def test_cycling_choice_at_resolution(self):
  self.library('Spellseeker');self.cycle()
  self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Spellseeker')
  self.t.spell_stack.resolve();self.assertIn('Spellseeker',[c.name for c in self.p.hand])

if __name__=='__main__':unittest.main()
