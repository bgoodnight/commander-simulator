import unittest
import json,subprocess,sys
from collections import Counter
from pathlib import Path
from premium_table import PremiumTable,load_premium,load_budget
from altar_table import AltarTable
from channel_table import OTAWARA
from resources import Cost

class PremiumTests(unittest.TestCase):
 def setUp(self):
  self.t=PremiumTable(seed=3101);self.t.active_seat=0;self.t.phase='main';self.t.priority_policy=lambda *a:None
  self.t.rules.mana_pools[0]=(30,30,30);self.p=self.t.details
 def give(self,name):
  c=next(c for c in self.p.hand+self.p.library if c.name==name)
  if c not in self.p.hand:
   oid=self.t.zones.move(c.object_id,'hand');c=next(c for c in self.p.hand if c.object_id==oid)
  return c
 def library(self,name):return self.t.zones.move(self.give(name).object_id,'library')
 def cast(self,name):
  c=self.give(name);self.assertTrue(self.t.cast(self.t.action_for_card(self.p,c)))
 def test_deck_exact_100(self):
  d=load_premium();self.assertEqual(sum(d.values()),100);self.assertEqual(d['Commander','Magnus the Red'],1);self.assertEqual(len(d),82)
 def test_physical_objects_match_file(self):
  actual=Counter((('Commander' if obj.zone=='command' else 'Library'),obj.card.name) for obj in self.t.rules.objects.values() if obj.owner==self.t.detailed_seat and not obj.token)
  self.assertEqual(actual,load_premium())
 def test_added_card_identity_and_color_checks(self):
  rows=json.loads((Path(__file__).with_name('NEW_CARD_IDENTITIES.json')).read_text())['cards']
  self.assertEqual({r.get('deck_name',r['name']) for r in rows},{'Cyclonic Rift','Reiterate','Training Center','Otawara, Soaring City','Lindblum, Industrial Regency'})
  self.assertTrue(all(r['commander_legality']=='legal' and set(r['color_identity'])<=set('UR') for r in rows))
 def test_cli_defaults_to_premium_and_budget_is_selectable(self):
  root=Path(__file__).resolve().parents[2]
  for args,name in (([], 'premium'),(['--deck','budget'], 'budget')):
   run=subprocess.run([sys.executable,str(root/'run_simulation.py'),'--rounds','1',*args],capture_output=True,text=True,check=True)
   self.assertEqual(json.loads(run.stdout)['deck'],name)
 def test_exact_four_premium_swaps(self):
  old=load_budget();new=load_premium()
  plus=new-old;minus=old-new
  self.assertEqual({k[1]:v for k,v in plus.items()},{'Cyclonic Rift':1,'Reiterate':1,'Lindblum, Industrial Regency':1})
  self.assertEqual({k[1]:v for k,v in minus.items()},{'Snap':1,'Increasing Vengeance':1,'Frostboil Snarl':1})
 def test_budget_engine_still_loads_budget(self):
  t=AltarTable(seed=3101);names=[o.card.name for o in t.rules.objects.values() if o.owner==t.detailed_seat and not o.token]
  self.assertIn('Snap',names);self.assertNotIn('Cyclonic Rift',names)
 def test_every_seat_loads_expected_deck(self):
  for seat in range(4):
   kinds=['aggro','control','combo'];kinds.insert(seat,'magnus');t=PremiumTable(kinds,seed=3102)
   self.assertEqual(t.detailed_seat,seat);self.assertTrue(t.tutor_library_known(seat));t.assert_consistent()
 def test_both_new_spells_are_instant_and_unsupported(self):
  for name in ('Cyclonic Rift','Reiterate'):
   c=self.give(name);self.assertEqual(c.card_type,'instant');self.assertEqual(c.effect,'unsupported')
   self.assertIn('instant',self.t.rules.get(c.object_id).types)
 def test_merchant_scroll_finds_rift(self):
  self.library('Cyclonic Rift');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Cyclonic Rift')
  self.cast('Merchant Scroll');self.assertIn('Cyclonic Rift',[c.name for c in self.p.hand])
 def test_merchant_scroll_excludes_reiterate(self):
  bad=self.library('Reiterate');self.t.tutor_policy=lambda r:bad
  with self.assertRaises(ValueError):self.cast('Merchant Scroll')
 def test_spellseeker_finds_rift(self):
  self.library('Cyclonic Rift');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Cyclonic Rift')
  self.cast('Spellseeker');self.assertIn('Cyclonic Rift',[c.name for c in self.p.hand]);self.t.assert_consistent()
 def test_spellseeker_excludes_reiterate(self):
  bad=self.library('Reiterate');self.t.tutor_policy=lambda r:bad
  with self.assertRaises(ValueError):self.cast('Spellseeker')
 def test_pending_premium_lands_are_not_in_current_deck(self):
  names={name for _,name in load_premium()}
  self.assertNotIn('Training Center',names);self.assertNotIn('Otawara, Soaring City',names)
 def test_lindblum_enters_tapped_and_produces_red(self):
  oid=self.t.enter_land(self.p,self.give('Lindblum, Industrial Regency').object_id)
  self.assertTrue(self.t.rules.get(oid).tapped);self.assertIn('Town',self.t.rules.get(oid).card.subtypes)
  self.t.rules.mana_pools[0]=(0,0,0);self.assertIsNone(self.t.resources.plan(0,Cost(red=1)))
  self.t.rules.get(oid).tapped=False;self.t.rules._dirty()
  self.assertIsNotNone(self.t.resources.plan(0,Cost(red=1)));self.assertIsNone(self.t.resources.plan(0,Cost(blue=1)))
  self.assertEqual(self.t.rules.get(oid).card.name,'Lindblum, Industrial Regency')
 def test_mystical_tutor_can_find_reiterate(self):
  self.library('Reiterate');self.t.tutor_policy=lambda r:next(c.object_id for c in r.cards if c.name=='Reiterate')
  self.cast('Mystical Tutor');self.assertEqual(self.p.library[-1].name,'Reiterate')
if __name__=='__main__':unittest.main()
