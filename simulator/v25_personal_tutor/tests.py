import unittest
from personal_tutor_table import PersonalTutorTable,NAME

class PersonalTutorTests(unittest.TestCase):
 def setUp(self):
  self.t=PersonalTutorTable(seed=2501);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *args:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def test_find_sorcery(self):
  self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=="Ral's Reinforcements")
  self.cast(NAME);self.assertEqual(self.p.library[-1].name,"Ral's Reinforcements");self.t.assert_consistent()
 def test_reject_instant(self):
  c=self.give('Consider');oid=self.t.zones.move(c.object_id,'library')
  self.t.tutor_policy=lambda r:oid
  with self.assertRaises(ValueError):self.cast(NAME)
 def test_fail_to_find_still_shuffles(self):
  self.t.tutor_policy=lambda r:None;before=len(self.t.zones.operations);self.cast(NAME)
  self.assertTrue(any(x[0]=='shuffle' for x in self.t.zones.operations[before:]))
  self.assertIsNone(self.t.tutor_events[-1][2])
 def test_sorcery_timing(self):
  self.give(NAME);self.t.active_seat=1
  self.assertFalse(any(c.kind=='spell' and c.action.source==NAME for c in self.t.priority_choices(0)))
 def test_spell_cost_remains_u_with_medallion(self):
  self.cast('Sapphire Medallion');c=self.give(NAME);a=self.t.action_for_card(self.p,c)
  self.assertEqual((a.cost,a.parameters['U']),(1,1))
 def test_pyromancer_trigger(self):
  self.cast('Young Pyromancer');self.cast(NAME)
  self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),1)
 def test_tutor_to_ral(self):
  self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=="Ral's Reinforcements")
  self.cast(NAME);self.p.draw();self.cast("Ral's Reinforcements")
  self.assertEqual(sum(o.card.card_id=='ral_elemental_1_1' for o in self.t.rules.controlled(0)),2)
  self.t.assert_consistent()

if __name__=='__main__':unittest.main()
