"""Source integrity and cohort-promotion protections for R2 projection."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.gorge_r2_projection_batch import project
from tools.gorge_cohort_eligibility import SCHEMA, IDENTITY_FIELDS


class R2ApprovedBatchTests(unittest.TestCase):
    def test_no_approved_cohort_means_zero_r2_publication(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            registry=p/"registry.json"
            registry.write_text(json.dumps({"schema":SCHEMA,"cohorts":[]}))
            with self.assertRaisesRegex(ValueError,"No approved"):
                project(p/"source",registry,p/"approved","123-1")
            self.assertFalse((p/"approved/publication.json").exists())

    def test_bad_batch_identifier_rejected(self):
        with self.assertRaisesRegex(ValueError,"Invalid batch"):
            project(Path("/tmp"),Path("/tmp"),Path("/tmp"),"../../unsafe")

    def test_corrupt_parquet_refuses_publication(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); folder=p/"source/mortarion_current/0"
            folder.mkdir(parents=True)
            cohort={"cohort_id":"reviewed","status":"current","approved":True,
                    "approval_ref":"signoff-1"}
            cohort.update({k:"pinned-"+k for k in IDENTITY_FIELDS})
            reg=p/"registry.json"
            reg.write_text(json.dumps({"schema":SCHEMA,"cohorts":[cohort]}))
            (folder/"games.parquet").write_bytes(b"CORRUPTED")
            (folder/"events.parquet").write_bytes(b"events")
            data={"schema":"gorge-warehouse-shard-v1","batch_id":"123-1",
                  "player_deck":"mortarion_current","shard":0,"files":{}}
            for name in ("games.parquet","events.parquet"):
                raw=(folder/name).read_bytes()
                data["files"][name]={"sha256":hashlib.sha256(raw).hexdigest(),
                                     "bytes":len(raw)}
            data["files"]["games.parquet"]["sha256"]="0"*64
            (folder/"manifest.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"digest mismatch"):
                project(p/"source",reg,p/"approved","123-1")
            self.assertFalse((p/"approved/publication.json").exists())


if __name__ == "__main__":
    unittest.main()
