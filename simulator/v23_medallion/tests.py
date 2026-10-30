import unittest
from medallion_table import MedallionTable,COLORS

class MedallionTests(unittest.TestCase):
 def setUp(self):
  self.t=MedallionTable(seed=2301);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def medallion(self):
  self.cast('Sapphire Medallion')
  return next(o for o in self.t.rules.controlled(0) if o.card.name=='Sapphire Medallion')
 def test_mana_value_and_adoption(self):
  c=self.give('Sapphire Medallion');self.assertEqual(self.t.action_for_card(self.p,c).cost,2)
  self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
  o=next(o for o in self.t.rules.controlled(0) if o.card.name=='Sapphire Medallion')
  self.assertEqual(o.types,frozenset({'artifact'}));self.t.assert_consistent()
 def test_color_is_not_color_identity(self):
  self.assertEqual(COLORS['Sapphire Medallion'],[])
  self.assertEqual(set(COLORS['Goblin Electromancer']),{'U','R'})
 def test_blue_creature_reduced(self):
  c=self.give('Archmage Emeritus');before=self.t.action_for_card(self.p,c).cost
  self.medallion();self.assertEqual(self.t.action_for_card(self.p,c).cost,before-1)
 def test_multicolor_is_blue(self):
  c=self.give('Goblin Electromancer');self.medallion()
  self.assertEqual(self.t.action_for_card(self.p,c).cost,2)
 def test_red_creature_not_reduced(self):
  c=self.give('Young Pyromancer');before=self.t.action_for_card(self.p,c).cost
  self.medallion();self.assertEqual(self.t.action_for_card(self.p,c).cost,before)
 def test_blue_mana_floor(self):
  c=self.give('Consider');self.medallion();a=self.t.action_for_card(self.p,c)
  self.assertEqual((a.cost,a.parameters['U']),(1,1))
 def test_buyback_reduction_and_stack_payment(self):
  self.medallion();self.t.add_creature(self.t.players[1],2,2,'target',token=True)
  c=self.give('Capsize');a=self.t.action_with_options(self.p,c,buyback=True)
  self.assertEqual(a.cost,5);self.assertTrue(self.t.cast(a));self.assertIn('Capsize',[x.name for x in self.p.hand]);self.t.assert_consistent()
 def test_removal_ends_reduction(self):
  c=self.give('Archmage Emeritus');before=self.t.action_for_card(self.p,c).cost
  obj=self.medallion();self.assertEqual(self.t.action_for_card(self.p,c).cost,before-1)
  self.t.world.move(obj.object_id,'graveyard','destroy')
  self.assertEqual(self.t.action_for_card(self.p,c).cost,before)
 def test_opponent_medallion_does_not_reduce(self):
  c=self.give('Archmage Emeritus');before=self.t.action_for_card(self.p,c).cost
  obj=self.medallion();obj.controller=1;self.t.rules._dirty()
  self.assertEqual(self.t.action_for_card(self.p,c).cost,before)

 def test_buyback_choice_generated_when_discount_makes_it_payable(self):
  self.medallion();self.t.rules.mana_pools[0]=(3,2,0)
  self.t.add_creature(self.t.players[1],2,2,'target',token=True)
  self.give('Capsize')
  choices=self.t.priority_choices(0)
  self.assertTrue(any(c.kind=='spell' and c.action.source=='Capsize' and c.action.tags==('buyback',) and c.action.cost==5 for c in choices))
 def test_blue_spell_does_not_lose_colored_pips(self):
  c=self.give('Counterspell');self.medallion();a=self.t.action_for_card(self.p,c)
  self.assertEqual((a.cost,a.parameters['U']),(2,2))
 def test_stale_discount_rejected_after_medallion_leaves(self):
  obj=self.medallion();card=self.give('Archmage Emeritus');a=self.t.action_for_card(self.p,card)
  self.t.world.move(obj.object_id,'graveyard','destroy')
  with self.assertRaises(ValueError):self.t.cast(a)

 def test_magnus_and_medallion_stack_against_buyback(self):
  self.medallion()
  commander=self.t.zones.views(0,'command')[0]
  self.assertTrue(self.t.cast(self.t.action_for_card(self.p,commander)))
  self.t.add_creature(self.p,1,1,'fixture',token=True)
  self.t.add_creature(self.t.players[1],2,2,'target',token=True)
  action=self.t.action_with_options(self.p,self.give('Capsize'),buyback=True)
  self.assertEqual((action.cost,action.parameters['U']),(4,2))
  self.assertTrue(self.t.cast(action));self.t.assert_consistent()

if __name__=='__main__':unittest.main()
