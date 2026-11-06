"""Source-backed fixture checks for materialized summary and lazy replay pages."""
import hashlib
import json
import tempfile
import unittest
import shutil
from pathlib import Path

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    pa = pq = None

from tools.gorge_cohort_eligibility import fingerprint
from tools.gorge_r2_materialized_results import project
from tools.gorge_card_insights import KINDS
from tools.gorge_r2_materialized_rollback import verified_target, guarded_rollback
from tools.gorge_r2_source_inventory import validate_inventory


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
                "game_id": gid, "batch_id": "123456-1", "deck": deck, "shard": 0,
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
        # Complete native events are indexed by the warehouse game source.
        events = []
        for i, row in enumerate(rows):
            row["event_start_row"] = len(events)
            row["native_event_count"] = 2
            for seq, secret in ((0, True), (1, False)):
                event = {"seq": seq, "kind": 3 if secret else 19,
                         "secret": secret, "obj": i + 1}
                events.append({
                    "game_id": row["game_id"], "chain": row["chain"],
                    "seed": row["seed"], "seq": seq,
                    "kind_id": event["kind"], "secret": secret,
                    "event_json": json.dumps(event)
                })
        pq.write_table(pa.Table.from_pylist(rows), self.shard / "games.parquet")
        pq.write_table(pa.Table.from_pylist(events), self.shard / "events.parquet")
        raw = (self.shard / "games.parquet").read_bytes()
        event_raw = (self.shard / "events.parquet").read_bytes()
        manifest = {
            "schema": "gorge-warehouse-shard-v1",
            "batch_id": "123456-1", "player_deck": deck, "shard": 0, "games": count,
            "native_events": len(events),
            "files": {"games.parquet": {"bytes": len(raw), "rows": count,
                                      "sha256": hashlib.sha256(raw).hexdigest()},
                      "events.parquet": {"bytes": len(event_raw), "rows": len(events),
                                      "sha256": hashlib.sha256(event_raw).hexdigest()}}
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
        first_game = json.loads(next((prefix / "games").glob("*.json")).read_text())
        self.assertEqual(first_game["native_event_count"], 2)
        native_part = json.loads((prefix / first_game["event_parts"][0]["path"]).read_text())
        self.assertEqual(len(native_part["events"]), 2)
        self.assertTrue(native_part["events"][0]["secret"],
                        "Omniscient native draws must not be filtered")
        self.assertEqual(native_part["events"][1]["kind"], 19)
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


    def test_expected_inventory_rejects_missing_entire_shard(self):
        self.build(1)
        inventory = [
            {"batch": "123456-1", "deck": "mortarion_current", "shard": "0"},
            {"batch": "123456-1", "deck": "mortarion_current", "shard": "1"},
        ]
        with self.assertRaisesRegex(ValueError, "Incomplete shard inventory"):
            project(self.root / "source", self.registry, self.root / "built",
                    expected_shards=inventory)

    def test_manifest_game_count_cannot_hide_partial_upload(self):
        self.build(2)
        manifest_path = self.shard / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["games"] = 3
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "Incomplete shard manifest"):
            project(self.root / "source", self.registry, self.root / "built")

    def test_projection_must_cover_exact_approved_game_ids(self):
        self.build(2)
        path = self.shard / "ui-original.v1.json"
        projection = json.loads(path.read_text())
        projection["games"][1] = dict(projection["games"][0])
        path.write_text(json.dumps(projection))
        with self.assertRaisesRegex(ValueError, "Duplicate projected game ID"):
            project(self.root / "source", self.registry, self.root / "built")

    def test_mismatched_shard_parquet_identity_rejected(self):
        self.build(1)
        rows = pq.read_table(self.shard / "games.parquet").to_pylist()
        rows[0]["shard"] = 99
        pq.write_table(pa.Table.from_pylist(rows), self.shard / "games.parquet")
        raw = (self.shard / "games.parquet").read_bytes()
        manifest_path = self.shard / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["files"]["games.parquet"]["bytes"] = len(raw)
        manifest["files"]["games.parquet"]["sha256"] = hashlib.sha256(raw).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "different shard"):
            project(self.root / "source", self.registry, self.root / "built")


    def test_rollback_requires_all_verified_replay_objects(self):
        self.build(26)
        report = project(self.root / "source", self.registry, self.root / "built",
                         expected_batches=["123456-1"])
        version = report["version"]
        built = self.root / "built"
        pointer = verified_target(built, self.registry, version)
        self.assertEqual(pointer, json.loads((built / "current.json").read_text()))
        fake_current = {"schema": "gorge-r2-results-current-v1",
                        "version": "f" * 64, "manifest_sha256": "d" * 64}
        self.assertEqual(guarded_rollback(fake_current, "f" * 64, pointer),
                         pointer)
        with self.assertRaisesRegex(ValueError, "Current pointer changed"):
            guarded_rollback(fake_current, "e" * 64, pointer)
        with self.assertRaisesRegex(ValueError, "already active"):
            guarded_rollback(pointer, version, pointer)
        game = next((built / "versions" / version / "mortarion_current" /
                     "games").glob("*.json"))
        game.unlink()
        with self.assertRaises(FileNotFoundError):
            verified_target(built, self.registry, version)

    def test_rollback_rejects_corrupt_page_and_outdated_registry(self):
        self.build(1)
        report = project(self.root / "source", self.registry, self.root / "built")
        version = report["version"]
        page = self.root / "built" / "versions" / version / "mortarion_current" / "pages" / "000000.json"
        page.write_text('{"altered":true}')
        with self.assertRaisesRegex(ValueError, "Digest mismatch"):
            verified_target(self.root / "built", self.registry, version)
        # Restore the page by rebuilding, then prove eligibility is rechecked.
        project(self.root / "source", self.registry, self.root / "built")
        obsolete = self.root / "obsolete-registry.json"
        obsolete.write_text(self.registry.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "no longer current"):
            verified_target(self.root / "built", obsolete, version)


    def test_reviewed_inventory_requires_every_batch_and_approved_deck(self):
        registry = json.loads(self.registry.read_text())
        approved = json.loads(Path("data/gorge_r2_source_inventory_v1.json").read_text())
        expected = validate_inventory(approved, registry, ["42143344243-1"])
        self.assertEqual(len(expected), 2)
        self.assertEqual({x["deck"] for x in expected},
                         {"magnus_premium", "mortarion_current"})
        with self.assertRaisesRegex(ValueError, "Requested batches differ"):
            validate_inventory(approved, registry, ["42143344243-1", "99999-1"])
        bad = json.loads(json.dumps(approved))
        bad["batches"][0]["shards"].append(
            {"deck": "unapproved_deck", "shard": 9, "games": 1})
        with self.assertRaisesRegex(ValueError, "lacks approved current cohort"):
            validate_inventory(bad, registry, ["42143344243-1"])

    def test_attested_game_count_rejects_partial_shard_even_when_rehashed(self):
        self.build(2)
        with self.assertRaisesRegex(ValueError, "Incomplete attested shard game count"):
            project(self.root / "source", self.registry, self.root / "built",
                    expected_shards=[{"batch":"123456-1",
                                      "deck":"mortarion_current", "shard":"0",
                                      "games":3}])

    def test_isolated_staging_publish_interrupt_and_rollback_rehearsal(self):
        # Local object-store rehearsal uses the same immutable version/pointer
        # contract as R2, but never connects to or mutates production R2.
        self.build(26)
        a = self.root / "build-old"
        old_version = project(self.root / "source", self.registry, a)["version"]
        self.build(27)
        b = self.root / "build-new"
        new_version = project(self.root / "source", self.registry, b)["version"]
        self.assertNotEqual(old_version, new_version)
        store = self.root / "staging-object-store"
        shutil.copytree(a / "versions", store / "versions")
        shutil.copy2(a / "current.json", store / "current.json")
        before = (store / "current.json").read_bytes()
        # A failed/partial upload cannot activate an unpublished manifest.
        (store / "versions" / new_version).mkdir(parents=True)
        self.assertEqual((store / "current.json").read_bytes(), before)
        with self.assertRaises(FileNotFoundError):
            verified_target(store, self.registry, new_version)
        shutil.copytree(b / "versions" / new_version,
                        store / "versions" / new_version, dirs_exist_ok=True)
        target = verified_target(store, self.registry, new_version)
        (store / "current.json").write_text(json.dumps(target) + "\n")
        self.assertEqual(json.loads((store / "current.json").read_text())["version"],
                         new_version)
        rollback = verified_target(store, self.registry, old_version)
        activated = guarded_rollback(
            json.loads((store / "current.json").read_text()), new_version, rollback)
        (store / "current.json").write_text(json.dumps(activated) + "\n")
        self.assertEqual(json.loads((store / "current.json").read_text())["version"],
                         old_version)
        # The forward version is still immutable and recoverable.
        self.assertEqual(verified_target(store, self.registry, new_version),
                         target)

    def test_reject_private_projection_payload(self):
        self.build(1, leak=True)
        with self.assertRaisesRegex(ValueError, "Invalid original UI run|Private source value"):
            project(self.root / "source", self.registry, self.root / "built")


if __name__ == "__main__":
    unittest.main()
