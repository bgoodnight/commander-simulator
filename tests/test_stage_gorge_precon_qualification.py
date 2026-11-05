"""Regression checks for fail-closed 60-deck certification queue."""
import copy
import unittest

from tools.stage_gorge_precon_qualification import build_queue


def fixtures():
    decks = []
    picks = []
    for index in range(60):
        key = f"deck-{index:02d}"
        cards = [{"name": f"Card {index}", "count": 100, "resolved": True,
                  "oracle_id": str(index), "mana_value": 2, "types": ["Creature"]}]
        decks.append({
            "key": key, "name": key, "commander": f"Commander {index}",
            "set_code": "TEST", "release_date": "2025-01-01",
            "color_identity": ["U"], "cards": cards,
            "cards_resolved": 100, "is_duplicate_variant": False,
            "active_opponent": False, "counts": {"creatures": 100},
            "mechanic_keywords": {}, "nonland_mean_mana_value": 2,
        })
        picks.append({"key": key})
    enrichment = {
        "schema": "gorge-precon-card-metadata-enrichment-v1",
        "oracle_bulk_sha256": "abc", "source_catalog_commit": "commit",
        "as_of": "2026-11-05", "decks": decks,
    }
    panel = {
        "schema": "gorge-opponent-selection-assessment-v1",
        "status": "provisional_not_gorge_qualified",
        "source_oracle_sha256": "abc", "source_catalog_commit": "commit",
        "as_of": "2026-11-05", "selection_method": "test",
        "shortlist": picks,
    }
    return enrichment, panel


class QualificationQueueTests(unittest.TestCase):
    def test_stages_60_without_activation(self):
        result = build_queue(*fixtures())
        self.assertEqual(result["panel_size"], 60)
        self.assertTrue(all(not d["active_opponent"] for d in result["decks"]))
        self.assertTrue(all(d["qualification"] == "queued_not_approved" for d in result["decks"]))
        self.assertEqual(result["decks"][0]["oracle_card_annotations"][0]["oracle_id"], "0")

    def test_rejects_wrong_snapshot(self):
        a, b = fixtures()
        b["source_oracle_sha256"] = "other"
        with self.assertRaisesRegex(ValueError, "snapshot mismatch"):
            build_queue(a, b)

    def test_rejects_duplicate_selected_key(self):
        a, b = fixtures()
        b["shortlist"][1]["key"] = b["shortlist"][0]["key"]
        with self.assertRaisesRegex(ValueError, "Exactly 60"):
            build_queue(a, b)

    def test_rejects_live_or_duplicate_deck(self):
        for attr in ("active_opponent", "is_duplicate_variant"):
            a, b = fixtures()
            a["decks"][0][attr] = True
            with self.assertRaisesRegex(ValueError, "Duplicate or active"):
                build_queue(a, b)

    def test_rejects_invalid_card_counts(self):
        a, b = fixtures()
        a["decks"][0]["cards"][0]["count"] = 99
        with self.assertRaisesRegex(ValueError, "100-card"):
            build_queue(a, b)

    def test_retains_unresolved_names_but_blocks_certification(self):
        a, b = fixtures()
        a["decks"][0]["cards"][0]["resolved"] = False
        a["decks"][0]["cards_resolved"] = 0
        result = build_queue(a, b)
        self.assertFalse(result["decks"][0]["oracle_complete"])
        self.assertEqual(result["decks"][0]["unresolved_card_names"], ["Card 0"])
        self.assertFalse(result["decks"][0]["active_opponent"])


if __name__ == "__main__":
    unittest.main()
