import unittest,json,sys
from pathlib import Path
from functools import partial
from collections import Counter
from dataclasses import replace
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from commander_sim.decks import DeckProvider
from scenarios import scenario
from baseline import CopyTable,check
from premium_table import PremiumPlayer
from budget_table import card_spec
from commander_sim.queries import Query, Match, ObjectView, target_legality
from commander_sim.snapshots import validate_snapshot
from commander_sim.identities import CardRegistry
from wizard_tutor_table import WIZARDCYCLING
from reference_state import reference_payload,canonical
from altar_table import AltarTable,AltarAbility
from resources import Cost,U,R

class ProviderCompositionTests(unittest.TestCase):
 def enter(self,t,name,choices=None):
  p=t.details;c=next(c for c in p.hand+p.library if c.name==name)
  return t.enter_land(p,c.object_id,choices=choices) if choices else t.enter_land(p,c.object_id)
 def test_budget_frostboil_and_altar_coexist(self):
  t=AltarTable(seed=9001);p=t.details;t.rules.mana_pools[p.seat]=(0,0,0)
  oid=self.enter(t,'Frostboil Snarl',(False,0,None))
  self.assertEqual({a.output for a in t.resources.abilities(t.rules.get(oid))},{U,R})
  self.assertIsNotNone(t.resources.plan(p.seat,Cost(blue=1)));self.assertIsNotNone(t.resources.plan(p.seat,Cost(red=1)))
  c=next(c for c in p.hand+p.library if c.name=='Phyrexian Altar')
  if c not in p.hand:
   cid=t.zones.move(c.object_id,'hand');c=next(c for c in p.hand if c.object_id==cid)
  t.active_seat=p.seat;t.phase='main';t.priority_policy=lambda *a:None;t.rules.mana_pools[p.seat]=(3,0,0)
  self.assertTrue(t.cast(t.action_for_card(p,c)))
  victim=t.add_creature(p,1,1,'fixture',token=True).id
  self.assertTrue(any(isinstance(a,AltarAbility) for a in dict(t.resources.sources(p.seat))[victim]))
  self.assertEqual({a.output for a in t.resources.abilities(t.rules.get(oid))},{U,R});t.assert_consistent()
 def test_premium_lindblum_and_standard_lands(self):
  t=CopyTable(seed=9002);p=t.details;t.rules.mana_pools[p.seat]=(0,0,0)
  lind=self.enter(t,'Lindblum, Industrial Regency');island=self.enter(t,'Island')
  self.assertTrue(t.rules.get(lind).tapped);self.assertEqual({a.output for a in t.resources.abilities(t.rules.get(lind))},{R})
  self.assertEqual({a.output for a in t.resources.abilities(t.rules.get(island))},{U})
  t.rules.get(lind).tapped=False;t.rules._dirty()
  self.assertIsNotNone(t.resources.plan(p.seat,Cost(blue=1,red=1)))
  c=next(c for c in p.hand+p.library if c.name=='Phyrexian Altar')
  if c not in p.hand:
   cid=t.zones.move(c.object_id,'hand');c=next(c for c in p.hand if c.object_id==cid)
  t.active_seat=p.seat;t.phase='main';t.priority_policy=lambda *a:None;t.rules.mana_pools[p.seat]=(3,0,0)
  self.assertTrue(t.cast(t.action_for_card(p,c)))
  victim=t.add_creature(p,1,1,'fixture',token=True).id
  self.assertTrue(any(isinstance(a,AltarAbility) for a in dict(t.resources.sources(p.seat))[victim]))
  self.assertEqual({a.output for a in t.resources.abilities(t.rules.get(lind))},{R});t.assert_consistent()
 def test_explicit_interaction_replays(self):
  data=json.loads(Path(__file__).with_name("SCENARIOS.json").read_text())
  for name,expected in data["scenarios"].items():
   with self.subTest(name=name):self.assertEqual(scenario(name),expected)
 def test_frozen_current_replays(self):self.assertEqual(check(),4)
 def test_injected_premium_matches_historical_engine(self):
  deck=DeckProvider.bundled().preset('premium')
  for seed in (0,29):
   with self.subTest(seed=seed):
    a=CopyTable(seed=seed).run(4)
    b=CopyTable(seed=seed,detailed_factory=partial(PremiumPlayer,deck=deck)).run(4)
    self.assertEqual(canonical(reference_payload(a)),canonical(reference_payload(b)))
    self.assertEqual(a.rule_events,b.rule_events);a.assert_consistent();b.assert_consistent()
 def test_budget_uses_current_engine_and_preserves_inventory(self):
  deck=DeckProvider.bundled().preset('budget')
  t=CopyTable(seed=3,detailed_factory=partial(PremiumPlayer,deck=deck));p=t.details
  actual=Counter(t.rules.get(oid).card.name for zone in ('library','hand','command') for oid in t.zones.ids(p.seat,zone))
  expected=Counter({name:qty for _,name,qty in deck.cards})
  self.assertEqual(actual,expected);self.assertEqual(sum(actual.values()),100)
  frost=self.enter(t,'Frostboil Snarl',(False,0,None))
  self.assertEqual({a.output for a in t.resources.abilities(t.rules.get(frost))},{U,R})
  t.run(2);t.assert_consistent();self.assertIsNone(t.safety_stop)
 def test_sparse_deck_installs_absent_card_definitions(self):
  deck=DeckProvider.bundled().parse('Commander\n1 Magnus the Red\nLibrary\n99 Island\n')
  t=CopyTable(seed=7,detailed_factory=partial(PremiumPlayer,deck=deck)).run(1)
  self.assertIsNone(t.safety_stop);t.assert_consistent()
 def test_unimplemented_artifact_is_found_by_real_tutor(self):
  t=CopyTable(seed=117);p=t.details
  spec=card_spec('Swiftfoot Boots')
  oid=t.zones.add_spec(spec,p.seat,'library',detailed=True)
  obj=t.rules.get(oid);obj.card=replace(obj.card,types=frozenset({'artifact'}),coverage='unimplemented')
  self.assertIs(Query(types_all=frozenset({'artifact'})).matches_kernel(t.rules,oid),Match.YES)
  self.assertIs(target_legality(ObjectView.from_kernel(t.rules,oid),source_controller=1),Match.UNKNOWN)
  t.tutor_policy=lambda request:next(c.object_id for c in request.cards if c.name=='Swiftfoot Boots')
  action=type('SearchAction',(),{'actor':p.seat})()
  t.resolve_fabricate(t,action)
  self.assertIn('Swiftfoot Boots',[c.name for c in p.hand]);t.assert_consistent()
 def test_verified_unimplemented_wizard_is_found_by_real_tutor(self):
  root=Path(__file__).resolve().parents[2]
  snapshot=validate_snapshot(root/'decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt',root/'simulator/card_data/flameslinger_v0_7_scryfall.json')
  face=CardRegistry(snapshot).get('Stormsplitter').primary_face()
  t=CopyTable(seed=118);p=t.details
  oid=t.zones.add_spec(card_spec(face.name),p.seat,'library',detailed=True)
  obj=t.rules.get(oid)
  obj.card=replace(obj.card,types=face.types,subtypes=face.subtypes,colors=face.colors,
                   base_power=face.power,base_toughness=face.toughness,coverage='unimplemented')
  query=Query(types_all=frozenset({'creature'}),subtypes_all=frozenset({'Wizard'}),max_power=2)
  self.assertIs(query.matches_kernel(t.rules,oid,power_verified=True),Match.YES)
  self.assertIs(target_legality(ObjectView.from_kernel(t.rules,oid,power_verified=True),source_controller=1),Match.UNKNOWN)
  t.tutor_policy=lambda request:next(c.object_id for c in request.cards if c.name=='Stormsplitter')
  self.assertTrue(t.resolve_activation(SimpleNamespace(ability=WIZARDCYCLING,controller=p.seat,source_id=0)))
  self.assertIn('Stormsplitter',[c.name for c in p.hand]);t.assert_consistent()

if __name__=='__main__':unittest.main()
