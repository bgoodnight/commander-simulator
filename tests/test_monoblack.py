import subprocess,sys,unittest
from pathlib import Path
from commander_sim.snapshots import validate_snapshot
from commander_sim.observation import observe
ROOT=Path(__file__).resolve().parents[1]
FIXTURES=(('Ghoulcaller Gisa','decklists/wretched_ranks_foundations_precon_2026.txt','simulator/card_data/gisa_scryfall.json',33),
          ('Mortarion, Daemon Primarch','decklists/mortarion_purchase_reconciled_candidate_2026_10_27.txt','simulator/card_data/mortarion_scryfall.json',32))
class MonoBlackTests(unittest.TestCase):
 def test_offline_validation(self):
  for commander,deck,data,swamps in FIXTURES:
   with self.subTest(commander=commander):
    result=validate_snapshot(ROOT/deck,ROOT/data,commander=commander)
    self.assertEqual(result.deck.count,100)
    self.assertEqual(sum(q for _,n,q in result.deck.cards if n=='Swamp'),swamps)
 def test_explicit_commander_must_match(self):
  commander,deck,data,_=FIXTURES[0]
  with self.assertRaises(ValueError):validate_snapshot(ROOT/deck,ROOT/data,commander=FIXTURES[1][0])
 def test_observation_is_reproducible_and_does_not_cast(self):
  for commander,deck,data,_ in FIXTURES:
   with self.subTest(commander=commander):
    r=observe(ROOT/deck,ROOT/data,commander=commander,seed=0)
    self.assertEqual(r,observe(ROOT/deck,ROOT/data,commander=commander,seed=0))
    self.assertTrue(any(t['land_played']=='Swamp' for t in r['trace']))
    self.assertTrue(all(t['library_count']+t['hand_count']+t['battlefield_count']+1==100 for t in r['trace']))
    self.assertTrue(all(not t['playable_now'] for t in r['trace']))
 def test_live_engine_rejects_unsupported_commander(self):
  _,deck,_,_=FIXTURES[0]
  p=subprocess.run([sys.executable,str(ROOT/'run_simulation.py'),'--deck-file',str(ROOT/deck)],capture_output=True,text=True)
  self.assertNotEqual(p.returncode,0);self.assertIn('Expected exactly one Magnus',p.stderr)
if __name__=='__main__':unittest.main()
