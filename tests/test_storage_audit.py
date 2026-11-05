"""The storage report must distinguish duplicate checkouts from Git object size."""
import unittest

from tools.audit_storage import inventory, markdown


class StorageAuditTests(unittest.TestCase):
    def test_mirrored_generated_files_are_counted_without_double_counting_blobs(self):
        rows = [
            ("docs/deck-lab/gorge-data/analytics.json", "sha-a", 100),
            ("web/pages/data/gorge/analytics.json", "sha-a", 100),
            ("docs/deck-lab/simulation-data/releases/r1/game.json", "sha-b", 20),
            ("web/pages/data/simulation-archive/releases/r1/game.json", "sha-b", 20),
            ("simulator/source.py", "sha-c", 50),
        ]
        report = inventory(rows)
        self.assertEqual(report["file_count"], 5)
        self.assertEqual(report["tracked_content_bytes"], 290)
        self.assertEqual(report["unique_blob_content_bytes"], 170)
        self.assertEqual(report["duplicate_worktree_bytes"], 120)
        self.assertEqual(report["historical_simulation_releases"], 1)
        self.assertEqual(sum(x["identical_pairs"] for x in report["known_mirrors"]), 2)
        self.assertIn("not** the GitHub repository", markdown(report))

    def test_unrelated_distinct_files_are_not_flagged(self):
        report = inventory([("main.py", "sha-x", 10), ("index.html", "sha-y", 30)])
        self.assertEqual(report["duplicate_worktree_bytes"], 0)
        self.assertEqual(report["unique_blob_content_bytes"], 40)


if __name__ == "__main__":
    unittest.main()
