import unittest
from mana_table import EarlyManaTable
from resources import Cost

class FrostboilTests(unittest.TestCase):
 def setUp(self):
  self.t=EarlyManaTable(seed=511);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.p=self.t.details
  for oid in self.t.zones.ids(0,'hand'):self.t.zones.move(oid,'library')
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def test_no_reveal_enters_tapped(self):
  oid=self.t.enter_land(self.p,self.give('Frostboil Snarl').object_id)
  self.assertTrue(self.t.rules.get(oid).tapped)
 def test_reveal_island_enters_untapped_and_produces_mana(self):
  self.give('Island');oid=self.t.enter_land(self.p,self.give('Frostboil Snarl').object_id)
  self.assertFalse(self.t.rules.get(oid).tapped)
  self.assertIsNotNone(self.t.resources.plan(0,Cost(blue=1)))
  self.assertIsNotNone(self.t.resources.plan(0,Cost(red=1)))
 def test_can_decline_reveal(self):
  self.give('Island');self.t.snarl_reveal_policy=lambda seat,options:None
  oid=self.t.enter_land(self.p,self.give('Frostboil Snarl').object_id)
  self.assertTrue(self.t.rules.get(oid).tapped)
 def test_reveal_nonbasic_island_mountain(self):
  self.give('Steam Vents');oid=self.t.enter_land(self.p,self.give('Frostboil Snarl').object_id)
  self.assertFalse(self.t.rules.get(oid).tapped)
 def test_reject_noneligible_card(self):
  bad=self.give('Ponder').object_id;self.t.snarl_reveal_policy=lambda seat,options:bad
  with self.assertRaises(ValueError):self.t.enter_land(self.p,self.give('Frostboil Snarl').object_id)
 def test_reveal_from_battlefield_not_allowed(self):
  island=self.t.enter_land(self.p,self.give('Island').object_id)
  oid=self.t.enter_land(self.p,self.give('Frostboil Snarl').object_id)
  self.assertTrue(self.t.rules.get(oid).tapped);self.assertIn(island,self.t.rules.objects)
 def test_forced_tapped(self):
  self.give('Mountain');oid=self.t.enter_land(self.p,self.give('Frostboil Snarl').object_id,force_tapped=True)
  self.assertTrue(self.t.rules.get(oid).tapped)
 def test_land_is_selectable_in_main_phase(self):
  oid=self.give('Frostboil Snarl').object_id
  self.assertTrue(any(c.kind=='land' and c.source_id==oid for c in self.t.priority_choices(0)))

 def test_magnus_tokens_reduce_buyback_generic_but_not_blue(self):
  self.t.rules.mana_pools[0]=(20,20,20)
  commander=self.t.zones.views(0,'command')[0]
  self.assertTrue(self.t.cast(self.t.action_for_card(self.p,commander)))
  for i in range(6):self.t.add_creature(self.p,1,1,'fixture',token=True)
  action=self.t.action_with_options(self.p,self.give('Capsize'),buyback=True)
  self.assertEqual((action.cost,action.parameters['U']),(2,2))
  self.t.assert_consistent()

 def test_creature_token_count_does_not_count_noncreature_treasures(self):
  self.t.rules.mana_pools[0]=(20,20,20)
  commander=self.t.zones.views(0,'command')[0]
  self.assertTrue(self.t.cast(self.t.action_for_card(self.p,commander)))
  self.t.world.create_treasure(self.p)
  self.t.add_creature(self.p,1,1,'fixture',token=True)
  action=self.t.action_with_options(self.p,self.give('Capsize'),buyback=True)
  self.assertEqual(action.cost,5)
  self.t.assert_consistent()

if __name__=='__main__':unittest.main()
