"""Bounded real-action batch counts only actual live-kernel events."""
import unittest

from commander_sim.bounded_batch import run_bounded_batch


class BoundedBatchTests(unittest.TestCase):
    def test_repeated_seeds_identical(self):
        a = run_bounded_batch("wretched_ranks", seeds=3, turns=4)
        self.assertEqual(a, run_bounded_batch("wretched_ranks", seeds=3, turns=4))
        self.assertEqual(a["mode"], "bounded_real_action_batch")
        self.assertEqual(len(a["turns"]), 4)
        self.assertNotIn("win_rate", a)
        self.assertIn("Never interpret", a["limitations"])

    def test_source_and_board_measures_have_sensible_ranges(self):
        r = run_bounded_batch("magnus_premium", seeds=3, turns=6)
        for row in r["turns"]:
            self.assertGreaterEqual(row["mean_lands_in_play"], 0)
            self.assertGreaterEqual(row["mean_reviewed_creatures_in_play"], 0)
            self.assertGreaterEqual(row["mean_unsupported_hand_cards"], 0)
            self.assertGreaterEqual(row["pct_with_reviewed_creature_by_turn"], 0)
            self.assertLessEqual(row["pct_with_reviewed_creature_by_turn"], 100)
        self.assertEqual(r["turns"][-1]["turn"], 6)

    def test_invalid_seed_count(self):
        for n in (0, -1, 1001, True):
            with self.subTest(n=n), self.assertRaises(ValueError):
                run_bounded_batch("wretched_ranks", seeds=n)


if __name__ == "__main__":
    unittest.main()
