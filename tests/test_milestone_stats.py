"""Seeded strategy reporting never turns missing game turns into losses."""
import unittest
from commander_sim.milestone_stats import summarize_strategy_runs


def turn(number, *, hand=0, battlefield=0, tutor=False, combo="incomplete",
         pieces_accessible=0, pieces_on_battlefield=0):
    return {
        "turn": number, "battlefield_count": battlefield,
        "groups_on_battlefield": {"wizards": battlefield},
        "key_cards": [{"id": "engine", "card": "Engine", "hand": hand,
                       "battlefield": battlefield, "graveyard": 0,
                       "engine_verified_tutor_access": tutor}],
        "combos": [{"id": "main_combo", "status": combo,
                    "pieces_required": 2, "pieces_accessible": pieces_accessible,
                    "pieces_on_battlefield": pieces_on_battlefield}],
    }


def run(seed, turns, deck="hash1"):
    return {"seed": seed, "deck_sha256": deck,
            "report": {"source": "authoritative_game_snapshots", "turns": turns}}


class MilestoneStatsTests(unittest.TestCase):
    def test_distinguishes_hand_tutor_play_and_operational(self):
        a = run(2, [turn(1, hand=1), turn(2, tutor=True),
                    turn(3, battlefield=1, combo="all_pieces_present_unverified",
                         pieces_on_battlefield=2, pieces_accessible=2)])
        b = run(1, [turn(1), turn(2), turn(3, combo="engine_verified_operational",
                    pieces_accessible=2, pieces_on_battlefield=2)])
        result = summarize_strategy_runs([a, b], checkpoints=(2, 3))
        by2 = result["checkpoints"][0]["milestones"]
        self.assertEqual(by2["key:engine:hand"]["rate"], 0.5)
        self.assertEqual(by2["key:engine:tutorable"]["rate"], 0.5)
        self.assertEqual(by2["key:engine:battlefield"]["rate"], 0)
        by3 = result["checkpoints"][1]["milestones"]
        self.assertEqual(by3["key:engine:battlefield"]["rate"], 0.5)
        self.assertEqual(by3["combo:main_combo:pieces_in_play"]["rate"], 1.0)
        self.assertEqual(by3["combo:main_combo:operational"]["rate"], 0.5)
        self.assertNotIn("win_rate", result)

    def test_censors_truncated_runs(self):
        a = run(1, [turn(1), turn(2, battlefield=1)])
        b = run(2, [turn(1)])
        result = summarize_strategy_runs([a, b], checkpoints=(1, 2, 3))
        self.assertEqual(result["checkpoints"][0]["eligible_runs"], 2)
        self.assertEqual(result["checkpoints"][1]["eligible_runs"], 1)
        self.assertEqual(result["checkpoints"][1]["censored_before_checkpoint"], 1)
        self.assertEqual(result["checkpoints"][2]["eligible_runs"], 0)
        self.assertIsNone(result["checkpoints"][2]["milestones"]["key:engine:accessible"]["rate"])
        self.assertIsNone(result["checkpoints"][2]["mean_board_count"])

    def test_counts_ever_reached_even_when_no_longer_in_hand(self):
        r = run(7, [turn(1, hand=1), turn(2), turn(3)])
        result = summarize_strategy_runs([r], checkpoints=(3,))
        self.assertEqual(result["checkpoints"][0]["milestones"]["key:engine:hand"]["rate"], 1.0)

    def test_seed_order_independent(self):
        a = run(3, [turn(1), turn(2)])
        b = run(1, [turn(1, hand=1), turn(2)])
        self.assertEqual(summarize_strategy_runs([a, b], checkpoints=(2,)),
                         summarize_strategy_runs([b, a], checkpoints=(2,)))

    def test_distinguishes_group_board_mean_at_checkpoint(self):
        a = run(3, [turn(1), turn(2, battlefield=2)])
        b = run(2, [turn(1), turn(2, battlefield=0)])
        value = summarize_strategy_runs([a, b], checkpoints=(2,))
        self.assertEqual(value["checkpoints"][0]["mean_group_counts"]["wizards"], 1.0)

    def test_rejects_duplicate_seeds_or_revision(self):
        a = run(1, [turn(1)])
        with self.assertRaises(ValueError):
            summarize_strategy_runs([a, a])
        with self.assertRaises(ValueError):
            summarize_strategy_runs([a, run(2, [turn(1)], deck="different")])

    def test_rejects_unsupported_observation_mode(self):
        a = run(1, [turn(1)])
        a["report"]["source"] = "early_game_observation_aggregate"
        with self.assertRaises(ValueError):
            summarize_strategy_runs([a])

    def test_rejects_skipped_turn_or_redefined_group(self):
        with self.assertRaises(ValueError):
            summarize_strategy_runs([run(1, [turn(1), turn(3)])])
        a = run(1, [turn(1)])
        b = run(2, [turn(1)])
        b["report"]["turns"][0]["groups_on_battlefield"] = {"zombies": 1}
        with self.assertRaises(ValueError):
            summarize_strategy_runs([a, b])

    def test_rejects_bad_checkpoints(self):
        for checkpoints in ((), (0,), (5, 3), (2, 2), (True,)):
            with self.subTest(checkpoints=checkpoints), self.assertRaises(ValueError):
                summarize_strategy_runs([run(1, [turn(1)])], checkpoints=checkpoints)

    def test_no_strategy_definitions_still_reports_board(self):
        empty = {"turn": 1, "battlefield_count": 4,
                 "groups_on_battlefield": {}, "key_cards": [], "combos": []}
        result = summarize_strategy_runs([run(1, [empty])], checkpoints=(1,))
        self.assertEqual(result["checkpoints"][0]["mean_board_count"], 4)
        self.assertEqual(result["checkpoints"][0]["milestones"], {})


if __name__ == "__main__":
    unittest.main()
