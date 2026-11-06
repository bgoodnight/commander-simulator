"""Source-backed fixture checks for materialized summary and lazy replay pages."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    pa = pq = None

from tools.gorge_cohort_eligibility import fingerprint
from tools.gorge_r2_materialized_results import project
from tools.gorge_card_insights import KINDS


@unittest.skipIf(pq is None, "pyarrow is required")
class MaterializedResultsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.registry = Path("data/gorge_analytics_cohort_registry_v1.json")
        cohorts = json.loads(self.registry.read_text())["cohorts"]
        self.cohort = next(c for c in cohorts if c.get("deck") == "mortarion_current")
        self.shard = self.root / "source" / "123456-1" / "mortarion_current" / "0"
        self.shard.mkdir(parents=True)

    def build(self, count=26, leak=False, omit_projection=False):
        rows, games = [], []
        c = self.cohort
        deck = c["deck"]
        for seed in range(count):
            gid = f"123456-1/{deck}/0/{seed}"
            row = {
                "game_id": gid, "batch_id": "123456-1", "deck": deck,
                "seed": seed, "chain": f"chain-{seed}",
                "source_sha256": "b" * 64,
                "cohort_id": c["cohort_id"],
                "cohort_manifest_sha256": fingerprint(c),
                "finished": True, "replay_verified": True,
                "error": None, "draw": False,
                "hero_seat": 0, "winner_seat": seed % 2,
                "turns": seed % 8 + 1,
                "decks_json": json.dumps([deck, "precon1", "precon2", "precon3"])
            }
            row.update({k: c[k] for k in (
                "engine_commit", "rules_patch_sha256", "card_corpus_sha256",
                "player_deck_sha256", "pilot_version", "opponent_panel_sha256",
                "oracle_bulk_sha256", "simulation_protocol_sha256"
            )})
            rows.append(row)
            run = {
                "seed": seed, "completed_rounds": 1,
                "opening_hand": None, "opening_hands_by_seat": None,
                "ui_observations": [], "life_history": [],
                "gorge_source": {"chain": row["chain"], "visibility": "public_events_only",
                                 "synthetic_simulation_only": False},
                "outcome": {"complete": True, "status": "win" if seed % 2 == 0 else "loss",
                            "winner_seat": seed % 2}
            }
            if leak and seed == 0:
                run["native_events"] = [{"secret": True}]
            games.append({"game_id": gid, "source_sha256": row["source_sha256"],
                          "chain": row["chain"], "run": run})
        pq.write_table(pa.Table.from_pylist(rows), self.shard / "games.parquet")
        raw = (self.shard / "games.parquet").read_bytes()
        manifest = {
            "schema": "gorge-warehouse-shard-v1",
            "batch_id": "123456-1", "player_deck": deck, "shard": 0,
            "files": {"games.parquet": {"bytes": len(raw), "rows": count,
                                      "sha256": hashlib.sha256(raw).hexdigest()}}
        }
        (self.shard / "manifest.json").write_text(json.dumps(manifest))
        if not omit_projection:
            projection = {
                "schema": "gorge-r2-original-ui-projection-v1",
                "source_batch": "123456-1", "deck": deck, "shard": 0,
                "ui_deck_sha256": "a"*64,
                "source_deck_sha256": c["player_deck_sha256"],
                "games": games
            }
            (self.shard / "ui-original.v1.json").write_text(json.dumps(projection))

    def test_complete_statistics_and_25_game_replay_pagination(self):
        self.build(26)
        report = project(self.root / "source", self.registry, self.root / "built",
                         expected_batches=["123456-1"])
        self.assertEqual(report["decks"]["mortarion_current"], 26)
        version = report["version"]
        prefix = self.root / "built" / "versions" / version / "mortarion_current"
        summary = json.loads((prefix / "summary.json").read_text())
        self.assertEqual((summary["n"], summary["wins"], summary["losses"]), (26, 13, 13))
        first = json.loads((prefix / "pages" / "000000.json").read_text())
        second = json.loads((prefix / "pages" / "000001.json").read_text())
        self.assertEqual((len(first["games"]), len(second["games"])), (25, 1))
        self.assertNotIn("batch", first)
        self.assertEqual(len(list((prefix / "games").glob("*.json"))), 26)
        pointer = json.loads((self.root / "built" / "current.json").read_text())
        raw = (self.root / "built" / "versions" / version / "manifest.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), pointer["manifest_sha256"])

    def test_versioned_insights_require_exact_full_cohort_native_evidence(self):
        self.build(2)
        source = self.root / "source"
        before = project(source, self.registry, self.root / "before")
        old_version = before["version"]
        rows = pq.read_table(self.shard / "games.parquet").to_pylist()
        categories = {kind: [] for kind in KINDS}
        categories["played"] = [{
            "name": "Sol Ring",
            "counts": [[row["seed"], 1] for row in rows],
            "seen": [row["seed"] for row in rows],
            "durations": [],
            "timesPlayed": 2,
            "events": [[row["seed"], 2] for row in rows]
        }]
        def digest_file(name):
            return hashlib.sha256((self.shard / name).read_bytes()).hexdigest()
        evidence = {
            "schema": "gorge-r2-card-feature-evidence-v1",
            "manifest_sha256": digest_file("manifest.json"),
            "games_sha256": digest_file("games.parquet"),
            "ui_sha256": digest_file("ui-original.v1.json"),
            "source_recordings": {row["game_id"]: row["source_sha256"] for row in rows},
            "features": {
                "schema": "gorge-card-insights-shard-v1",
                "deck": "mortarion_current",
                "deck_sha256": "a" * 64,
                "completed_verified_games": 2,
                "seed_chains": [[row["seed"], row["chain"]] for row in rows],
                "confirmed_tutors": 0,
                "categories": categories
            }
        }
        (self.shard / "card-insights.v1.json").write_text(json.dumps(evidence))
        after = project(source, self.registry, self.root / "after")
        self.assertNotEqual(after["version"], old_version)
        root = self.root / "after" / "versions" / after["version"]
        summary = json.loads((root / "mortarion_current/summary.json").read_text())
        self.assertEqual(summary["card_insights"]["status"], "complete")
        insights = json.loads((root / "mortarion_current/insights.json").read_text())
        self.assertEqual(insights["verified_games"], 2)
        self.assertEqual(insights["categories"]["played"][0]["games"], 2)
        self.assertEqual(insights["cohort_version"], after["version"])
        manifest = json.loads((root / "manifest.json").read_text())
        expected = manifest["decks"]["mortarion_current"]["insights"]["sha256"]
        self.assertEqual(expected,
                         hashlib.sha256((root / "mortarion_current/insights.json").read_bytes()).hexdigest())

    def test_501_games_have_21_lightweight_pages_and_individual_replay_objects(self):
        self.build(501)
        report = project(self.root / "source", self.registry, self.root / "built",
                         expected_batches=["123456-1"])
        prefix = self.root / "built" / "versions" / report["version"] / "mortarion_current"
        manifest = json.loads((prefix.parent / "manifest.json").read_text())
        self.assertEqual(manifest["decks"]["mortarion_current"]["n"], 501)
        self.assertEqual(len(manifest["decks"]["mortarion_current"]["pages"]), 21)
        self.assertEqual(len(json.loads((prefix / "pages" / "000020.json").read_text())["games"]), 1)
        self.assertEqual(len(list((prefix / "games").glob("*.json"))), 501)
        summary = json.loads((prefix / "summary.json").read_text())
        self.assertEqual(summary["wins"] + summary["losses"], 501)
        self.assertEqual(sum(x["games"] for x in summary["game_turn_histogram"]), 501)

    def test_reject_missing_source_and_projection(self):
        self.build(1, omit_projection=True)
        with self.assertRaisesRegex(ValueError, "Missing approved shard replay"):
            project(self.root / "source", self.registry, self.root / "built")
        with self.assertRaisesRegex(ValueError, "Missing source batch"):
            project(self.root / "source", self.registry, self.root / "built",
                    expected_batches=["123456-1", "123457-1"])

    def test_reject_private_projection_payload(self):
        self.build(1, leak=True)
        with self.assertRaisesRegex(ValueError, "Invalid original UI run|Private source value"):
            project(self.root / "source", self.registry, self.root / "built")


if __name__ == "__main__":
    unittest.main()
