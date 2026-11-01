"""Curated strategy reporting stays optional on real kernel-based seeds."""
import unittest

from commander_sim.early_game_runner import run_bounded_early_game
from commander_sim.bounded_batch import run_bounded_batch


PROFILE = {
    "key_cards": [{"id": "undead_augur", "card": "Undead Augur",
                   "role": "conditional draw engine"}],
    "groups": [{"id": "zombie_creatures", "cards": ["Undead Augur", "Carrion Feeder"]}],
    "combos": [{"id": "illustrative_pair", "pieces": ["Undead Augur", "Carrion Feeder"]}],
}


class CuratedBoundedRunTests(unittest.TestCase):
    def test_curated_key_and_group_use_actual_board_and_hand(self):
        report = run_bounded_early_game("wretched_ranks", seed=3, turns=4, profile=PROFILE)
        turns = report["deck_intelligence"]["strategy"]["turns"]
        self.assertEqual(len(turns), 4)
        self.assertEqual(turns[0]["key_cards"][0]["card"], "Undead Augur")
        self.assertIn("zombie_creatures", turns[0]["groups_on_battlefield"])
        self.assertTrue(all(t["combos"][0]["status"] != "engine_verified_operational"
                            for t in turns))

    def test_seed_batch_curated_milestones_include_censored_safe_rates(self):
        result = run_bounded_batch("wretched_ranks", seeds=2, turns=4, profile=PROFILE)
        report = result["curated_milestones"]
        self.assertEqual(report["run_count"], 2)
        self.assertEqual(len(report["checkpoints"]), 4)
        labels = report["checkpoints"][3]["milestones"]
        self.assertIn("key:undead_augur:accessible", labels)
        self.assertIn("combo:illustrative_pair:pieces_in_play", labels)
        self.assertEqual(labels["combo:illustrative_pair:operational"]["rate"], 0)
        self.assertNotIn("win_rate", report)

    def test_unpinned_card_in_profile_is_not_accepted(self):
        bad = {"key_cards": [{"id": "unknown", "card": "Not in this deck"}]}
        with self.assertRaises(ValueError):
            run_bounded_early_game("wretched_ranks", seed=1, turns=1, profile=bad)


if __name__ == "__main__":
    unittest.main()
