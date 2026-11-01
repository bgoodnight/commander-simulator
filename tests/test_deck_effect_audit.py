"""Pinned six-deck audit stays conservative about what is executable."""
import json
import unittest

from commander_sim.deck_effect_audit import (
    MECHANIC_PATTERNS, audit_all, audit_snapshot, verified_suboperations,
)
from commander_sim.deck_fixtures import FIXTURES


class DeckMechanicAuditTests(unittest.TestCase):
    def test_all_six_pinned_decks_are_covered_without_missing_oracle(self):
        self.assertEqual(len(FIXTURES),6)
        inventory=audit_all()
        self.assertEqual(inventory["deck_count"],6)
        self.assertEqual(inventory["deck_card_entries"],448)
        self.assertGreaterEqual(inventory["distinct_oracle_ids"],290)
        for fixture in FIXTURES:
            rows=audit_snapshot(fixture)
            self.assertEqual(len(rows), inventory["decks"][fixture.key]["unique_printed_cards"])
            self.assertTrue(all(row.oracle_id and row.name for row in rows))

    def test_repeated_graveyard_token_and_sacrifice_are_discovered(self):
        audit=audit_all()
        for mechanic in ("graveyard","tokens","sacrifice","draw","mana"):
            self.assertGreater(audit["distinct_cards_by_mechanic"][mechanic],20)
        self.assertGreater(audit["decks"]["necron_dynasties"][
            "mechanic_candidates"]["graveyard"],10)
        self.assertGreater(audit["decks"]["mortarion_current"][
            "mechanic_candidates"]["sacrifice"],10)

    def test_verified_suboperation_is_distinct_from_entire_card_coverage(self):
        audit=audit_all()
        self.assertIn("not implemented",audit["disclaimer"].lower())
        self.assertEqual(sum(d["full_card_execution_verified"]
            for d in audit["decks"].values()),0)
        self.assertIn("reviewed_search_template",verified_suboperations("Fabricate"))
        self.assertIn("reviewed_mana_template",verified_suboperations("Sol Ring"))
        self.assertIn("historical_live_trigger_slot",
                      verified_suboperations("Young Pyromancer"))
        self.assertEqual(verified_suboperations("Invented Card"),())

    def test_each_audited_card_has_only_explicit_verified_registrations(self):
        for fixture in FIXTURES:
            for row in audit_snapshot(fixture):
                self.assertEqual(row.full_card_status,"not_established")
                self.assertEqual(row.verified_operations,
                                 verified_suboperations(row.name))
                self.assertEqual(len(row.candidates),len(set(row.candidates)))
                self.assertTrue(set(row.candidates)<=set(MECHANIC_PATTERNS))

    def test_report_is_deterministic_and_json_compatible(self):
        first=audit_all()
        second=audit_all()
        self.assertEqual(json.dumps(first,sort_keys=True),
                         json.dumps(second,sort_keys=True))


if __name__=="__main__":
    unittest.main()
