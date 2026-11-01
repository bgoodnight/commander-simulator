"""Regression: exploratory physical Magnus uses the existing shared kernel.

The original owned list is preserved; an explicit off-color substitution is
used solely in the fixture. No invented spell effects or win-rate reporting.
"""
import unittest
from commander_sim.deck_fixtures import FIXTURES,EXPERIMENTAL_FIXTURES
from commander_sim.early_game_runner import run_bounded_early_game

class PhysicalMagnusTests(unittest.TestCase):
    def test_trial_is_excluded_from_six_published_decks(self):
        self.assertEqual(len(FIXTURES),6)
        self.assertEqual(len(EXPERIMENTAL_FIXTURES),1)
        self.assertEqual(EXPERIMENTAL_FIXTURES[0].key,"magnus_physical_trial")
        self.assertIn("simulation_only",EXPERIMENTAL_FIXTURES[0].status)
        self.assertNotIn("Narset's Rebuke",
                         EXPERIMENTAL_FIXTURES[0].deck_path.read_text())
    def test_shared_physical_kernel_replays_and_preserves_card_count(self):
        a=run_bounded_early_game("magnus_physical_trial",seed=12,turns=4)
        b=run_bounded_early_game("magnus_physical_trial",seed=12,turns=4)
        self.assertEqual(a,b)
        self.assertEqual(a["mode"],"bounded_authoritative_early_actions")
        self.assertEqual(len(a["state_snapshots"]),4)
        for turn in a["events"]:
            self.assertLessEqual(turn["hand_size"],7)
            for event in turn["events"]:
                if event["type"]=="source_paid_candidate":
                    self.assertEqual(event["fidelity"],"payment_preview_only")
                    self.assertEqual(event["effect_status"],"unsupported")
                    self.assertTrue(event["source_object_ids"])
                    self.assertNotIn("stack_object_id",event)
    def test_new_card_diagnostics_do_not_enable_unknown_effects(self):
        result=run_bounded_early_game("magnus_physical_trial",seed=2,turns=6)
        self.assertNotIn("win_rate",result)
        self.assertEqual(len(result["events"]),6)
        self.assertTrue(result["limits"])
        self.assertTrue(any(turn["unsupported_cards_in_hand"] for turn in result["events"]))
