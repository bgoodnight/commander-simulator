"""Seven-card cleanup, verified maximum hand size and bounded discard pilot."""
import unittest

from commander_sim.early_game_runner import _load_live_kernel, run_bounded_early_game
from commander_sim.hand_cleanup import cleanup_hand, maximum_hand_size

VESSEL = ("9965d9c5-2ebf-4a6c-930e-55c5890979be",
          "You have no maximum hand size.\n{T}: Add {C}.")
TOWER = ("c23e5b80-08d2-4e24-9908-fe2aa4f30f6f",
         "You have no maximum hand size.\n{T}: Add {C}.")


class PhysicalCleanupTests(unittest.TestCase):
    def setUp(self):
        K, Z, C = _load_live_kernel()
        self.kernel, self.zones, self.C = K(), Z(K(), seed=4), C
        # LiveZones and kernel must be one object, not two fixture kernels.
        self.zones = Z(self.kernel, seed=4)
        self.raw = {
            "Swamp": {"type_line": "Basic Land — Swamp", "cmc": 0},
            "Mountain": {"type_line": "Basic Land — Mountain", "cmc": 0},
            "Heavy Spell": {"type_line": "Sorcery", "mana_cost": "{8}{B}", "cmc": 9},
            "Cheap Spell": {"type_line": "Sorcery", "mana_cost": "{B}", "cmc": 1},
            "Future Spell": {"type_line": "Sorcery", "mana_cost": "{3}{B}", "cmc": 4},
            "Thought Vessel": {"oracle_id": VESSEL[0], "oracle_text": VESSEL[1]},
            "Reliquary Tower": {"oracle_id": TOWER[0], "oracle_text": TOWER[1]},
        }

    def card(self, name, zone="hand", *, owner=0, types=None, oracle=None):
        if types is None:
            types = {"land"} if name in {"Swamp", "Mountain", "Reliquary Tower"} else (
                {"artifact"} if name == "Thought Vessel" else {"sorcery"})
        return self.zones.add(self.C(
            oracle or self.raw.get(name, {}).get("oracle_id", "test:" + name),
            name, frozenset(types), coverage="approx"), owner, zone)

    def fill(self, names):
        return [self.card(name) for name in names]

    def test_cleanup_discards_exact_excess_to_real_graveyard(self):
        self.fill(["Swamp", "Swamp", "Swamp", "Cheap Spell", "Future Spell",
                   "Heavy Spell", "Heavy Spell", "Heavy Spell", "Heavy Spell"])
        before = tuple(self.zones.ids(0, "hand"))
        outcome = cleanup_hand(self.zones, 0, self.raw)
        self.assertEqual(outcome.hand_before, 9)
        self.assertEqual(outcome.maximum_hand_size, 7)
        self.assertEqual(outcome.hand_after, 7)
        self.assertEqual(len(outcome.discarded), 2)
        self.assertEqual(len(self.zones.ids(0, "graveyard")), 2)
        for item in outcome.discarded:
            self.assertIn(item.old_id, before)
            self.assertNotIn(item.old_id, self.kernel.objects)
            self.assertIn(item.graveyard_id, self.zones.ids(0, "graveyard"))
            self.assertEqual(self.kernel.get(item.graveyard_id).card.name, item.name)
        self.assertTrue(self.zones.assert_consistent())

    def test_early_land_and_cheap_supported_spell_retained(self):
        self.fill(["Swamp", "Swamp", "Cheap Spell", "Future Spell",
                   "Heavy Spell", "Heavy Spell", "Heavy Spell", "Heavy Spell"])
        outcome = cleanup_hand(self.zones, 0, self.raw,
                               supported_action=lambda obj: obj.card.name == "Cheap Spell")
        self.assertEqual([item.name for item in outcome.discarded], ["Heavy Spell"])
        self.assertIn("Cheap Spell", self.zones.names(0, "hand"))
        self.assertEqual(self.zones.names(0, "hand").count("Swamp"), 2)

    def test_board_mana_changes_discard_preference(self):
        self.fill(["Swamp", "Swamp", "Swamp", "Cheap Spell", "Future Spell",
                   "Heavy Spell", "Heavy Spell", "Heavy Spell"])
        for _ in range(10):
            self.card("Mountain", "battlefield")
        outcome = cleanup_hand(self.zones, 0, self.raw)
        # On a well-developed board, an extra land is less useful than a
        # high-cost payoff that is now affordable.
        self.assertEqual(outcome.discarded[0].name, "Swamp")

    def test_no_discard_at_or_under_limit_and_idempotent(self):
        self.fill(["Swamp"] * 7)
        self.assertEqual(cleanup_hand(self.zones, 0, self.raw).discarded, ())
        self.card("Cheap Spell")
        one = cleanup_hand(self.zones, 0, self.raw)
        two = cleanup_hand(self.zones, 0, self.raw)
        self.assertEqual(len(one.discarded), 1)
        self.assertEqual(two.discarded, ())
        self.assertEqual(len(self.zones.ids(0, "hand")), 7)

    def test_verified_reliquary_tower_and_thought_vessel_disable_limit(self):
        for name, (oracle, _) in (
                ("Reliquary Tower", TOWER), ("Thought Vessel", VESSEL)):
            with self.subTest(name=name):
                k, z, C = _load_live_kernel()
                self.kernel, self.zones, self.C = k(), None, C
                self.zones = z(self.kernel, seed=6)
                self.fill(["Swamp"] * 9)
                self.card(name, "battlefield", oracle=oracle)
                self.assertIsNone(maximum_hand_size(self.kernel, 0, self.raw))
                self.assertEqual(cleanup_hand(self.zones, 0, self.raw).discarded, ())
                self.assertEqual(len(self.zones.ids(0, "hand")), 9)

    def test_false_text_and_opponent_source_do_not_disable_limit(self):
        self.fill(["Swamp"] * 8)
        self.card("Thought Vessel", "battlefield", oracle=VESSEL[0], owner=1)
        self.assertEqual(maximum_hand_size(self.kernel, 0, self.raw), 7)
        self.card("Reliquary Tower", "battlefield", oracle="fake:oracle")
        self.assertEqual(maximum_hand_size(self.kernel, 0, self.raw), 7)
        self.assertEqual(len(cleanup_hand(self.zones, 0, self.raw).discarded), 1)

    def test_cleanup_policy_is_replay_deterministic(self):
        def replay():
            k, z, C = _load_live_kernel()
            self.kernel, self.zones, self.C = k(), None, C
            self.zones = z(self.kernel, seed=42)
            self.fill(["Heavy Spell"] * 4 + ["Cheap Spell"] * 4)
            return cleanup_hand(self.zones, 0, self.raw), self.zones.names(0, "hand")
        a, ha = replay()
        b, hb = replay()
        self.assertEqual(a, b)
        self.assertEqual(ha, hb)

    def test_all_six_decks_enforce_cleanup_and_replay(self):
        for deck in ("magnus_premium", "magnus_budget", "wretched_ranks",
                     "mortarion_current", "mortarion_ideal", "necron_dynasties"):
            with self.subTest(deck=deck):
                a = run_bounded_early_game(deck, seed=9, turns=6)
                b = run_bounded_early_game(deck, seed=9, turns=6)
                self.assertEqual(a, b)
                for turn in a["events"]:
                    limit = turn["maximum_hand_size"]
                    if limit is not None:
                        self.assertLessEqual(turn["hand_size"], limit)
                    self.assertEqual(
                        turn["cleanup_discard_count"],
                        max(0, turn["hand_size_before_cleanup"] -
                            (limit if limit is not None else turn["hand_size_before_cleanup"])))
                    self.assertEqual(turn["cleanup_discard_count"],
                                     sum(e["type"] == "cleanup_discard"
                                         for e in turn["events"]))
                for turn, state in zip(a["events"], a["state_snapshots"]):
                    self.assertEqual(
                        turn["library_size"] + turn["hand_size"] +
                        len(state["battlefield"]) + len(state["graveyard"]) +
                        len(state["exile"]) + 1, 100)


if __name__ == "__main__":
    unittest.main()
