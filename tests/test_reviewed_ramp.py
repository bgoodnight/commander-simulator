"""Checks for generic, source-reviewed ramp/ritual descriptors."""
import unittest
from types import SimpleNamespace

from commander_sim.reviewed_ramp import (
    reviewed_ramp, reviewed_ritual, basic_land_candidates,
)


class BasicRampContractTests(unittest.TestCase):
    def test_reviewed_ramp_requires_correct_source_characteristics(self):
        card = dict(oracle_id="oracle-1", type_line="Artifact",
                    oracle_text="Search your library for a basic land card, put it onto the battlefield tapped.",
                    mana_cost="{1}")
        self.assertIsNotNone(reviewed_ramp("Wayfarer's Bauble", card))
        self.assertIsNone(reviewed_ramp("Wayfarer's Bauble", dict(card, type_line="Creature")))
        self.assertIsNone(reviewed_ramp("Wayfarer's Bauble", dict(card, oracle_text="Draw a card.")))

    def test_basic_search_uses_only_actual_library_objects(self):
        def item(oid, name, card_id):
            return SimpleNamespace(card=SimpleNamespace(name=name, card_id=card_id))
        objects = {
            1:item(1,"Swamp","a"), 2:item(2,"Swamp","a"),
            3:item(3,"Island","b"), 4:item(4,"Swamp","wrong"),
        }
        zones = SimpleNamespace(
            kernel=SimpleNamespace(get=lambda oid: objects[oid]),
            ids=lambda seat, zone: (1,2,3,4))
        catalog = {
            "Swamp":{"oracle_id":"a", "type_line":"Basic Land — Swamp"},
            "Island":{"oracle_id":"b", "type_line":"Basic Land — Island"},
        }
        self.assertEqual(basic_land_candidates(zones,0,catalog,2,same_type=True),(1,2))
        self.assertEqual(len(basic_land_candidates(zones,0,catalog,3,same_type=True)),0)

    def test_ritual_does_not_infer_other_black_spells(self):
        card = dict(oracle_id="oracle-2", type_line="Instant",
                    mana_cost="{B}", oracle_text="Add {B}{B}{B}.")
        self.assertTrue(reviewed_ritual("Dark Ritual",card))
        self.assertFalse(reviewed_ritual("Other Ritual",card))
        self.assertFalse(reviewed_ritual("Dark Ritual",dict(card,mana_cost="{2}{B}")))


if __name__ == "__main__":
    unittest.main()
