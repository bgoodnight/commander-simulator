"""Pinned six-turn mana rock actions share the same authoritative kernel."""
import unittest

from commander_sim.early_game_runner import run_bounded_early_game
from commander_sim.bounded_batch import run_bounded_batch


class RockEarlyTurnTests(unittest.TestCase):
    def test_reviewed_ramp_produces_real_artifact_objects_in_seed_sweep(self):
        rocks = []
        for seed in range(16):
            run = run_bounded_early_game("wretched_ranks", seed=seed, turns=6)
            for row in run["events"]:
                casts = [x for x in row["events"] if x["type"] == "artifact_cast"]
                resolves = [x for x in row["events"] if x["type"] == "artifact_resolved"]
                self.assertEqual(len(casts), len(resolves))
                for event in casts:
                    self.assertEqual(event["fidelity"], "limited_generic_cast")
                rocks.extend(casts)
            for row, state in zip(run["events"], run["state_snapshots"]):
                self.assertEqual(row["mana_rock_count"],
                                 sum(obj["name"] in {
                                     "Sol Ring", "Mind Stone", "Arcane Signet",
                                     "Charcoal Diamond", "Commander's Sphere"
                                 } for obj in state["object_views"]["battlefield"]))
        self.assertGreater(len(rocks), 0)

    def test_pinned_izzet_rocks_can_be_deployed_in_magnus_runs(self):
        occurrences = []
        for seed in range(16):
            run = run_bounded_early_game("magnus_premium", seed=seed, turns=6)
            for turn in run["events"]:
                occurrences.extend(x["card"] for x in turn["events"]
                                   if x["type"] == "artifact_cast")
        self.assertGreater(len(occurrences), 0)

    def test_bounded_batch_reports_ramp_separately_from_creature_board(self):
        batch = run_bounded_batch("wretched_ranks", seeds=2, turns=5)
        self.assertEqual(batch["seed_count"], 2)
        self.assertEqual(len(batch["turns"]), 5)
        self.assertNotIn("win_rate", batch)


if __name__ == "__main__":
    unittest.main()
