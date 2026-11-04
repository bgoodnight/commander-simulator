"""The publisher merges independent Gorge batches without losing earlier games."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.merge_gorge_results_catalog import merge_publication


class CatalogMergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.destination = self.root / "published"

    def tearDown(self):
        self.tmp.cleanup()

    def bundle(self, seed, chain):
        source = self.root / ("batch-" + str(seed) + chain)
        source.mkdir()
        decks = ["mortarion_current","necron_dynasties",
                 "wretched_ranks","science-pip"]
        name = f"gorge-seed-{seed}.ui.json"
        replay = {"schema":"gorge-ui-replay-v1",
                  "engine":"gorge","seed":seed,"chain":chain,
                  "decks":decks,"visibility":"omniscient",
                  "synthetic_simulation_only":True,
                  "snapshots":[{"boundary":"first_pending_decision_of_turn",
                                "players":[]}]}
        (source/name).write_text(json.dumps(replay))
        (source/"manifest.json").write_text(json.dumps({
            "schema":"gorge-omniscient-replay-manifest-v1",
            "visibility":"omniscient","synthetic_simulation_only":True,
            "analytics_file":"analytics.json",
            "games":[{"file":name,"seed":seed,"decks":decks,"chain":chain}]}))
        (source/"analytics.json").write_text(json.dumps({
            "schema":"gorge-batch-analytics-v1",
            "games":[{"seed":seed,"chain":chain,
                      "decks":decks,"replay_verified":True}]}))
        return source

    def test_batches_merge_without_dropping_old_replays(self):
        a = self.bundle(400,"first")
        b = self.bundle(600,"second")
        self.assertEqual(merge_publication(a,self.destination)["replays"],1)
        self.assertEqual(merge_publication(b,self.destination)["replays"],2)
        manifest=json.loads((self.destination/"manifest.json").read_text())
        analytics=json.loads((self.destination/"analytics.json").read_text())
        self.assertEqual([r["seed"] for r in manifest["games"]],[400,600])
        self.assertEqual([r["seed"] for r in analytics["games"]],[400,600])
        self.assertTrue((self.destination/"gorge-seed-400.ui.json").is_file())

    def test_conflicting_same_seed_fails(self):
        merge_publication(self.bundle(400,"first"),self.destination)
        with self.assertRaisesRegex(ValueError,"different source game"):
            merge_publication(self.bundle(400,"other"),self.destination)


if __name__ == "__main__":
    unittest.main()
