import unittest
from search_table import SearchTable,MERCHANT,SOLVE

class SearchTests(unittest.TestCase):
 def setUp(self):
  self.t=SearchTable(seed=2601);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def in_library(self,name):
  c=self.give(name);return self.t.zones.move(c.object_id,'library')
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def test_merchant_finds_blue_instant_to_hand(self):
  self.in_library('Consider');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Consider')
  self.cast(MERCHANT);self.assertIn('Consider',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_merchant_excludes_red_instant(self):
  bad=self.in_library('Searing Touch');self.t.tutor_policy=lambda r:bad
  with self.assertRaises(ValueError):self.cast(MERCHANT)
 def test_merchant_excludes_blue_sorcery(self):
  bad=self.in_library('Ponder');self.t.tutor_policy=lambda r:bad
  with self.assertRaises(ValueError):self.cast(MERCHANT)
 def test_solve_can_find_red_sorcery(self):
  self.in_library("Ral's Reinforcements");self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=="Ral's Reinforcements")
  self.cast(SOLVE);self.assertIn("Ral's Reinforcements",[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_solve_can_find_instant(self):
  self.in_library('Consider');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Consider')
  self.cast(SOLVE);self.assertIn('Consider',[c.name for c in self.p.hand])
 def test_fail_to_find_still_shuffles(self):
  self.t.tutor_policy=lambda r:None;before=len(self.t.zones.operations);self.cast(MERCHANT)
  self.assertTrue(any(x[0]=='shuffle' for x in self.t.zones.operations[before:]));self.assertIsNone(self.t.tutor_events[-1][2])
 def test_sorcery_timing(self):
  self.give(MERCHANT);self.give(SOLVE);self.t.active_seat=1
  self.assertFalse(any(c.kind=='spell' and c.action.source in (MERCHANT,SOLVE) for c in self.t.priority_choices(0)))
 def test_sapphire_reduces_both(self):
  self.cast('Sapphire Medallion')
  self.assertEqual(self.t.action_for_card(self.p,self.give(MERCHANT)).cost,1)
  self.assertEqual(self.t.action_for_card(self.p,self.give(SOLVE)).cost,2)
 def test_pyromancer_trigger_and_search(self):
  self.cast('Young Pyromancer');self.in_library('Consider');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Consider')
  self.cast(MERCHANT);self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),1)
  self.assertIn('Consider',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_unknown_instant_color_fails_closed(self):
  c=self.in_library('Consider');obj=self.t.rules.get(c)
  from dataclasses import replace
  obj.card=replace(obj.card,name='Unknown Instant')
  with self.assertRaises(NotImplementedError):self.cast(MERCHANT)

 def test_magnus_and_medallion_preserve_blue_mana_floor(self):
  self.cast('Sapphire Medallion')
  commander=self.t.zones.views(0,'command')[0]
  self.assertTrue(self.t.cast(self.t.action_for_card(self.p,commander)))
  self.t.add_creature(self.p,1,1,'fixture',token=True)
  a=self.t.action_for_card(self.p,self.give(SOLVE))
  self.assertEqual((a.cost,a.parameters['U']),(1,1))
 def test_merchant_chooses_at_resolution_after_response(self):
  self.in_library('Consider');used=[];observed=[];self.give('Brainstorm')
  def policy(seat,frames,choices):
   c=next((c for c in choices if seat==0 and frames and c.kind=='spell' and c.action.source=='Brainstorm'),None)
   if c and not used:used.append(True);return c
   return None
  self.t.priority_policy=policy
  self.t.tutor_policy=lambda r:(observed.append(r.kind) or None)
  self.cast(MERCHANT)
  self.assertTrue(used);self.assertEqual(observed,['merchant_scroll'])
  resolved=[x[2] for x in self.t.spell_stack.history if x[0]=='resolve']
  self.assertEqual(resolved[-2:],['spell','spell']);self.t.assert_consistent()

if __name__=='__main__':unittest.main()
