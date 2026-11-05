"""Candidate staging is isolated from runtime opponent registration."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.stage_commander_precon_candidates import normalize, build_catalog, generate


def source_row(name, set_code, *, type="Commander Deck", card_count=99, partner=False):
    commanders = [{"name":"Commander A","count":1}]
    if partner:
        commanders.append({"name":"Commander B","count":1})
        card_count -= 1
    return {
        "name":name, "type":type, "set_code":set_code,
        "release_date":"2025-01-01",
        "commander":commanders,
        "cards":[{"name":"Forest","count":card_count}],
        "sideboard":[],
    }


class StagePreconCandidatesTests(unittest.TestCase):
    def test_regular_and_partner_commander(self):
        self.assertIsNotNone(normalize(source_row("A","C1")))
        self.assertIsNotNone(normalize(source_row("B","C2",partner=True)))
        self.assertEqual(len(normalize(source_row("B","C2",partner=True))["deck"]["commanders"]),2)

    def test_reject_invalid_and_noncommander(self):
        self.assertIsNone(normalize(source_row("A","C1",type="Theme Deck")))
        self.assertIsNone(normalize(source_row("A","C1",card_count=98)))
        self.assertIsNone(normalize(source_row("A","C1",type="Brawl Deck")))

    def test_build_at_least_100_and_write_candidate_only(self):
        rows=[source_row("Stock "+str(i),"S"+str(i)) for i in range(112)]
        with tempfile.TemporaryDirectory() as tmp:
            result = generate(json.dumps(rows).encode(), Path(tmp),limit=105)
            self.assertEqual(result["count"],105)
            self.assertEqual(len(list(Path(tmp).glob("*.json"))),106)
            self.assertTrue(all(c["opponent_status"]=="candidate_not_enabled" for c in result["candidates"]))
            self.assertTrue(all(c["rules_status"]=="not_tested" for c in result["candidates"]))

    def test_fail_if_insufficient(self):
        with self.assertRaisesRegex(ValueError,"at least 100"):
            build_catalog([source_row("A","C1")])


if __name__=="__main__":
    unittest.main()
