import unittest
from rift_table import RiftTable,RIFT

class RiftTests(unittest.TestCase):
 def setUp(self):
  self.t=RiftTable(seed=3201);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def creature(self,seat=1,keywords=()):return self.t.add_creature(self.t.players[seat],2,2,'fixture',token=True,keywords=keywords).id
 def cast(self,target=None,overload=False):return self.t.cast(self.t.rift_action(self.p,self.give(RIFT),overload=overload,target=target))
 def test_target_bounces_opponent(self):
  target=self.creature();self.assertTrue(self.cast(target));self.assertNotIn(target,self.t.rules.objects);self.t.assert_consistent()
 def test_target_rejects_own_creature(self):
  with self.assertRaises(ValueError):self.cast(self.creature(0))
 def test_hexproof_and_shroud_prevent_targeting(self):
  for keyword in ('hexproof','shroud'):
   with self.assertRaises(ValueError):self.cast(self.creature(keywords=(keyword,)))
 def test_overload_removes_all_opponents_even_hexproof_and_shroud(self):
  ids=[self.creature(1,('hexproof',)),self.creature(2,('shroud',)),self.creature(3)];own=self.creature(0)
  self.cast(overload=True);self.assertTrue(all(x not in self.t.rules.objects for x in ids));self.assertIn(own,self.t.rules.objects);self.t.assert_consistent()
 def test_overload_does_not_return_lands(self):
  land_card=next(oid for zone in ('hand','library') for oid in self.t.zones.ids(1,zone) if 'land' in self.t.rules.get(oid).types)
  land=self.t.enter_land(self.t.players[1],land_card)
  self.cast(overload=True);self.assertIn(land,self.t.rules.objects)
 def test_overload_no_target_even_empty_board(self):
  a=self.t.rift_action(self.p,self.give(RIFT),overload=True);self.assertIsNone(a.target_object);self.assertTrue(self.t.cast(a))
 def test_costs_and_sapphire_discount(self):
  a=self.t.rift_action(self.p,self.give(RIFT));b=self.t.rift_action(self.p,self.give(RIFT),overload=True)
  self.assertEqual((a.cost,b.cost),(2,7));self.t.cast(self.t.action_for_card(self.p,self.give('Sapphire Medallion')))
  self.assertEqual((self.t.rift_action(self.p,self.give(RIFT)).cost,self.t.rift_action(self.p,self.give(RIFT),overload=True).cost),(1,6))
 def test_own_spell_cost_reduction_applies_to_overload(self):
  c=self.t.zones.views(0,'command')[0];self.t.cast(self.t.action_for_card(self.p,c))
  self.creature(0);self.creature(0)
  self.assertEqual(self.t.rift_action(self.p,self.give(RIFT),overload=True).cost,5)
 def test_target_leaving_fizzles(self):
  oid=self.creature();used=[]
  def policy(seat,frames,choices):
   if frames and frames[-1].label==RIFT and not used:used.append(True);self.t.world.move(oid,'graveyard','destroy')
   return None
  self.t.priority_policy=policy;self.cast(oid);self.assertTrue(used);self.assertEqual(self.t.counts['spells_fizzled'],1)
 def test_pilot_choices_offer_instant_modes_with_opponent_turn(self):
  self.give(RIFT);oid=self.creature();self.t.active_seat=1;choices=self.t.priority_choices(0)
  self.assertTrue(any(c.kind=='spell' and c.action.source==RIFT and c.action.target_object==oid for c in choices))
  self.assertTrue(any(c.kind=='spell' and c.action.source==RIFT and c.action.parameters.get('overload') for c in choices))
 def test_cast_triggers_young_pyromancer_once(self):
  self.t.cast(self.t.action_for_card(self.p,self.give('Young Pyromancer')));self.cast(overload=True)
  self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),1)
if __name__=='__main__':unittest.main()
