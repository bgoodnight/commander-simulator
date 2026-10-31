import unittest
from pathlib import Path
from commander_sim.identities import CardRegistry
from commander_sim.snapshots import validate_snapshot
ROOT=Path(__file__).resolve().parents[1]
DECK=ROOT/'decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt'
SNAPSHOT=ROOT/'simulator/card_data/flameslinger_v0_7_scryfall.json'

class IdentityTests(unittest.TestCase):
    def setUp(self):self.registry=CardRegistry(validate_snapshot(DECK,SNAPSHOT))
    def test_unfamiliar_verified_body_and_cost(self):
        card=self.registry.get('Stormsplitter');face=card.primary_face()
        self.assertIn('creature',face.types);self.assertIn('Wizard',face.subtypes)
        self.assertEqual((face.power,face.toughness),(1,4))
        self.assertEqual(face.colors,frozenset({'R'}))
        self.assertEqual(face.mana_cost,'{3}{R}')
    def test_adventure_main_face_has_unknown_face_values(self):
        card=self.registry.get('Lindblum, Industrial Regency');face=card.primary_face()
        self.assertEqual(face.types,frozenset({'land'}));self.assertIn('Town',face.subtypes)
        self.assertIsNone(face.mana_value);self.assertIsNone(face.keywords)
    def test_unreviewed_layout_fails_closed(self):
        card=self.registry.get('Sanar, Unfinished Genius // Wild Idea')
        self.assertEqual(card.layout,'prepare')
        with self.assertRaises(NotImplementedError):card.primary_face()
    def test_unknown_identity(self):
        with self.assertRaises(KeyError):self.registry.get('Not a real card')
if __name__=='__main__':unittest.main()
