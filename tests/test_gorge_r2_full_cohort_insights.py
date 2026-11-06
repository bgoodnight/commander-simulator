"""Regression tests for full-cohort native card feature joins and repeated seeds."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.gorge_card_insights import KINDS
from tools.gorge_r2_full_cohort_insights import FullCohortCardInsights


def digest(data):
    return hashlib.sha256(data).hexdigest()


class FullCohortInsightsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = b"manifest"
        self.games = b"games"
        self.ui = b"projection"

    def shard(self, batch, count=1, bad_hash=False, coverage=True):
        deck = "mortarion_current"
        folder = self.root / batch
        folder.mkdir()
        rows = []
        for seed in range(count):
            rows.append({
                "batch_id": batch, "deck": deck, "seed": seed,
                "chain": f"chain-{seed}", "game_id": f"{batch}/{deck}/0/{seed}",
                "source_sha256": "b" * 64, "hero_seat": 0,
                "decks_json": json.dumps([deck, "precon1", "precon2", "precon3"])
            })
        features = {
            "schema": "gorge-card-insights-shard-v1", "deck": deck,
            "deck_sha256": "a"*64, "completed_verified_games": count,
            "seed_chains": [[row["seed"], row["chain"]] for row in rows],
            "confirmed_tutors": 0,
            "categories": {kind: [] for kind in KINDS},
        }
        features["categories"]["played"] = [{
            "name": "Sol Ring",
            "counts": [[row["seed"], 1] for row in rows],
            "seen": [row["seed"] for row in rows],
            "durations": [], "timesPlayed": count,
            "events": [[row["seed"], 2] for row in rows]
        }]
        if not coverage:
            features["seed_chains"].pop()
        envelope = {
            "schema": "gorge-r2-card-feature-evidence-v1",
            "manifest_sha256": digest(self.manifest),
            "games_sha256": digest(self.games if not bad_hash else b"WRONG"),
            "ui_sha256": digest(self.ui),
            "source_recordings": {r["game_id"]: r["source_sha256"] for r in rows},
            "features": features
        }
        (folder / "card-insights.v1.json").write_text(json.dumps(envelope))
        return folder, rows

    def test_reused_seeds_across_batches_are_distinct_games(self):
        a, rows_a = self.shard("111-1", 2)
        b, rows_b = self.shard("222-1", 2)
        merger = FullCohortCardInsights()
        for folder, rows in ((a, rows_a), (b, rows_b)):
            merger.add(folder, self.manifest, self.games, self.ui, rows)
        result = merger.report("mortarion_current", rows_a + rows_b)
        self.assertEqual(result["verified_games"], 4)
        self.assertEqual(result["coverage"]["missing"], 0)
        self.assertEqual(result["categories"]["played"][0]["games"], 4)
        self.assertEqual(result["categories"]["played"][0]["eventCount"], 4)
        self.assertEqual(result["categories"]["played"][0]["average"], 1)
        self.assertEqual(result["categories"]["played"][0]["median"], 1)
        self.assertEqual(result["categories"]["played"][0]["exampleEvents"], [])

    def test_missing_shard_does_not_publish_partial_card_rankings(self):
        folder, rows = self.shard("111-1")
        another = {**rows[0], "game_id": "222-1/mortarion_current/0/0",
                   "batch_id": "222-1"}
        merger = FullCohortCardInsights()
        merger.add(folder, self.manifest, self.games, self.ui, rows)
        merger.add(self.root, self.manifest, self.games, self.ui, [another])
        self.assertIsNone(merger.report("mortarion_current", rows + [another]))

    def test_source_digest_and_game_coverage_fail_closed(self):
        folder, rows = self.shard("111-1", bad_hash=True)
        with self.assertRaisesRegex(ValueError, "verified R2 source"):
            FullCohortCardInsights().add(folder, self.manifest, self.games, self.ui, rows)
        folder, rows = self.shard("222-1", coverage=False)
        with self.assertRaisesRegex(ValueError, "coverage"):
            FullCohortCardInsights().add(folder, self.manifest, self.games, self.ui, rows)


if __name__ == "__main__":
    unittest.main()
