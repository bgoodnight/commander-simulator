"""End-to-end pinned M3 bounded actions on the actual IndexedKernel."""
import unittest

from commander_sim.early_game_runner import run_bounded_early_game


class BoundedEarlyGameTests(unittest.TestCase):
    def test_wretched_ranks_deterministic_zone_based_turns(self):
        a = run_bounded_early_game("wretched_ranks", seed=18, turns=6)
        b = run_bounded_early_game("wretched_ranks", seed=18, turns=6)
        self.assertEqual(a, b)
        self.assertEqual(a["mode"], "bounded_authoritative_early_actions")
        self.assertEqual(len(a["state_snapshots"]), 6)
        self.assertEqual([x["turn"] for x in a["events"]], list(range(1, 7)))
        self.assertEqual(a["deck_intelligence"]["automatic"]["source"],
                         "authoritative_printed_board_features")
        self.assertNotIn("win_rate", a)

    def test_magnus_premium_uses_same_shared_runner(self):
        result = run_bounded_early_game("magnus_premium", seed=17, turns=6)
        self.assertEqual(result["commander"], "Magnus the Red")
        self.assertEqual(len(result["state_snapshots"]), 6)
        self.assertTrue(all(state["source"] == "authoritative_game"
                            for state in result["state_snapshots"]))
        self.assertIn("no modeled combat", result["limits"])

    def test_creature_casts_have_actual_source_and_resolution_events(self):
        # Sweep reproducible random hands; a reviewed subset must actually cast.
        plays = []
        for seed in range(12):
            result = run_bounded_early_game("wretched_ranks", seed=seed, turns=6)
            for turn in result["events"]:
                events = turn["events"]
                casts = [event for event in events if event["type"] == "creature_cast"]
                resolutions = [event for event in events if event["type"] == "creature_resolved"]
                self.assertEqual(len(casts), len(resolutions))
                for cast in casts:
                    self.assertTrue(cast["source_object_ids"])
                    self.assertEqual(cast["fidelity"], "limited_generic_cast")
                plays.extend(casts)
        self.assertGreater(len(plays), 0)

    def test_no_unsupported_casts_and_all_100_cards_remain_in_zones(self):
        for deck in ("wretched_ranks", "magnus_premium", "magnus_budget"):
            report = run_bounded_early_game(deck, seed=3, turns=6)
            for turn, state in zip(report["events"], report["state_snapshots"]):
                total = (turn["library_size"] + turn["hand_size"]
                         + len(state["battlefield"]) + 1)  # commander
                self.assertEqual(total, 100)
                self.assertTrue(all(event["type"] in {
                    "draw", "untap", "land_play", "creature_cast", "creature_resolved",
                } for event in turn["events"]))

    def test_invalid_deck_or_horizon_fails_closed(self):
        for key, turns in (("necron_dynasties", 6), ("wretched_ranks", 0),
                           ("wretched_ranks", 11)):
            with self.assertRaises(ValueError):
                run_bounded_early_game(key, turns=turns)


if __name__ == "__main__":
    unittest.main()
