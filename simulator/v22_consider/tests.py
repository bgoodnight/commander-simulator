import unittest
from consider_table import ConsiderTable

class ConsiderTests(unittest.TestCase):
 def setUp(self):
  self.t=ConsiderTable(seed=2201);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(10,10,10);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def top(self,name):
  c=self.give(name);self.t.zones.move(c.object_id,'library')
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def test_keep_top_then_draw(self):
  self.give('Consider');self.top('Ponder');self.cast('Consider')
  self.assertIn('Ponder',[c.name for c in self.p.hand]);self.assertFalse(self.t.consider_events[-1][2]);self.t.assert_consistent()
 def test_mill_top_then_draw_next(self):
  self.give('Consider');self.top('Preordain');self.top('Ponder');self.t.consider_policy=lambda seat,top:True
  self.cast('Consider');self.assertIn('Ponder',self.p.graveyard)
  self.assertIn('Preordain',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_invalid_policy_rejected(self):
  self.t.consider_policy=lambda seat,top:'yes'
  with self.assertRaises(ValueError):self.cast('Consider')
 def test_exact_blue_cost(self):
  card=self.give('Consider');a=self.t.action_for_card(self.p,card)
  self.assertEqual(a.cost,1);self.assertEqual(a.parameters['U'],1)
 def test_pyromancer_cast_trigger(self):
  self.cast('Young Pyromancer');self.cast('Consider')
  self.assertEqual(sum(o.card.name=='Elemental' for o in self.t.rules.controlled(0)),1)
 def test_tutor_finds_consider_then_consider_casts(self):
  self.t.tutor_policy=lambda req:next(x.object_id for x in req.cards if x.name=='Consider')
  self.cast('Mystical Tutor');self.assertEqual(self.p.library[-1].name,'Consider')
  self.p.draw();self.cast('Consider');self.t.assert_consistent()

 def test_empty_library_draw_eliminates_player(self):
  card=self.give('Consider')
  for oid in self.t.zones.ids(0,'library'):self.t.zones.move(oid,'exile')
  self.assertTrue(self.t.cast(self.t.action_for_card(self.p,card)))
  self.assertIsNotNone(self.p.eliminated_round)

 def test_surveil_graveyard_card_can_be_recovered_by_sanctuary(self):
  self.give('Consider');self.top('Ponder');self.t.consider_policy=lambda seat,oid:True
  self.cast('Consider');self.assertIn('Ponder',self.p.graveyard)
  for _ in range(3):
   card=self.give('Island');self.t.enter_land(self.p,card.object_id,cause='fixture')
  self.t.sanctuary_target_policy=lambda req:next(oid for oid in req.eligible if self.t.rules.get(oid).card.name=='Ponder')
  sanctuary=self.give('Mystic Sanctuary');self.t.enter_land(self.p,sanctuary.object_id,cause='fixture')
  self.t.spell_stack.resolve();self.assertEqual(self.p.library[-1].name,'Ponder')
  self.t.assert_consistent()

if __name__=='__main__':unittest.main()
