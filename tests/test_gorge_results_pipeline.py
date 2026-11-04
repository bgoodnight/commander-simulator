"""Gorge results pipeline: fidelity, caching, retention, and analytics."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.gorge_results_pipeline import (
    load_summaries, project_batch, public_replay_is_safe,
)


class GorgeResultsPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.native = self.root / "native"
        self.native.mkdir()
        self.runs = self.root / "runs.jsonl"
        self.output = self.root / "public"
        self.keys = ["mortarion_current", "magnus_premium",
                     "necron_dynasties", "wretched_ranks"]
        self.rows = []
        for seed in (400, 401):
            source = {"schema": "gorge-native-trace-v1", "engine": "gorge",
                      "format": "commander", "seed": seed,
                      "decks": self.keys, "policies": ["bot"] * 4,
                      "chain": f"chain-{seed}",
                      "log": {"events": [{"kind": 11, "seq": 1}], "intents": []}}
            (self.native / f"gorge-seed-{seed}.json").write_text(json.dumps(source))
            self.rows.append({"seed": seed, "decks": self.keys,
                              "policies": ["bot"] * 4,
                              "replay_chain": f"chain-{seed}",
                              "finished": True, "replay_verified": True,
                              "draw": False, "winner_seat": 0,
                              "turns": 36})
        self.runs.write_text("".join(json.dumps(row) + "\n" for row in self.rows))

    def tearDown(self):
        self.tmp.cleanup()

    def projected(self, source, include_hidden=False):
        self.assertTrue(include_hidden)
        return {"schema": "gorge-ui-replay-v1", "engine": "gorge",
                "seed": source["seed"], "chain": source["chain"],
                "decks": source["decks"], "policies": source["policies"],
                "visibility": "omniscient",
                "synthetic_simulation_only": True,
                "snapshots": [{"boundary": "first_pending_decision_of_turn",
                               "players": []}]}

    def run_project(self, **kwargs):
        with (patch("tools.gorge_results_pipeline.validate_trace",
                    return_value={"source_events": 1,
                                  "turn_boundaries": 1,
                                  "snapshot_definition": "first_pending_decision_of_turn"}),
              patch("tools.gorge_results_pipeline.convert",
                    side_effect=self.projected) as convert):
            report = project_batch(native_dir=self.native, summaries=self.runs,
                                   out=self.output, include_hidden=True, **kwargs)
        return report, convert.call_count

    def test_all_summary_rows_but_selective_replay_retention(self):
        report, calls = self.run_project(max_replays=1)
        self.assertEqual(report["summaries"], 2)
        self.assertEqual(report["catalog_games"], 1)
        self.assertEqual(calls, 1)
        catalog = json.loads((self.output / "manifest.json").read_text())
        analytics = json.loads((self.output / "analytics.json").read_text())
        self.assertEqual(catalog["games"][0]["seed"], 400)
        self.assertEqual(len(analytics["games"]), 2)
        self.assertEqual(analytics["games"][0]["winner_seat"], 0)
        self.assertFalse((self.output / "gorge-seed-401.ui.json").exists())
        self.assertNotIn("log", (self.output / "gorge-seed-400.ui.json").read_text())

    def test_existing_replay_cache_does_not_reconvert(self):
        self.run_project(max_replays=2)
        original = self.output
        another = self.root / "second"
        with (patch("tools.gorge_results_pipeline.validate_trace",
                    return_value={"source_events": 1,
                                  "turn_boundaries": 1,
                                  "snapshot_definition": "first_pending_decision_of_turn"}),
              patch("tools.gorge_results_pipeline.convert") as converter):
            report = project_batch(native_dir=self.native, summaries=self.runs,
                                   out=another, existing_dir=original,
                                   include_hidden=True, max_replays=2)
        converter.assert_not_called()
        self.assertEqual(report["catalog_games"], 2)

    def test_invalid_game_and_missing_trace_fail_closed(self):
        self.rows[0]["replay_verified"] = False
        self.runs.write_text("".join(json.dumps(x)+"\n" for x in self.rows))
        with self.assertRaisesRegex(ValueError,"not fully verified"):
            load_summaries(self.runs)
        self.rows[0]["replay_verified"] = True
        self.runs.write_text("".join(json.dumps(x)+"\n" for x in self.rows))
        (self.native/"gorge-seed-401.json").unlink()
        with self.assertRaisesRegex(ValueError,"Missing source traces"):
            project_batch(native_dir=self.native,summaries=self.runs,
                          out=self.output,include_hidden=True)

    def test_native_log_cannot_be_published(self):
        row={"seed":400,"chain":"chain-400","decks":self.keys}
        replay=self.projected({"seed":400,"chain":"chain-400","decks":self.keys,"policies":["bot"]*4},
                              include_hidden=True)
        self.assertTrue(public_replay_is_safe(replay,row))
        replay["objects"]=[]
        self.assertFalse(public_replay_is_safe(replay,row))


if __name__ == "__main__":
    unittest.main()
