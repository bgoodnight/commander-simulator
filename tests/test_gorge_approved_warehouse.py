"""Safe warehouse projection must never join archived game actions."""
import unittest
from tools.gorge_approved_warehouse import partition_warehouse
from tools.gorge_cohort_eligibility import SCHEMA, IDENTITY_FIELDS, fingerprint


class WarehouseIsolationTests(unittest.TestCase):
    def test_archive_and_experiment_actions_are_excluded(self):
        cohort = {"cohort_id": "fixed-2026", "status": "current",
                  "approved": True, "approval_ref": "reviewed-001"}
        cohort.update({k: "v1-" + k for k in IDENTITY_FIELDS})
        registry = {"schema": SCHEMA, "cohorts": [
            cohort,
            {"cohort_id": "old-mortarion", "status": "archived", "approved": False},
            {"cohort_id": "precon-test", "status": "experimental", "approved": False},
        ]}
        def game(gid, cid):
            row = {"game_id": gid, "cohort_id": cid,
                   "cohort_manifest_sha256": fingerprint(cohort),
                   "source_sha256": "a" * 64, "finished": True,
                   "replay_verified": True, "error": None}
            row.update({k: cohort[k] for k in IDENTITY_FIELDS})
            return row
        games = [game("old/1", "old-mortarion"),
                 game("test/1", "precon-test"),
                 game("now/1", "fixed-2026"),
                 game("unknown/1", "missing")]
        events = [{"game_id": r["game_id"], "seq": 0} for r in games]
        accepted, selected_events, excluded = partition_warehouse(games, events, registry)
        self.assertEqual([r["game_id"] for r in accepted], ["now/1"])
        self.assertEqual([r["game_id"] for r in selected_events], ["now/1"])
        self.assertEqual(len(excluded), 3)

    def test_blank_registry_returns_no_games_or_events(self):
        games = [{"game_id": "old/1", "finished": True, "replay_verified": True}]
        accepted, events, excluded = partition_warehouse(
            games, [{"game_id": "old/1"}], {"schema": SCHEMA, "cohorts": []})
        self.assertEqual(accepted, [])
        self.assertEqual(events, [])
        self.assertEqual(len(excluded), 1)


if __name__ == "__main__":
    unittest.main()
