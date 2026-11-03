"""Reusable attack-token recipe uses verified source and one physical kernel."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.early_game_runner import _load_live_kernel
from commander_sim.reviewed_attack_tokens import (
    reviewed_attack_token_recipe, resolve_attack_tokens,
)


class ReviewedAttackTokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = next(f for f in FIXTURES if f.key == "wretched_ranks")
        cls.catalog = {x["deck_name"]: x["card"] for x in
                       json.loads(fixture.snapshot_path.read_text())["cards"]}

    def setUp(self):
        kernel_type, zones_type, card_type = _load_live_kernel()
        self.kernel = kernel_type()
        self.zones = zones_type(self.kernel, seed=1)
        self.card_type = card_type

    def add(self, name, *, verified=True, seat=0):
        raw = self.catalog[name]
        identity = raw["oracle_id"] if verified else "unreviewed:" + name
        definition = self.card_type(
            identity, name, frozenset({"creature"}),
            base_power=6, base_toughness=6, coverage="approx")
        return self.zones.add(definition, seat, "battlefield")

    def test_grave_titan_attack_creates_two_physical_zombies(self):
        attacker = self.add("Grave Titan")
        result = resolve_attack_tokens(self.zones, self.catalog, attacker)
        self.assertEqual(len(result), 2)
        for oid in result:
            token = self.kernel.get(oid)
            self.assertEqual(token.zone, "battlefield")
            self.assertEqual(token.controller, 0)
            self.assertTrue(token.token)
            self.assertIn("Zombie", token.subtypes)
            self.assertEqual((token.power, token.toughness), (2, 2))
        self.assertEqual(self.kernel.get(attacker).zone, "battlefield")

    def test_other_seat_receives_its_own_tokens(self):
        attacker = self.add("Grave Titan", seat=2)
        result = resolve_attack_tokens(self.zones, self.catalog, attacker)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(self.kernel.get(oid).controller == 2 for oid in result))

    def test_unverified_identity_or_text_is_not_executable(self):
        attacker = self.add("Grave Titan", verified=False)
        self.assertEqual(resolve_attack_tokens(self.zones, self.catalog, attacker), ())
        raw = dict(self.catalog["Grave Titan"])
        raw["oracle_text"] = "Unreviewed revised effect"
        self.assertIsNone(reviewed_attack_token_recipe("Grave Titan", raw))
        self.assertEqual(resolve_attack_tokens(
            self.zones, {"Grave Titan": raw}, attacker), ())

    def test_nonbattlefield_source_does_not_trigger(self):
        attacker = self.add("Grave Titan")
        self.zones.move(attacker, "graveyard", "destroy")
        self.assertEqual(resolve_attack_tokens(self.zones, self.catalog, attacker), ())


if __name__ == "__main__":
    unittest.main()
