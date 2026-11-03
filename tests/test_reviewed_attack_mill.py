"""Physical attack-mill follow-ups retain exact milled card provenance."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_attack_mill import (
    reviewed_attack_mill, resolve_attack_mill)


class AttackMillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = next(f for f in FIXTURES if f.key == "necron_dynasties")
        cls.catalog = {row["deck_name"]: row["card"] for row in
                       json.loads(f.snapshot_path.read_text())["cards"]}

    def setUp(self):
        K, Z, C = _load_live_kernel()
        self.kernel = K()
        self.zones = Z(self.kernel, seed=17)
        self.C = C

    def add(self, name, zone, *, types=("creature",), subtypes=(),
            seat=0, identity=None):
        row = self.catalog.get(name, {})
        return self.zones.add(self.C(identity or row.get("oracle_id", "test:" + name),
            name, frozenset(types), subtypes=frozenset(subtypes),
            base_power=4, base_toughness=6, coverage="approx"), seat, zone)

    def test_szarekh_mills_and_returns_only_eligible_milled_card(self):
        attacker = self.add("Szarekh, the Silent King", "battlefield")
        self.add("Ordinary Zombie", "library")
        self.add("Artifact Soldier", "library", types=("artifact", "creature"))
        self.add("Instant", "library", types=("instant",))
        out = resolve_attack_mill(self.zones, self.catalog, attacker)
        self.assertEqual(len(out.milled_ids), 3)
        self.assertIsNotNone(out.returned_id)
        self.assertEqual(self.kernel.get(out.returned_id).card.name, "Artifact Soldier")
        self.assertEqual(self.kernel.get(out.returned_id).zone, "hand")
        self.assertEqual(len(self.zones.ids(0, "graveyard")), 2)
        self.assertFalse(out.token_ids)
        self.assertTrue(self.zones.assert_consistent())

    def test_szarekh_may_retrieve_vehicle(self):
        attacker = self.add("Szarekh, the Silent King", "battlefield")
        self.add("Vehicle", "library", types=("artifact",), subtypes=("Vehicle",))
        out = resolve_attack_mill(self.zones, self.catalog, attacker)
        self.assertEqual(self.kernel.get(out.returned_id).card.name, "Vehicle")
        self.assertTrue(self.zones.assert_consistent())

    def test_monolith_creates_one_token_per_milled_creature(self):
        # Crew eligibility is tested by combat; this fixture models a
        # successfully crewed Vehicle that is already a creature.
        attacker = self.add("Necron Monolith", "battlefield",
                            types=("artifact", "creature"), subtypes=("Vehicle",))
        self.add("Creature A", "library")
        self.add("Rock", "library", types=("artifact",))
        self.add("Creature B", "library")
        out = resolve_attack_mill(self.zones, self.catalog, attacker)
        self.assertEqual(len(out.milled_ids), 3)
        self.assertEqual(len(out.token_ids), 2)
        self.assertIsNone(out.returned_id)
        for oid in out.token_ids:
            obj = self.kernel.get(oid)
            self.assertTrue(obj.token)
            self.assertEqual(obj.controller, 0)
            self.assertTrue({"artifact", "creature"} <= obj.types)
            self.assertEqual((obj.power, obj.toughness), (2, 2))
            self.assertIn("Necron", obj.subtypes)
        self.assertTrue(self.zones.assert_consistent())

    def test_short_library_and_zero_creature_hits(self):
        attacker = self.add("Necron Monolith", "battlefield",
                            types=("artifact", "creature"))
        self.add("Rock", "library", types=("artifact",))
        out = resolve_attack_mill(self.zones, self.catalog, attacker)
        self.assertEqual(len(out.milled_ids), 1)
        self.assertEqual(out.token_ids, ())
        self.assertTrue(self.zones.assert_consistent())

    def test_missing_review_or_uncrewed_source_never_mills(self):
        attacker = self.add("Necron Monolith", "battlefield",
                            types=("artifact",), subtypes=("Vehicle",))
        self.add("Creature A", "library")
        self.assertIsNone(resolve_attack_mill(self.zones, self.catalog, attacker))
        self.assertEqual(len(self.zones.ids(0, "library")), 1)
        altered = dict(self.catalog["Necron Monolith"])
        altered["oracle_text"] = "Different Oracle revision"
        self.assertIsNone(reviewed_attack_mill("Necron Monolith", altered))
        source = self.add("Szarekh, the Silent King", "battlefield")
        self.assertIsNone(resolve_attack_mill(
            self.zones, {"Szarekh, the Silent King": altered}, source))
        self.assertEqual(len(self.zones.ids(0, "library")), 1)


if __name__ == "__main__":
    unittest.main()
