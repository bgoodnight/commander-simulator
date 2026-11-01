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
        self.assertNotIn("1 Narset's Rebuke",
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

    def test_new_mana_rocks_reuse_typed_templates(self):
        from commander_sim.card_cache import pinned_deck_entries
        from commander_sim.deck_fixtures import SHARED_CATALOG
        from commander_sim.reviewed_rocks import reviewed_rock
        fixture=EXPERIMENTAL_FIXTURES[0]
        data={e["deck_name"]:e["card"] for e in pinned_deck_entries(
            fixture.deck_path,fixture.manifest_path,SHARED_CATALOG)}
        powerstone=reviewed_rock("Worn Powerstone",data["Worn Powerstone"],frozenset("UR"))
        self.assertIsNotNone(powerstone)
        self.assertTrue(powerstone[0].enter_tapped)
        self.assertEqual(powerstone[0].mana_modes[0].output,("C","C"))
        lantern=reviewed_rock("Chromatic Lantern",data["Chromatic Lantern"],frozenset("UR"))
        self.assertIsNotNone(lantern)
        self.assertEqual(set(mode.output for mode in lantern[0].mana_modes),{("U",),("R",)})
        changed=dict(data["Worn Powerstone"],oracle_text="The artifact doesn't tap for mana")
        self.assertRaises(ValueError,reviewed_rock,"Worn Powerstone",changed,frozenset("UR"))

    def test_reviewed_creatures_have_pinned_generic_cast_permission_only(self):
        from commander_sim.card_cache import pinned_deck_entries
        from commander_sim.deck_fixtures import SHARED_CATALOG
        from commander_sim.reviewed_early_cards import reviewed_creature
        fixture=EXPERIMENTAL_FIXTURES[0]
        data={e["deck_name"]:e["card"] for e in pinned_deck_entries(
            fixture.deck_path,fixture.manifest_path,SHARED_CATALOG)}
        for name in ("Elementalist Adept","Firebrand Archer","Reckless Scholar","Thermo-Alchemist"):
            with self.subTest(card=name):
                self.assertTrue(reviewed_creature(fixture.key,name,data[name]))
                other=dict(data[name],oracle_id="incorrect")
                self.assertFalse(reviewed_creature(fixture.key,name,other))
        self.assertFalse(reviewed_creature(fixture.key,"Harmonic Prodigy",data["Harmonic Prodigy"]))
