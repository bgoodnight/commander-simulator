import unittest
from pathlib import Path
from commander_sim.observation import observe, _mulligan_decision, _source_colors
ROOT=Path(__file__).resolve().parents[1]
DECK=ROOT/'decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt'
SNAPSHOT=ROOT/'simulator/card_data/flameslinger_v0_7_scryfall.json'

class ObservationTests(unittest.TestCase):
    def test_repeatable_and_conserves_cards(self):
        a=observe(DECK,SNAPSHOT,seed=0);b=observe(DECK,SNAPSHOT,seed=0)
        self.assertEqual(a,b);self.assertEqual(len(a['opening_hand']),7)
        self.assertEqual(len(a['trace']),6)
        for t in a['trace']:
            self.assertEqual(t['library_count']+t['hand_count']+t['battlefield_count']+1,100)
            self.assertEqual(t['battlefield_count'],len(t['modeled_sources']))
            self.assertLessEqual(sum(t['modeled_basic_sources'].values()),t['battlefield_count'])
            self.assertEqual(t['playable_now'],[])
            self.assertTrue(all(x['status']=='candidate_if_supported' for x in t['candidate_if_supported']))
    def test_scenario_and_reserve_are_qualified(self):
        threat={'turn':3,'description':'scripted opposing noncreature spell'}
        result=observe(DECK,SNAPSHOT,seed=0,reserve=1,threats=[threat])
        self.assertEqual(result['trace'][2]['scripted_threats'],[threat])
        self.assertIn('not modeled',result['land_policy'])
        self.assertLessEqual(result['trace'][0]['reserved_mana'],1)
        self.assertTrue(all(not x['playable_now'] for x in result['trace']))
    def test_sources_and_draws_reconcile(self):
        result=observe(DECK,SNAPSHOT,seed=3)
        self.assertEqual(result['trace'][0]['library_count'],91)
        self.assertTrue(all(t['land_played'] in (None,'Island','Mountain','Command Tower') for t in result['trace']))
        self.assertEqual(result['trace'][5]['library_count'],86)
    def test_invalid_inputs_fail(self):
        for kwargs in ({'turns':0},{'reserve':-1},{'threats':[{'turn':0}]},{'seed':True},{'mulligan':'invalid'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):observe(DECK,SNAPSHOT,**kwargs)
    def test_first_multiplayer_mulligan_is_free_and_reproducible(self):
        a=observe(DECK,SNAPSHOT,seed=0,mulligan='one-free')
        self.assertEqual(a,observe(DECK,SNAPSHOT,seed=0,mulligan='one-free'))
        self.assertEqual(a['mulligan']['decision'],'mulligan')
        self.assertEqual(len(a['mulligan']['initial_hand']),7)
        self.assertEqual(len(a['opening_hand']),7)
        self.assertNotEqual(a['mulligan']['initial_hand'],a['opening_hand'])
        for t in a['trace']:
            self.assertEqual(t['library_count']+t['hand_count']+t['battlefield_count']+1,100)
    def test_mulligan_policy_does_not_guess_unknown_faces(self):
        self.assertEqual(_mulligan_decision(1,1),'uncertain_keep')
        self.assertEqual(_mulligan_decision(0,1),'mulligan')
        self.assertEqual(_mulligan_decision(2,1),'keep')
    def test_command_tower_reports_commander_colors(self):
        result=observe(DECK,SNAPSHOT,seed=2)
        tower=next(s for t in result['trace'] for s in t['modeled_sources'] if s['card']=='Command Tower')
        self.assertEqual(set(tower['colors']),{'U','R'})
        self.assertEqual(_source_colors('Command Tower',frozenset({'B'})),('B',))

if __name__=='__main__':unittest.main()
