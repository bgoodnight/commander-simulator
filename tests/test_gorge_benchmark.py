"""Offline contract tests for optional gorge research; no dependency on Go."""
import json
import tempfile
import unittest
from pathlib import Path

from commander_sim.deck_fixtures import FIXTURES
from tools.export_gorge_decks import export_all, export_deck
from tools.gorge_benchmark import summarize, collect


class GorgeProbeTests(unittest.TestCase):
    def test_pinned_four_deck_exports_have_correct_commander_and_hundred_cards(self):
        for f in FIXTURES:
            with self.subTest(fixture=f.key):
                data=export_deck(f)
                self.assertEqual(data["format"],"commander")
                self.assertEqual(data["commander"],f.commander)
                self.assertEqual(data["cards"][0],
                    {"name":f.commander,"count":1})
                self.assertEqual(sum(x["count"] for x in data["cards"]),100)
                self.assertEqual(len({x["name"] for x in data["cards"]}),
                                 len(data["cards"]))

    def test_export_stays_within_named_fixture_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            created=export_all(folder,["mortarion_current","necron_dynasties"])
            self.assertEqual(set(created),
                             {"mortarion_current","necron_dynasties"})
            self.assertTrue(all(Path(p).is_file() for p in created.values()))
            with self.assertRaises(ValueError):
                export_all(folder,["not-a-deck"])

    def test_summary_classifies_stalled_games_separately(self):
        rows=[
            {"seed":1,"decks":["mortarion_current","magnus_premium"],
             "finished":True,"winner_seat":1,"turns":20,"intents":300,
             "events":1000,"elapsed_seconds":2,"replay_verified":True},
            {"seed":2,"decks":["necron_dynasties","wretched_ranks"],
             "finished":False,"stall_reason":"turns","turns":35,
             "events":2000,"elapsed_seconds":3},
            {"seed":3,"finished":False,"error":"bad deck",
             "elapsed_seconds":1},
        ]
        report=summarize(rows,"gorge")
        self.assertEqual(report["completed"],1)
        self.assertEqual(report["failed"],1)
        self.assertEqual(report["stalled_or_horizon_reached"],1)
        self.assertEqual(report["winners"],{"magnus_premium":1})
        self.assertEqual(report["replay_verified"],1)
        self.assertEqual(report["games_per_minute"],30.0)

    def test_collection_retains_non_comparability_and_raw_results(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            gorge={"seed":100,"decks":["mortarion_current"],
                   "finished":False,"elapsed_seconds":1.2}
            base={"seed":100,"deck":"mortarion_current",
                  "finished":False,"elapsed_seconds":2.5}
            (p/"gorge.jsonl").write_text(json.dumps(gorge)+"\n")
            (p/"base.json").write_text(json.dumps([base]))
            data=collect(p/"gorge.jsonl",p/"base.json",p/"report.json")
            self.assertEqual(data["schema"],"commander-backend-comparison-v1")
            self.assertEqual(len(data["gorge_samples"]),1)
            self.assertIn("NOT an apples-to-apples",data["comparable_metrics"])
            self.assertTrue((p/"report.json").is_file())


if __name__=="__main__":
    unittest.main()
