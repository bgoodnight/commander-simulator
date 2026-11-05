"""Precon compatibility is staging-only, per-deck, and fail-closed."""
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from tools.check_gorge_precon_compatibility import export, summarize



def make_queue():
    rows = []
    for i in range(60):
        key = f"deck-{i:02d}"
        rows.append({
            "key": key, "name": key, "commander": f"Commander {i}",
            "color_identity": ["U"], "oracle_complete": True,
            "unresolved_card_names": [], "decklist_sha256": str(i),
            "active_opponent": False, "qualification": "queued_not_approved",
            "oracle_card_annotations": [
                {"name": f"Commander {i}", "count": 1, "resolved": True},
                {"name": "Basic Test Land", "count": 99, "resolved": True},
            ],
        })
    return {
        "schema": "gorge-precon-qualification-queue-v1",
        "status": "certification_pending_no_activation",
        "oracle_bulk_sha256": "fixture-sha",
        "source_catalog_commit": "fixture-commit",
        "decks": rows,
    }

class CompatibilityTests(unittest.TestCase):
    def test_export_and_per_deck_reports(self):
        queue = make_queue()
        for d in queue["decks"]:
            d["oracle_card_annotations"] = [
                {"name": d["commander"], "count": 1, "resolved": True},
                {"name": "Basic Test Land", "count": 99, "resolved": True},
            ]
        with TemporaryDirectory() as temp:
            names = export(queue, Path(temp))
            self.assertEqual(len(names), 60)
            self.assertEqual(len(list(Path(temp).glob("*.json"))), 60)
        records = [
            {"deck_key": key, "load_ok": i != 1,
             "commander_valid": i != 1,
             "cards_loaded": 100 if i != 1 else 0,
             "commander_count": 1 if i != 1 else 0,
             **({"error": "unknown card"} if i == 1 else {})}
            for i, key in enumerate(names)
        ]
        report = summarize(queue, records)
        self.assertEqual(report["tested"], 60)
        self.assertEqual(report["import_passed"], 59)
        self.assertEqual(report["import_failed"], 1)
        self.assertEqual(report["qualified"], 0)
        self.assertEqual(report["decks"][1]["error"], "unknown card")

    def test_missing_or_duplicate_results_fail(self):
        queue = build_queue(*fixtures())
        row = {"deck_key": queue["decks"][0]["key"], "load_ok": True,
               "commander_valid": True, "cards_loaded": 100, "commander_count": 1}
        with self.assertRaisesRegex(ValueError, "Missing"):
            summarize(queue, [row])
        with self.assertRaisesRegex(ValueError, "repeated"):
            summarize(queue, [row, row])


if __name__ == "__main__":
    unittest.main()
