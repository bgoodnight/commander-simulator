"""Targeted invariants for the partial simulator. Run: python test_magnus_v16_sim_v2.py"""
import unittest
from magnus_v16_sim_v2 import Game,LIB

class TestRulesProxies(unittest.TestCase):
 def test_deck_size(self):self.assertEqual(len(LIB),99)
 def new(self):
  x=Game('rush',1234)
  x.hand=[];x.deck=[];x.turn=4;x.lands=[('Island','U',False),('Mountain','R',False)]
  return x
 def test_sorcery_discount_and_colored_pips(self):
  x=self.new();x.magnus=True;x.add_token(count=3)
  self.assertEqual(x.resolved_cost('Capsize',True,True),(1,2,0)) # 1+3-3
  self.assertEqual(x.resolved_cost('Searing Touch',True,True),(1,0,1))
  self.assertEqual(x.resolved_cost('Magnus the Red'),(3,1,1))
 def test_sorcerer_class_does_not_cast_creatures(self):
  x=self.new();x.level=2;x.board['Young Pyromancer']=3
  x.tapped.update({'L0','L1'})
  self.assertFalse(x.try_pay('Baral, Chief of Compliance',spell=False))
  self.assertTrue(x.try_pay('Ponder',spell=True))
 def test_lute_restricted_to_spells(self):
  x=self.new();x.board['Resonating Lute']=3
  # One island can't be two mana for non-spell.
  x.lands=[('Island','U',False)]
  self.assertFalse(x.try_pay('Baral, Chief of Compliance',spell=False))
  self.assertTrue(x.try_pay('Counterspell',spell=True))
 def test_sol_ring_floats_unspent_mana(self):
  x=self.new();x.lands=[];x.rocks={'Sol Ring':3}
  self.assertTrue(x.try_pay('Sol Ring',execute=True)) # pay 1, float 1
  self.assertEqual(x.float['C'],1)
  self.assertTrue(x.try_pay('Sol Ring'))
 def test_summoning_sickness_and_class(self):
  x=self.new();x.level=2;x.board['Young Pyromancer']=4
  self.assertFalse(any(s.sid=='C:Young Pyromancer' for s in x.sources(True)))
  x.board['Young Pyromancer']=3
  self.assertTrue(any(s.sid=='C:Young Pyromancer' for s in x.sources(True)))
 def test_storm_kiln_trigger(self):
  x=self.new();x.board['Storm-Kiln Artist']=3;x.board['Harmonic Prodigy']=3
  x.noncreature_trigger('Preordain')
  self.assertEqual(x.treasures,2)
 def test_token_restrictions(self):
  x=self.new();x.board['Phyrexian Altar']=3;x.add_token()
  self.assertEqual(x.available_wizards(),0)
  x.board['Arcane Adaptation']=3
  self.assertEqual(x.available_wizards(),1)
 def test_no_duplicate_mana(self):
  x=self.new();x.lands=[('Island','U',False)];x.hand=['Ponder','Preordain']
  self.assertTrue(x.cast_card('Ponder'))
  self.assertFalse(x.cast_card('Preordain'))
 def test_paired_seed_is_deterministic(self):
  a=Game('rush',42,True).run();b=Game('rush',42,True).run()
  self.assertEqual(a,b)

 def test_signet_activation_requires_input(self):
  x=self.new();x.lands=[];x.rocks={'Izzet Signet':3}
  self.assertFalse(x.try_pay('Third Path Iconoclast'))
  x.lands=[('Island','U',False)]
  self.assertTrue(x.try_pay('Third Path Iconoclast'))
 def test_phyrexian_altar_sacrifices_actual_token(self):
  x=self.new();x.board['Phyrexian Altar']=2;x.magnus=True;x.add_token(count=2)
  x.lands=[]
  self.assertTrue(x.try_pay('Mystic Speculation',spell=True,buyback=True,execute=True))
  self.assertEqual(x.live_tokens(),1)
 def test_stormsplitter_tokens_expire(self):
  x=self.new();x.board['Stormsplitter']=2;x.turn=5
  x.noncreature_trigger('Preordain')
  self.assertEqual(x.live_tokens(),1)
  x.tokens=[t for t in x.tokens if t[3] is None or t[3]>x.turn]
  self.assertEqual(x.live_tokens(),0)

if __name__=='__main__':unittest.main()
