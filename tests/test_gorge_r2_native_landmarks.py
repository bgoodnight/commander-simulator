"""Native Gorge landmark and R2 acquisition integrity contracts."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.gorge_landmark_features import features,extract_root
from tools.gorge_r2_native_ingest import verify_shards,safely_extract_native
import hashlib
import tarfile


def specimen():
    return {"schema":"gorge-native-trace-v1","seed":9,"chain":"abc",
      "decks":["mortarion_current","a","b","c"],
      "objects":[{"object_id":1,"card_name":"Swamp","is_token":False},
                 {"object_id":2,"card_name":"Sol Ring","is_token":False},
                 {"object_id":3,"card_name":"Astartes Warrior Token","is_token":True}],
      "snapshots":[{"turn":4,"after_event_seq":22,"boundary":"first_pending_decision_of_turn",
                    "players":[{"life":36,"lost":False,"zones":{
                      "hand":[2],"battlefield":[1,3],"graveyard":[]}},
                               {"zones":{}},{"zones":{}},{"zones":{}}]},
                   {"turn":8,"after_event_seq":80,"boundary":"first_pending_decision_of_turn",
                    "players":[{"life":21,"lost":False,"zones":{
                      "hand":[],"battlefield":[1],"graveyard":[2,3]}},
                               {"zones":{}},{"zones":{}},{"zones":{}}]}]}


class LandmarkTests(unittest.TestCase):
    def test_exact_landmarks_and_no_forward_fill(self):
        r=features(specimen(),0,(4,6,8))
        self.assertEqual(r[0]["hero_life"],36)
        self.assertEqual(r[0]["hero_tokens_on_battlefield"],1)
        self.assertEqual(r[0]["hero_basic_lands_on_battlefield"],1)
        self.assertEqual(r[0]["source_event_seq"],22)
        self.assertFalse(r[1]["landmark_observed"])
        self.assertIsNone(r[1]["hero_life"])
        self.assertEqual(r[2]["hero_graveyard_count"],2)

    def test_bad_snapshot_fails_closed(self):
        n=specimen()
        n["snapshots"][1]["after_event_seq"]=20
        with self.assertRaisesRegex(ValueError,"Unordered"):
            features(n,0)

    def test_missing_record_is_missing_not_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            record={"seed":9,"hero_seat":0,"decks":["mortarion_current","a","b","c"],
                    "replay_chain":"abc"}
            (root/"runs.jsonl").write_text(json.dumps(record)+"\n")
            r=extract_root(root,"mortarion_current",(4,8))
            self.assertEqual(len(r),2)
            self.assertFalse(r[0]["landmark_observed"])
            self.assertFalse(r[0]["native_available"])
            (root/"native").mkdir()
            (root/"native"/"gorge-seed-9.json").write_text(json.dumps(specimen()))
            rows=extract_root(root,"mortarion_current",(4,8))
            self.assertTrue(all(x["landmark_observed"] for x in rows))

    def test_verified_warehouse_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"mortarion_current"/"0"
            path.mkdir(parents=True)
            files={}
            for name in ("games.parquet","events.parquet"):
                (path/name).write_bytes(name.encode())
                files[name]={"sha256":hashlib.sha256(name.encode()).hexdigest(),
                             "bytes":len(name)}
            (path/"manifest.json").write_text(json.dumps({"schema":"gorge-warehouse-shard-v1",
                "batch_id":"test","player_deck":"mortarion_current","shard":0,
                "games":1,"native_events":12,"files":files}))
            self.assertEqual(verify_shards(Path(td))["shard_count"],1)
            (path/"events.parquet").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"mismatch"):
                verify_shards(Path(td))

    def test_tar_traversal_rejected(self):
        from io import BytesIO
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/"unsafe.tar.gz"
            with tarfile.open(src,"w:gz") as t:
                payload=b"bad"
                info=tarfile.TarInfo("../escape.txt")
                info.size=len(payload)
                t.addfile(info,BytesIO(payload))
            with self.assertRaisesRegex(ValueError,"Unsafe tar"):
                safely_extract_native(src,Path(td)/"dest")


if __name__=="__main__":
    unittest.main()
