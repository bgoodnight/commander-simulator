import copy,unittest
from engine import Catalog,Game
from combos import Combos
from pilot import Pilot

class ModelTests(unittest.TestCase):
    def setUp(self):self.cat=Catalog();self.g=Game(self.cat,1234,trace=True);self.g.turn=5;self.g.hand=[];self.g.deck=[]
    def island(self,n=1):self.g.lands.extend([('Island','U')]*n)
    def red(self,n=1):self.g.lands.extend([('Mountain','R')]*n)
    def test_card_count(self):
        self.assertEqual(len(self.cat.library),99)
        self.assertEqual(sum(self.cat.deck_counts.values())+1,100)
    def test_card_metadata_available(self):
        self.assertEqual(self.cat.get('Young Pyromancer')['effects'][0]['op'],'create_token')
        self.assertEqual(self.cat.get('Storm-Kiln Artist')['effects'][0]['event'],'cast_or_copy_instant_sorcery')
    def test_swap_card_removes_trigger_without_code_change(self):
        self.g.board['Young Pyromancer']=1;self.g.event('cast_instant_sorcery','Preordain')
        self.assertEqual(self.g.token_count(),1)
        # Remove a named card from the board: its abilities stop automatically.
        self.g.board.pop('Young Pyromancer');self.g.event('cast_instant_sorcery','Preordain')
        self.assertEqual(self.g.token_count(),1)
        # Add a newly catalogued card using an existing effect handler: no engine edits.
        self.cat.cards['Experimental Sorcerer']={'type':'creature','cost':[1,1,0],
          'status':'modeled','subtypes':['Wizard'],'effects':[{'event':'cast_instant_sorcery','op':'create_token','token':'Wizard','amount':2}]}
        self.g.board['Experimental Sorcerer']=1;self.g.event('cast_instant_sorcery','Preordain')
        self.assertEqual(self.g.token_count(),3)
    def test_deck_swap_independent_from_card_library(self):
        import json,tempfile
        from pathlib import Path
        original=self.cat.deck_counts
        swapped=dict(original)
        swapped.pop('Young Pyromancer')
        swapped['Preordain']=2  # test only; two copies may be illegal in Commander but verifies count loading
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'swap.json'
            p.write_text(json.dumps({'name':'test swapped deck','commander':'Magnus the Red','cards':swapped}))
            new=Catalog(deck_path=p)
            self.assertNotIn('Young Pyromancer',new.library)
            self.assertEqual(new.library.count('Preordain'),2)
            self.assertIn('Young Pyromancer',new.cards) # rules retained, inactive in deck
    def test_enter_triggers_only_on_creature_that_enters(self):
        self.g.board['Spellseeker']=1
        self.g.hand=['Sorcerer Class'];self.island();self.red()
        self.assertTrue(self.g.cast('Sorcerer Class'))
        self.assertNotIn('Spellseeker',self.g.hand)
        self.assertEqual(len(self.g.deck),0)
    def test_harmonic_pyromancer_double(self):
        self.g.board={'Young Pyromancer':1,'Harmonic Prodigy':1}
        self.g.event('cast_instant_sorcery','Preordain')
        self.assertEqual(self.g.token_count(),2)
    def test_stormsplitter_copies_trigger_as_wizards(self):
        self.g.board={'Stormsplitter':1,'Harmonic Prodigy':1}
        self.g.event('cast_instant_sorcery','Ponder')
        self.assertEqual(self.g.token_count(),2)
        self.g.event('cast_instant_sorcery','Ponder')
        self.assertEqual(self.g.token_count(),8) # original + two token copies each trigger twice
        self.g.end_turn();self.assertEqual(self.g.token_count(),0)
    def test_signet_needs_activation_mana(self):
        self.g.board={'Izzet Signet':1};self.assertFalse(self.g.can_pay('Third Path Iconoclast'))
        self.island();self.assertTrue(self.g.can_pay('Third Path Iconoclast'))
        self.assertTrue(self.g.pay('Third Path Iconoclast'))
        self.assertIn('A:Izzet Signet',self.g.tapped)
    def test_sol_ring_surplus_floats(self):
        self.g.board={'Sol Ring':1};self.assertTrue(self.g.pay('Sol Ring'))
        self.assertEqual(self.g.floating[2],1)
    def test_lute_not_creature_ramp(self):
        self.g.board={'Resonating Lute':1};self.island()
        self.assertFalse(self.g.can_pay('Baral, Chief of Compliance'))
        self.assertTrue(self.g.can_pay('Counterspell'))
    def test_sorcerer_class_restricted_mana(self):
        self.g.board={'Sorcerer Class':1,'Young Pyromancer':1};self.g.class_levels={'Sorcerer Class':2};self.island()
        self.assertFalse(self.g.can_pay('Baral, Chief of Compliance'))
        self.assertTrue(self.g.can_pay('Counterspell'))
    def test_spells_discount_including_buyback(self):
        self.g.board={'Magnus the Red':1};self.g.add_tokens('Spawn',4)
        self.assertEqual(self.g.resolve_cost('Searing Touch',True),(0,0,1))
        self.assertEqual(self.g.resolve_cost('Magnus the Red'),(3,1,1))
    def test_buyback_returns_to_hand(self):
        self.g.board={'Magnus the Red':1,'Storm-Kiln Artist':1};self.g.add_tokens('Spawn',4)
        self.g.hand=['Searing Touch'];self.red()
        self.assertTrue(self.g.cast('Searing Touch',buyback=True))
        self.assertIn('Searing Touch',self.g.hand);self.assertEqual(self.g.treasures,1)
        self.assertTrue(self.g.can_pay('Searing Touch',buyback=True))
    def test_mystic_altar_combo_detected_with_enough_tokens(self):
        self.g.board={'Magnus the Red':1,'Young Pyromancer':1,'Phyrexian Altar':1};self.g.add_tokens('Spawn',2)
        self.g.hand=['Mystic Speculation'];self.island()
        self.assertIn('speculation_pyromancer_altar',[r['id'] for r in Combos().evaluate(self.g)])
    def test_class_combo_requires_level_2(self):
        self.g.board={'Magnus the Red':1,'Stormsplitter':1,'Sorcerer Class':1};self.g.add_tokens('Spawn',2)
        self.g.hand=['Mystic Speculation'];self.island()
        self.assertEqual(Combos().evaluate(self.g),[])
        self.g.class_levels['Sorcerer Class']=2
        self.assertIn('speculation_stormsplitter_class',[r['id'] for r in Combos().evaluate(self.g)])
    def test_underworld_breach_escape_increases_tokens(self):
        self.g.board={'Underworld Breach':1,'The Lost and the Damned':1};self.island()
        self.g.grave=['Preordain','Ponder','Telling Time','Impulse'];self.g.deck=['Island']
        self.assertTrue(self.g.cast('Preordain',from_grave=True))
        self.assertEqual(self.g.token_count(),1)
        self.assertIn('Preordain',self.g.grave)
        self.assertEqual(len(self.g.exile),3)
    def test_bounded_searing_touch_loop(self):
        self.g.board={'Magnus the Red':1,'Storm-Kiln Artist':1}
        self.g.add_tokens('Spawn',4);self.g.hand=['Searing Touch'];self.red()
        outcome=Combos().execute_bounded(self.g,'searing_storm_kiln',cycles=3)
        self.assertEqual(outcome['iterations'],3)
        self.assertTrue(outcome['sustainable'])
        self.assertIn('Searing Touch',self.g.hand)
        self.assertEqual(self.g.instant_sorcery_cast,3)
    def test_bounded_pyromancer_altar_loop(self):
        self.g.board={'Magnus the Red':1,'Young Pyromancer':1,'Phyrexian Altar':1}
        self.g.add_tokens('Spawn',2);self.g.hand=['Mystic Speculation'];self.island()
        result=Combos().execute_bounded(self.g,'speculation_pyromancer_altar',cycles=3)
        self.assertTrue(result['sustainable'])
        self.assertGreaterEqual(self.g.token_count(),2)
    def test_bounded_stormsplitter_class_loop(self):
        self.g.board={'Magnus the Red':1,'Stormsplitter':1,'Sorcerer Class':1}
        self.g.class_levels={'Sorcerer Class':2};self.g.add_tokens('Spawn',2)
        self.g.hand=['Mystic Speculation'];self.island()
        result=Combos().execute_bounded(self.g,'speculation_stormsplitter_class',cycles=3)
        self.assertTrue(result['sustainable'])
        self.assertGreaterEqual(self.g.token_count(),3)
    def test_pilot_deterministic(self):
        p=Pilot(self.cat)
        a=p.run(42,'rush',turns=6).summary();b=p.run(42,'rush',turns=6).summary()
        self.assertEqual(a,b)

if __name__=='__main__':unittest.main()
