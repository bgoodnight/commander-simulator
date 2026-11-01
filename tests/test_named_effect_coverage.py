"""Exact six-deck source registry coverage without false full-card claims."""
import json
import unittest

from commander_sim.named_effect_coverage import (
    REGISTRATIONS,named_effect_coverage)


class NamedCoverageTests(unittest.TestCase):
    def test_all_pinned_299_named_cards_have_explicit_coverage_status(self):
        report=named_effect_coverage()
        self.assertEqual(report["deck_count"],6)
        self.assertEqual(report["deck_card_entries"],448)
        self.assertEqual(report["distinct_oracle_cards"],299)
        self.assertEqual(report["full_card_coverage_confirmed"],0)
        self.assertEqual(sum(row["count"] for row in
            report["unregistered_by_card_type"].values()),
            report["without_registered_suboperations"])
        self.assertEqual(sorted(name for row in
            report["unregistered_by_card_type"].values()
            for name in row["names"]),report["unregistered_names"])
        self.assertEqual(
            report["with_reviewed_suboperations"]+
            report["without_registered_suboperations"],299)

    def test_reviewed_named_effects_span_multiple_decks(self):
        report=named_effect_coverage()
        kinds=report["reviewed_unique_cards_by_operation"]
        for kind in ("mana","search","fixed_token_spell","cast_trigger",
                     "death_trigger","sacrifice_activation",
                     "phase_trigger","unearth","flashback","enter_trigger",
                     "cost_reduction","graveyard_creature_cast"):
            self.assertIn(kind,kinds)
            self.assertGreater(kinds[kind],0)
        self.assertGreaterEqual(report["with_reviewed_suboperations"],30)

    def test_any_registered_card_remains_partial_and_unknown_unregistered(self):
        report=named_effect_coverage()
        deck=report["decks"]["wretched_ranks"]["cards"]
        self.assertIn("death_trigger",deck["Headless Rider"]["reviewed_suboperations"])
        self.assertIn("sacrifice_activation",deck["Ghoulcaller Gisa"]["reviewed_suboperations"])
        self.assertEqual(deck["Ghoulcaller Gisa"]["status"],"partial")
        self.assertEqual(report["decks"]["necron_dynasties"]["full_card_coverage_confirmed"],0)

    def test_report_is_deterministic_and_has_no_fabricated_claims(self):
        a=named_effect_coverage()
        b=named_effect_coverage()
        self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
        self.assertIn("suboperation",a["disclaimer"])
        self.assertTrue(all(len(values)>0 for values in REGISTRATIONS.values()))

    def test_each_deck_named_card_is_accounted_without_omission(self):
        report=named_effect_coverage()
        for key,deck in report["decks"].items():
            with self.subTest(deck=key):
                self.assertEqual(deck["with_reviewed_suboperations"]+
                                 deck["without_registered_suboperations"],
                                 deck["named_cards"])
                self.assertTrue(all(x["status"] in {"partial","not_registered"}
                     for x in deck["cards"].values()))


if __name__=="__main__":
    unittest.main()
