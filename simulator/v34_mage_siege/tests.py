import unittest
from adventure_table import AdventureTable,LAND,SPELL

class AdventureTests(unittest.TestCase):
 def setUp(self):
  self.t=AdventureTable(seed=3401);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def adventure(self):
  c=self.give(LAND);self.t.spell_stack.holder=0;self.assertTrue(self.t.cast_adventure(0,c.object_id))
 def test_adventure_creates_wizard_and_exiles_land(self):
  self.adventure();w=next(o for o in self.t.rules.controlled(0) if o.card.card_id=='mage_siege_wizard')
  self.assertEqual((w.power,w.toughness,w.card.colors),(0,1,frozenset({'B'})));self.assertIn('Wizard',w.subtypes)
  self.assertEqual(self.t.zones.names(0,'exile').count(LAND),1);self.t.assert_consistent()
 def test_land_played_from_adventure_exile_enters_tapped(self):
  self.adventure();oid=next(iter(self.t.adventure_exiled));self.t.play_adventure_land(0,oid)
  land=next(o for o in self.t.rules.controlled(0) if o.card.name==LAND)
  self.assertTrue(land.tapped);self.assertNotIn(oid,self.t.adventure_exiled);self.t.assert_consistent()
 def test_unrelated_exile_not_playable(self):
  oid=self.t.zones.move(self.give(LAND).object_id,'exile')
  with self.assertRaises(ValueError):self.t.play_adventure_land(0,oid)
 def test_respects_one_land_per_turn(self):
  self.adventure();oid=next(iter(self.t.adventure_exiled));self.t.play_land(self.p,self.give('Island'),1)
  with self.assertRaises(ValueError):self.t.play_adventure_land(0,oid)
 def test_later_noncreature_cast_damages_each_opponent(self):
  self.adventure();self.cast('Consider');self.assertEqual([p.life for p in self.t.players],[40,39,39,39])
 def test_creature_cast_does_not_trigger_wizard(self):
  self.adventure();self.cast('Young Pyromancer');self.assertEqual([p.life for p in self.t.players],[40,40,40,40])
 def test_reiterate_copies_adventure_creating_two_wizards(self):
  self.give('Reiterate');used=[]
  def policy(seat,frames,choices):
   if seat==0 and not used:
    c=next((c for c in choices if c.kind=='spell' and c.action.source=='Reiterate' and not c.action.parameters['buyback']),None)
    if c:used.append(True);return c
   return None
  self.t.priority_policy=policy;self.adventure()
  self.assertTrue(used);self.assertEqual(sum(o.card.card_id=='mage_siege_wizard' for o in self.t.rules.controlled(0)),2)
  self.assertEqual(self.t.zones.names(0,'exile').count(LAND),1);self.t.assert_consistent()
 def test_harmonic_doubles_wizard_trigger(self):
  self.cast('Harmonic Prodigy');self.adventure();self.cast('Consider')
  self.assertEqual([p.life for p in self.t.players],[40,38,38,38])
 def test_countered_adventure_goes_to_graveyard(self):
  c=self.give(LAND);used=[]
  def policy(seat,frames,choices):
   if frames and frames[-1].label==SPELL and not used:
    used.append(True);self.t.spell_stack.counter(frames[-1].frame_id,{'spell'})
   return None
  self.t.priority_policy=policy;self.t.spell_stack.holder=0;self.t.cast_adventure(0,c.object_id)
  self.assertTrue(used);self.assertIn(LAND,self.t.zones.names(0,'graveyard'));self.assertFalse(self.t.adventure_exiled)
  self.assertFalse(any(o.card.card_id=='mage_siege_wizard' for o in self.t.rules.controlled(0)));self.t.assert_consistent()
 def test_default_pilot_can_select_adventure_and_land(self):
  from priority import Choice
  c=self.give(LAND);self.t.spell_stack.holder=0
  selected=self.t.choose_priority(0,(Choice('adventure',source_id=c.object_id),))
  self.assertEqual(selected.kind,'adventure');self.adventure()
  oid=next(iter(self.t.adventure_exiled));selected=self.t.choose_priority(0,(Choice('adventure_land',source_id=oid),))
  self.assertEqual(selected.kind,'adventure_land')
 def test_adventure_cast_triggers_pyromancer(self):
  self.cast('Young Pyromancer');self.adventure()
  self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),1)
 def test_magnus_reduces_adventure_cost(self):
  commander=self.t.zones.views(0,'command')[0];self.t.cast(self.t.action_for_card(self.p,commander))
  self.t.add_creature(self.p,1,1,'fixture',token=True);self.t.add_creature(self.p,1,1,'fixture',token=True)
  cost=self.t.adventure_cost(0);self.assertEqual((cost.total,cost.red),(1,1))
 def test_wizard_trigger_resolves_even_when_spell_is_countered(self):
  self.adventure();used=[]
  def policy(seat,frames,choices):
   if not used and any(f.kind=='triggered' and f.trigger.op=='mage_siege_damage' for f in frames):
    original=next(f for f in frames if f.kind=='spell' and f.label=='Consider')
    used.append(True);self.t.spell_stack.counter(original.frame_id,{'spell'})
   return None
  self.t.priority_policy=policy;self.cast('Consider')
  self.assertTrue(used);self.assertEqual([p.life for p in self.t.players],[40,39,39,39]);self.assertEqual(len(self.t.consider_events),0)
 def test_trigger_survives_token_leaving(self):
  self.adventure();w=next(o for o in self.t.rules.controlled(0) if o.card.card_id=='mage_siege_wizard');used=[]
  def policy(seat,frames,choices):
   if any(f.kind=='triggered' and f.source_id==w.object_id for f in frames) and not used:
    used.append(True);self.t.world.move(w.object_id,'graveyard','sacrifice')
   return None
  self.t.priority_policy=policy;self.cast('Consider')
  self.assertTrue(used);self.assertEqual([p.life for p in self.t.players],[40,39,39,39])
if __name__=='__main__':unittest.main()
