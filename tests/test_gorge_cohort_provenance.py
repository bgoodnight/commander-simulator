"""Pinned cohort stamping requires verified, matching Gorge native source."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.gorge_cohort_provenance import stamp
from tools.gorge_cohort_eligibility import IDENTITY_FIELDS, fingerprint


class ProvenanceStampTests(unittest.TestCase):
    def test_verified_native_game_gets_exact_cohort_fingerprint(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            native={"schema":"gorge-native-trace-v1","seed":123,
                    "chain":"replay-123","decks":["hero","a","b","c"]}
            raw=json.dumps(native).encode()
            (root/"gorge-seed-123.json").write_bytes(raw)
            cohort={"cohort_id":"experimental-post-fix","status":"experimental"}
            cohort.update({k:"pinned-"+k for k in IDENTITY_FIELDS})
            row={"seed":123,"decks":["hero","a","b","c"],"hero_seat":0,
                 "finished":True,"replay_verified":True,"error":None,
                 "replay_chain":"replay-123","draw":False,"winner_seat":0}
            result=stamp([row],root,cohort)
            self.assertEqual(result[0]["source_sha256"],hashlib.sha256(raw).hexdigest())
            self.assertEqual(result[0]["cohort_manifest_sha256"],fingerprint(cohort))
            self.assertEqual(result[0]["cohort_id"],"experimental-post-fix")
            with self.assertRaisesRegex(ValueError,"restamping"):
                stamp(result,root,cohort)
            with self.assertRaisesRegex(ValueError,"Native log"):
                stamp([{**row,"replay_chain":"wrong"}],root,cohort)
            with self.assertRaisesRegex(ValueError,"Unverified"):
                stamp([{**row,"replay_verified":False}],root,cohort)


if __name__=="__main__":
    unittest.main()
