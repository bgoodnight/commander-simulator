"""Verify corrected-pilot R2 experimental archive without AWS credentials."""
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.gorge_r2_experiment_ingest import acquire


def fixture_archive(path: Path, *, native_ok=True):
    run={"seed":187000,"decks":["mortarion_current","a","b","c"],
         "hero_seat":0,"finished":True,"replay_verified":True,
         "replay_chain":"chain","winner_seat":0}
    trace={"schema":"gorge-native-trace-v1","seed":187000,
           "chain":"chain","decks":run["decks"],"hero_seat":0,
           "log":{"events":[],"intents":[]},"objects":[],
           "snapshots":[]}
    m={"schema":"gorge-fresh-corrected-pilot-source-v1",
       "source_run_id":"42143344243","run_attempt":"1",
       "hero_deck":"mortarion_current","approval":False,"attempts_expected":1}
    summary={"attempted":1,"completed":1,"replay_verified":1,
             "status":"experimental_unqualified"}
    files={
      "results/runs.jsonl":json.dumps(run)+"\n",
      "results/source-manifest.json":json.dumps(m),
      "results/qualification-summary.json":json.dumps(summary)}
    if native_ok:files["results/native/gorge-seed-187000.json"]=json.dumps(trace)
    with tarfile.open(path,"w:gz") as tar:
        for name,data in files.items():
            raw=data.encode()
            ti=tarfile.TarInfo(name)
            ti.size=len(raw)
            tar.addfile(ti,io.BytesIO(raw))


class ExperimentalR2Tests(unittest.TestCase):
    def test_source_matches_native(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            src=root/"fixture.tar.gz"
            fixture_archive(src)
            def fake_aws(args,endpoint):
                self.assertTrue(any("native/experimental/corrected-pilot/v1/42143344243-1/mortarion_current.tar.gz" in a for a in args))
                Path(args[-2]).write_bytes(src.read_bytes())
            with patch("tools.gorge_r2_experiment_ingest._aws",side_effect=fake_aws):
                d=acquire("42143344243-1","mortarion_current","a"*32,root/"out")
            self.assertEqual(d["native_available"],1)
            self.assertEqual(d["completed"],1)
            self.assertFalse(d["production_eligible"])

    def test_missing_native_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            src=root/"fixture.tar.gz"
            fixture_archive(src,native_ok=False)
            def fake_aws(args,endpoint):
                Path(args[-2]).write_bytes(src.read_bytes())
            with patch("tools.gorge_r2_experiment_ingest._aws",side_effect=fake_aws):
                d=acquire("42143344243-1","mortarion_current","a"*32,root/"out")
            self.assertEqual(d["native_missing_seeds"],[187000])

    def test_rejects_unexpected_keys(self):
        with self.assertRaisesRegex(ValueError,"Run attempt"):
            acquire("../../secrets","mortarion_current","a"*32,Path("/tmp/unused"))
        with self.assertRaisesRegex(ValueError,"Unrecognized"):
            acquire("42143344243-1","unauthorized","a"*32,Path("/tmp/unused"))


if __name__=="__main__":
    unittest.main()
