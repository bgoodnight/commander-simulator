"""Cross-deck gap inventory is diagnostic, not executable Oracle authority."""
import json
import unittest

from commander_sim.deck_fixtures import FIXTURES, EXPERIMENTAL_FIXTURES
from commander_sim.named_effect_coverage import named_effect_coverage
from tools.audit_effect_gaps import audit_effect_gaps, candidate_families, FORMAT


class EffectGapAuditTests(unittest.TestCase):
    def test_all_eight_pinned_deck_variants_have_reproducible_statuses(self):
        report=audit_effect_gaps()
        self.assertEqual(report["format"],FORMAT)
        self.assertEqual(report["deck_variants"],8)
        self.assertGreaterEqual(report["unique_pinned_oracle_cards"],299)
        for fixture in (*FIXTURES,*EXPERIMENTAL_FIXTURES):
            row=report["by_deck"][fixture.key]
            self.assertEqual(sum(row["status_counts"].values()),
                             len(json.loads(fixture.snapshot_path.read_text())["cards"]))
        self.assertEqual(json.dumps(report,sort_keys=True),
                         json.dumps(audit_effect_gaps(),sort_keys=True))
        self.assertIn("not whole-card support",report["disclaimer"])

    def test_source_reviewed_registries_are_not_falsely_reported_missing(self):
        report=named_effect_coverage(fixtures=(*FIXTURES,*EXPERIMENTAL_FIXTURES))
        cards=report["decks"]
        self.assertIn("enter_trigger",
                      cards["necron_dynasties"]["cards"]["Canoptek Scarab Swarm"][
                          "reviewed_suboperations"])
        self.assertIn("removal_spell",
                      cards["wretched_ranks"]["cards"]["Go for the Throat"][
                          "reviewed_suboperations"])
        for deck in ("magnus_budget","magnus_premium"):
            self.assertIn("draw_spell",
                          cards[deck]["cards"]["Meeting of Minds"][
                              "reviewed_suboperations"])
        self.assertIn("draw_spell",
                      cards["magnus_physical_trial"]["cards"]["Deduce"][
                          "reviewed_suboperations"])
        self.assertEqual(cards["necron_dynasties"][
                         "cards"]["Canoptek Scarab Swarm"]["status"],"partial")

    def test_candidate_wording_never_claims_permission_or_full_support(self):
        self.assertIn("graveyard_recursion",
                      candidate_families("Return target creature from your graveyard."))
        self.assertIn("token_generation",
                      candidate_families("Create two 2/2 Zombie creature tokens."))
        self.assertIn("mana_cost_alternatives",
                      candidate_families("Convoke (Tap creatures.)"))
        report=audit_effect_gaps(FIXTURES)
        self.assertEqual(report["deck_variants"],6)
        self.assertIn("candidate families",report["disclaimer"])
        self.assertTrue(all(item["variant_count"]>=2
            for item in report["recurring_gaps_across_variants"]))


if __name__=="__main__":
    unittest.main()
