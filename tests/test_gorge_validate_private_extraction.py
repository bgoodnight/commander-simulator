"""Synthetic contract tests, no credentials or private source data."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.gorge_validate_private_extraction import validate


class ExtractionValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "acquisition-report.json").write_text(json.dumps(
            {"hero": "magnus_premium", "run_attempt": "test-1", "attempts": 1}))
        self.write("hero_features.jsonl", [{"seed": 10}])
        self.write("landmarks.jsonl", [self.land(t) for t in (4, 8, 12)])
        self.write("event-features.jsonl", [self.event(t) for t in (4, 8, 12)])
        self.write("analytic_features.jsonl", [self.table(t) for t in (4, 8, 12)])
        self.write("card_exposures.jsonl", [{"seed": 10, "landmark_global_turn": 4,
            "run_attempt": "test-1", "source_event_seq": 40, "model_eligible": False,
            "card_name": "Private example"}])

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, rows):
        (self.root / name).write_text("".join(json.dumps(r) + "\n" for r in rows))

    def land(self, t):
        return {"seed": 10, "hero": "magnus_premium", "landmark_global_turn": t,
                "landmark_observed": True, "source_event_seq": 10*t}

    def event(self, t):
        return {"seed": 10, "hero": "magnus_premium", "landmark_global_turn": t,
                "landmark_observed": True, "event_cutoff_seq": 10*t}

    def table(self, t):
        return {"seed": 10, "deck": "magnus_premium", "landmark_global_turn": t,
                "landmark_observed": True, "source_event_seq": 10*t, "model_eligible": False}

    def test_success_receipt_contains_counts_not_card_names(self):
        receipt = validate(self.root, "test-1", "magnus_premium")
        self.assertEqual(receipt["joined_rows"], 3)
        self.assertEqual(receipt["sparse_card_rows"], 1)
        self.assertNotIn("Private example", json.dumps(receipt))

    def test_rejects_event_cutoff_drift(self):
        rows = [self.event(t) for t in (4,8,12)]
        rows[0]["event_cutoff_seq"] = 41
        self.write("event-features.jsonl", rows)
        with self.assertRaisesRegex(ValueError, "cutoff"):
            validate(self.root, "test-1", "magnus_premium")

    def test_rejects_outcome_eligibility(self):
        rows = [self.table(t) for t in (4,8,12)]
        rows[0]["model_eligible"] = True
        self.write("analytic_features.jsonl", rows)
        with self.assertRaisesRegex(ValueError, "eligible"):
            validate(self.root, "test-1", "magnus_premium")

    def test_rejects_card_future_leakage(self):
        rows = [{"seed": 10, "landmark_global_turn": 4,
                 "run_attempt": "test-1", "source_event_seq": 80, "model_eligible": False}]
        self.write("card_exposures.jsonl", rows)
        with self.assertRaisesRegex(ValueError, "cutoff"):
            validate(self.root, "test-1", "magnus_premium")


if __name__ == "__main__":
    unittest.main()
