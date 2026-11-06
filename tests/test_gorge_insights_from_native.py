import json
from pathlib import Path
import tempfile
import unittest

from tools.gorge_insights_from_native import build


class NativeInsightInputTests(unittest.TestCase):
    def test_refuses_recording_that_does_not_match_summary(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "native").mkdir()
            (root / "runs.jsonl").write_text(json.dumps({
                "seed": 10, "hero_seat": 1, "decks": ["a", "hero", "b", "c"],
                "finished": True, "replay_verified": True, "replay_chain": "right"}) + "\n")
            (root / "native/gorge-seed-10.json").write_text(json.dumps({
                "seed": 10, "hero_seat": 1, "decks": ["a", "hero", "b", "c"], "chain": "wrong"}))
            catalog = root / "catalog.json"
            catalog.write_text(json.dumps({"decks": [{"key": "hero", "deck_sha256": "a" * 64}]}))
            with self.assertRaisesRegex(ValueError, "does not match summary"):
                build(root, catalog, "hero", root / "report.json")
            self.assertFalse((root / "report.json").exists())


if __name__ == "__main__":
    unittest.main()
