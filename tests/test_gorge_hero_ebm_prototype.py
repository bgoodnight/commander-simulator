"""Fixture-level contracts for native Gorge hero dataset and EBM eligibility."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.gorge_hero_ebm_prototype import extract, demo_ebm


class GorgeHeroEBMTests(unittest.TestCase):
    def test_fixture_extract_and_no_outcome_leakage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "native").mkdir()
            runs = []
            for seed, winner in [(100,0),(101,1)]:
                runs.append({"seed":seed, "decks":["mortarion_current","necron_dynasties","wretched_ranks","cavalry-charge"],
                             "hero_seat":0,"finished":True,"replay_verified":True,"draw":False,
                             "winner_seat":winner,"turns":16,"replay_chain":f"chain{seed}"})
                src = {"schema":"gorge-native-trace-v1","seed":seed,
                       "chain":f"chain{seed}","decks":runs[-1]["decks"],
                       "log":{"events":[{"seq":0,"kind":0}],"intents":[{}]},
                       "objects":[{"object_id":1,"card_name":"Sol Ring"},{"object_id":2,"card_name":"Swamp"}],
                       "snapshots":[{"players":[
                           {"life":40,"zones":{"hand":[1,2]}},
                           {"life":40,"zones":{"hand":[]}},
                           {"life":40,"zones":{"hand":[]}},
                           {"life":40,"zones":{"hand":[]}}]}]}
                (root/"native"/f"gorge-seed-{seed}.json").write_text(json.dumps(src))
            (root/"runs.jsonl").write_text("".join(json.dumps(x)+"\n" for x in runs))
            rows,report=extract(root,"mortarion_current")
            self.assertEqual(report["source_games"],2)
            self.assertEqual(report["opening_hand_observed"],2)
            self.assertEqual([r["won"] for r in rows],[1,0])
            self.assertEqual(rows[0]["opening_basic_lands"],1)
            self.assertEqual(rows[0]["opening_sol_ring"],1)
            self.assertNotIn("game_turns", ["hero_seat","opening_basic_lands","opening_sol_ring",
                "opening_arcane_signet","opening_mind_stone"])
            self.assertEqual(demo_ebm(rows)["status"],"not_fit")

    def test_missing_native_is_not_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            run={"seed":100,"decks":["mortarion_current","a","b","c"],
                 "hero_seat":0,"finished":False,"stall_reason":"turns","turns":60}
            (root/"runs.jsonl").write_text(json.dumps(run)+"\n")
            rows,rep=extract(root,"mortarion_current")
            self.assertIsNone(rows[0]["opening_basic_lands"])
            self.assertIsNone(rows[0]["won"])
            self.assertEqual(rows[0]["status"],"turn_cap")
            self.assertEqual(rep["native_recordings"],0)

    def test_reject_duplicate_seed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            run={"seed":100,"decks":["mortarion_current","a","b","c"],"hero_seat":0}
            (root/"runs.jsonl").write_text(json.dumps(run)+"\n"+json.dumps(run)+"\n")
            with self.assertRaisesRegex(ValueError,"duplicated seed"):
                extract(root,"mortarion_current")


if __name__ == "__main__":
    unittest.main()
