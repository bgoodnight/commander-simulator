import unittest
from reinforcements_table import ReinforcementTable,NAME

class ReinforcementTests(unittest.TestCase):
 def setUp(self):
  self.t=ReinforcementTable(seed=2401);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def ral_tokens(self):return [o for o in self.t.rules.controlled(0) if o.card.card_id=='ral_elemental_1_1']
 def test_two_blue_red_elementals(self):
  self.cast(NAME);tokens=self.ral_tokens();self.assertEqual(len(tokens),2)
  self.assertTrue(all(o.token and o.card.colors=={'U','R'} and o.subtypes=={'Elemental'} and o.power==1 and o.toughness==1 for o in tokens))
  self.t.assert_consistent()
 def test_cost_is_one_red(self):
  a=self.t.action_for_card(self.p,self.give(NAME));self.assertEqual((a.cost,a.parameters['R']),(2,1))
 def test_sapphire_does_not_discount_red_spell(self):
  self.cast('Sapphire Medallion');self.assertEqual(self.t.action_for_card(self.p,self.give(NAME)).cost,2)
 def test_pyromancer_adds_third_distinct_token(self):
  self.cast('Young Pyromancer');self.cast(NAME)
  self.assertEqual(len(self.ral_tokens()),2)
  self.assertEqual(sum(o.token and o.card.name=='Elemental' for o in self.t.rules.controlled(0)),3)
  self.t.assert_consistent()
 def test_magnus_reduces_subsequent_spell_cost(self):
  commander=self.t.zones.views(0,'command')[0];self.assertTrue(self.t.cast(self.t.action_for_card(self.p,commander)))
  self.cast(NAME);a=self.t.action_with_options(self.p,self.give('Capsize'),buyback=True)
  self.assertEqual((a.cost,a.parameters['U']),(4,2))
 def test_token_colors_present_during_entry_event(self):
  seen=[]
  def observer(table,event,action,payload):
   if event=='creature_entered' and payload.get('source')=='Elemental':seen.append(table.rules.get(payload['creature_id']).card.colors)
  self.t.on_event(observer);self.cast(NAME);self.assertEqual(seen,[frozenset({'U','R'})]*2)
 def test_sorcery_not_available_during_opponent_turn(self):
  self.give(NAME);self.t.active_seat=1
  self.assertFalse(any(c.kind=='spell' and c.action.source==NAME for c in self.t.priority_choices(0)))
 def test_unknown_legacy_token_color_is_not_assumed(self):
  self.cast('Young Pyromancer');self.cast('Consider')
  pyro=next(o for o in self.t.rules.controlled(0) if o.token and o.card.name=='Elemental')
  self.assertIsNone(pyro.card.colors)

 def test_reference_canonicalizer_preserves_unknown_legacy_colors(self):
  import importlib.util
  from pathlib import Path
  from rules import CardDefinition
  path=Path(__file__).resolve().parents[1]/'v14_lands'/'reference_state.py'
  spec=importlib.util.spec_from_file_location('legacy_reference',path)
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  old=CardDefinition('old','Old',frozenset({'creature'}))
  known=CardDefinition('known','Known',frozenset({'creature'}),colors=frozenset({'U','R'}))
  self.assertNotIn('colors',module.canonical(old))
  self.assertEqual(module.canonical(known)['colors'],['R','U'])

if __name__=='__main__':unittest.main()
