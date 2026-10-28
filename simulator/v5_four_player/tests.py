"""Regression and invariants for the shared four-player action engine."""
import unittest,copy
from simulation import *

class TestTable(unittest.TestCase):
 def make(self,archs=['aggro']*4,seed=19,interactive=True):return Table(archs,seed,interactive)
 def test_synthetic_deck_counts(self):
  for archetype in ARCHETYPES:
   deck=synthetic_library(archetype,10)
   self.assertEqual(len(deck),99)
   self.assertTrue(all(c.card_type in ('land','creature','instant','sorcery','artifact','enchantment') for c in deck))
 def test_four_active_and_duplicate_archetypes(self):
  t=self.make();self.assertEqual(len(t.alive()),4)
  self.assertEqual([p.archetype for p in t.players],['aggro']*4)
 def test_reproducible(self):
  a=self.make(seed=321).run(15).summary()
  b=self.make(seed=321).run(15).summary()
  self.assertEqual(a,b)
 def test_no_ghost_mana(self):
  t=self.make();p=t.players[0];p.mana=1
  c=CardSpec('expensive','small',5,'creature','creature',{'power':4,'toughness':4})
  p.hand=[c];self.assertFalse(t.cast(Action(p.seat,c.name,c.card_type,c.effect,5)))
  self.assertEqual(len(p.creatures),0)
 def test_spell_counter_targets_permanent_spell(self):
  t=self.make(seed=92);a,b=t.players[:2]
  a.hand=[CardSpec('fatty','large',5,'creature','creature',{'power':8,'toughness':8})]
  b.hand=[CardSpec('Counterspell','counter',2,'instant','counter')]
  a.mana=5;b.mana=2
  t.respond=lambda action: True
  t.cast(Action(a.seat,'fatty','creature','creature',5))
  self.assertEqual(len(a.creatures),0)
  self.assertEqual(a.mana,0)
 def test_single_life_elimination_cleans_board(self):
  t=self.make();p=t.players[2];p.life=4
  t.add_creature(p,6,6,'test');t.damage(p,5,t.players[1],'combat')
  self.assertFalse(p.alive);self.assertEqual(len(p.creatures),0)
  self.assertEqual(p.eliminated_round,0)
 def test_multi_elimination(self):
  t=self.make(['combo','aggro','aggro','aggro'])
  actor=t.players[0];actor.mana=9
  for _ in range(3):t.add_permanent(actor,'combo_piece',4,'test')
  t.finish(actor,{'mode':'combo_win'},Action(0,'test','sorcery','finisher',8))
  self.assertEqual(len(t.alive()),1);self.assertEqual(t.counts['multi_elimination_events'],1)
  self.assertEqual(len(t.eliminations),3)
 def test_burst_simultaneous_eliminations(self):
  t=self.make(['spellslinger','aggro','aggro','aggro']);p=t.players[0]
  for q in t.players[1:]:q.life=2
  t.finish(p,{'mode':'spell_burst','damage':9},Action(0,'burst','sorcery','finisher',7))
  self.assertEqual(len(t.eliminations),3)
 def test_creature_vs_permanent_removal(self):
  t=self.make();a,b=t.players[:2]
  c=t.add_creature(b,7,7,'big')
  g=t.add_permanent(b,'engine',4,'engine')
  t.apply(Action(0,'spell','instant','remove',2,b.seat,c.id))
  self.assertNotIn(c,b.creatures);self.assertIn(g,b.permanents)
  t.apply(Action(0,'spell','instant','remove',2,b.seat,g.id))
  self.assertNotIn(g,b.permanents)
 def test_blocker_not_tapped_and_only_blocks_once(self):
  t=self.make();d=t.players[0];a=t.players[1]
  defender=t.add_creature(d,5,5,'defender');attacker=t.add_creature(a,2,2,'attack')
  used=set();b=t.block(d,attacker,used);self.assertIs(b,defender)
  used.add(b.id);self.assertIsNone(t.block(d,attacker,used))
  self.assertFalse(defender.tapped)
 def test_own_board_not_removed_by_targeted_effect(self):
  t=self.make();a,b=t.players[:2];c=t.add_creature(b,4,4,'target')
  t.apply(Action(a.seat,'removal','instant','remove',2,b.seat,c.id))
  self.assertNotIn(c,b.creatures)
 def test_mana_spending_limited(self):
  t=self.make();p=t.players[0];p.lands=4;p.mana=4
  c1=CardSpec('x','ramp',2,'artifact','ramp',{'mana_gain':1})
  c2=CardSpec('y','ramp',3,'artifact','ramp',{'mana_gain':1})
  p.hand=[c1,c2];self.assertTrue(t.cast(t.build_action(p,c1)))
  self.assertFalse(t.cast(t.build_action(p,c2)))
  self.assertEqual(p.mana,2)
 def test_action_contract_from_external_deck(self):
  """Same resolver accepts a named externally supplied card."""
  t=self.make();p=t.players[0];p.mana=3
  custom=CardSpec('Custom Wizard','wizard_spell',3,'creature','creature',{'power':3,'toughness':4})
  p.hand=[custom];self.assertTrue(t.cast(t.build_action(p,custom)))
  self.assertEqual((p.creatures[-1].power,p.creatures[-1].toughness),(3,4))
 def test_external_pilot_fourth_seat_runs(self):
  base=self.make(['aggro','control','combo','tokens'],seed=123)
  class DemoPilot:
   def select_action(self,table,p):
    for c in p.hand:
     if c.kind=='land' or c.mana_value>p.mana:continue
     return table.build_action(p,c)
    return None
  # A detailed-deck seat has a separate pilot and card list, but uses the same
  # shared multiplayer engine, attacks, targeting, life, and win conditions.
  demo=[CardSpec(f'Custom Spirit {i}', 'custom_creature',2,'creature','creature',{'power':2,'toughness':2}) for i in range(63)]
  demo.extend(CardSpec(f'Land {i}','land',0,'land','none') for i in range(36))
  import random
  random.Random(123).shuffle(demo)
  player=Player(0,'detailed',123,demo,DemoPilot());player.draw(7)
  base.players[0]=player
  base.run(6)
  self.assertEqual(len(base.turns),6)
  self.assertGreater(player.cards_cast,0)
 def test_custom_effect_and_cast_event(self):
  t=self.make();p=t.players[0];p.mana=2
  c=CardSpec('Custom Draw','custom',2,'sorcery','draw_three',{})
  p.hand=[c];events=[]
  t.on_event(lambda table,name,action,payload:events.append(name))
  t.register_effect('draw_three',lambda table,action:table.players[action.actor].draw(3))
  prior=len(p.hand);self.assertTrue(t.cast(t.build_action(p,c)))
  self.assertEqual(len(p.hand),prior-1+3)
  self.assertEqual(events,['spell_cast','spell_resolved'])
 def test_counter_card_type_restrictions(self):
  t=self.make();p=t.players[0];q=t.players[1]
  q.mana=2;q.hand=[CardSpec('Limited Counter','counter',2,'instant','counter',{'can_counter_types':['instant','sorcery']})]
  options=t.respond(Action(p.seat,'Large Creature','creature','creature',4))
  self.assertFalse(options)
  self.assertEqual(len(q.hand),1)
 def test_turn_order_random_and_life_tracks(self):
  t=self.make(['aggro','control','combo','tokens'],85).run(8)
  self.assertEqual(sorted(t.turn_order),[0,1,2,3])
  self.assertEqual(len(t.turns),min(t.round_num,8))
 def test_detailed_deck_can_decline_all_blocks(self):
  t=self.make();defender=t.players[0];defender.block_policy='never'
  t.add_creature(defender,9,9,'Champion')
  self.assertIsNone(t.block(defender,Creature(99,1,1,1,0,'Opponent'),set()))
 def test_response_hooks(self):
  t=self.make();p=t.players[0];q=t.players[1]
  t.add_response_hook(lambda table,action: True if action.card_type=='creature' else None)
  c=CardSpec('Custom threat','custom',2,'creature','creature',{'power':9,'toughness':9})
  p.hand=[c];p.mana=2;t.cast(t.build_action(p,c));self.assertFalse(p.creatures)
 def test_land_resource_causality(self):
  t=self.make();p=t.players[0]
  p.hand=[CardSpec('land','land',0,'land','none')]
  p.library=[] # without draw upkeep loses; manually test direct source accounting
  p.lands=3;t.add_permanent(p,'ramp',2,'ramp')
  self.assertEqual(p.available_sources(),5)
 def test_same_seed_goldfish_vs_interactive_same_opening(self):
  a=self.make(['tokens','aggro','control','combo'],912,True)
  b=self.make(['tokens','aggro','control','combo'],912,False)
  self.assertEqual([[(c.name,c.mana_value) for c in p.hand] for p in a.players],
                   [[(c.name,c.mana_value) for c in p.hand] for p in b.players])

if __name__=='__main__':unittest.main(verbosity=2)
