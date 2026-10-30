import unittest
from dataclasses import replace
from altar_table import AltarTable,AltarAbility,NAME
from resources import Activation,U,R,Cost

class AltarTests(unittest.TestCase):
 def setUp(self):
  self.t=AltarTable(seed=3001);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.p=self.t.details;self.t.rules.mana_pools[0]=(3,0,0)
  card=next(c for c in self.p.hand+self.p.library if c.name==NAME)
  if card not in self.p.hand:
   oid=self.t.zones.move(card.object_id,'hand');card=next(c for c in self.p.hand if c.object_id==oid)
  self.assertTrue(self.t.cast(self.t.action_for_card(self.p,card)))
  self.altar=next(o.object_id for o in self.t.rules.controlled(0) if o.card.name==NAME)
 def creature(self,seat=0):return self.t.add_creature(self.t.players[seat],1,1,'fixture',token=True).id
 def test_cast_altar(self):self.assertIn(self.altar,self.t.rules.objects);self.assertEqual(self.t.resources.pool(0),(0,0,0))
 def test_sacrifice_produces_colored_not_colorless(self):
  victim=self.creature();abilities=dict(self.t.resources.sources(0))[victim]
  self.assertEqual({a.output for a in abilities if isinstance(a,AltarAbility)},{U,R})
  activation=Activation(victim,next(a for a in abilities if a.output==U),(0,0,0))
  self.t.resources.activate(0,activation);self.assertEqual(self.t.resources.pool(0),U);self.assertNotIn(victim,self.t.rules.objects)
  self.assertFalse(self.t.rules.get(self.altar).tapped);self.t.assert_consistent()
 def test_two_sacrifices_same_altar_for_colored_cost(self):
  a=self.creature();b=self.creature();plan=self.t.resources.pay(0,Cost(blue=1,red=1))
  self.assertEqual({x.source_id for x in plan.activations},{a,b});self.assertIn(self.altar,self.t.rules.objects)
  self.assertFalse(self.t.rules.get(self.altar).tapped);self.t.assert_consistent()
 def test_tapped_creature_and_tapped_altar_can_be_used(self):
  victim=self.creature();self.t.rules.get(victim).tapped=True;self.t.rules.get(self.altar).tapped=True;self.t.rules._dirty()
  self.assertIsNotNone(self.t.resources.plan(0,Cost(red=1)));self.t.resources.pay(0,Cost(red=1))
  self.assertNotIn(victim,self.t.rules.objects)
 def test_cannot_sacrifice_opponent_creature(self):
  victim=self.creature(1)
  with self.assertRaises(ValueError):self.t.resources.activate(0,Activation(victim,AltarAbility(U,sacrifice=True,altar_id=self.altar),(0,0,0)))
 def test_stale_plan_is_rejected_without_cost(self):
  victim=self.creature();plan=self.t.resources.plan(0,Cost(blue=1));self.t.world.move(self.altar,'graveyard','destroy')
  with self.assertRaises(ValueError):self.t.resources.pay(0,Cost(blue=1),plan)
  self.assertIn(victim,self.t.rules.objects)
 def test_sacrificed_physical_creature_goes_to_graveyard(self):
  self.t.rules.mana_pools[0]=(2,0,1);c=next(c for c in self.p.hand+self.p.library if c.name=='Young Pyromancer')
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  self.t.cast(self.t.action_for_card(self.p,c));obj=next(o for o in self.t.rules.controlled(0) if o.card.name=='Young Pyromancer')
  self.t.resources.pay(0,Cost(blue=1));self.assertTrue(any(self.t.rules.get(oid).card.name=='Young Pyromancer' for oid in self.t.zones.ids(0,'graveyard')))
 def test_no_stack_frame_created(self):
  victim=self.creature();self.t.spell_stack.holder=0
  choice=next(c for c in self.t.priority_choices(0) if c.kind=='mana' and c.activation.source_id==victim and c.activation.ability.output==R)
  self.t.commit_choice(0,choice);self.assertEqual(self.t.spell_stack.frames,[]);self.assertEqual(self.t.resources.pool(0),R)
 def test_avoid_sacrifice_when_land_pays(self):
  victim=self.creature();self.t.rules.mana_pools[0]=(0,1,0)
  self.t.resources.pay(0,Cost(blue=1));self.assertIn(victim,self.t.rules.objects)
 def test_cannot_forge_life_or_cost(self):
  victim=self.creature();bad=AltarAbility(U,Cost(0),life=1,sacrifice=True,altar_id=self.altar)
  with self.assertRaises(ValueError):self.t.resources.activate(0,Activation(victim,bad,(0,0,0)))
if __name__=='__main__':unittest.main()
