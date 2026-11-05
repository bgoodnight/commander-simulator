import json
import tempfile
import unittest
from pathlib import Path

from tools.gorge_candidate_coverage import era, jaccard, make_report


class CandidateCoverageTests(unittest.TestCase):
    def test_era_and_jaccard(self):
        self.assertEqual(era("2014"),"2011-2017")
        self.assertEqual(era("2023"),"2022-2024")
        self.assertEqual(jaccard({"A","B"},{"B","C"}),1/3)

    def test_full_catalog_read_only_and_future_exclusion(self):
        report=make_report(shortlist=24)
        self.assertGreaterEqual(report["released_count"],100)
        self.assertEqual(report["source_catalog_count"],report["released_count"]+report["future_count"])
        self.assertEqual(len(report["released_profiles"]),report["released_count"])
        self.assertEqual(len(report["provisional_shortlist"]),24)
        self.assertEqual(len({x["key"] for x in report["provisional_shortlist"]}),24)
        self.assertEqual(sum(report["provisional_shortlist_release_eras"].values()),24)
        self.assertEqual(report["feature_completeness"]["verified_color_identity"],0)
        self.assertEqual(report["feature_completeness"]["Gorge_qualified"],0)
        self.assertTrue(all(x["release_date"] <= report["as_of"] for x in report["released_profiles"]))
        self.assertTrue(all(x["release_date"] > report["as_of"] for x in report["future_decks"]))
        self.assertTrue(all(x["qualification"]=="not_evaluated" for x in report["released_profiles"]))

    def test_empty_cutoff_rejected(self):
        with self.assertRaisesRegex(ValueError,"No released"):
            make_report(as_of="2000-01-01",shortlist=4)


if __name__=="__main__":unittest.main()
