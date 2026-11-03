"""Checks that published per-game UI observations are complete, not inferred."""
import json
import tempfile
from pathlib import Path
import unittest

from tools.validate_outcome_ui_coverage import validate


def cohort():
    records=[]
    for seed in (0,1):
        records.append({
            "seed":seed,"completed_rounds":2,
            "opening_hand":["Land"]*7,
            "life_history":[{"round":i} for i in range(3)],
            "ui_observations":[
                {"turn":1,"hand":["Land"],"battlefield":[],"graveyard":[],
                 "land_count":1,"mana_rock_count":0,"creature_count":0,
                 "actions":[{"type":"land_play","card":"Swamp"}]},
                {"turn":2,"hand":[],"battlefield":["Swamp","Grave Titan"],"graveyard":[],
                 "land_count":2,"mana_rock_count":0,"creature_count":1,
                 "actions":[{"type":"creature_cast","card":"Grave Titan"}]}
            ]
        })
    return {"format":"commander-modeled-outcomes-v1","seed_count":2,
            "requested_rounds":2,"runs":records}


class CurrentUiOutputTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir=Path(temp.name)

    def check(self, data):
        (self.dir/"batch.json").write_text(json.dumps(data),encoding="utf-8")
        return validate(self.dir.glob("*.json"),expected_games=2,expected_rounds=2)

    def test_full_observations_pass(self):
        result=self.check(cohort())
        self.assertEqual(result["games"],2)
        self.assertEqual(result["observed_rounds"],4)
        self.assertEqual(result["named_casts"],4)

    def test_missing_turn_evidence_rejected(self):
        data=cohort()
        del data["runs"][0]["ui_observations"]
        with self.assertRaisesRegex(ValueError,"incomplete per-seed"):
            self.check(data)

    def test_missing_mana_or_board_rejected(self):
        data=cohort()
        del data["runs"][0]["ui_observations"][0]["mana_rock_count"]
        with self.assertRaisesRegex(ValueError,"turn/zone/resource"):
            self.check(data)

    def test_unattributed_cast_is_not_a_named_card_insight(self):
        data=cohort()
        for run in data["runs"]:
            for row in run["ui_observations"]:
                for event in row["actions"]:
                    del event["card"]
        with self.assertRaisesRegex(ValueError,"No named card-play"):
            self.check(data)


if __name__=="__main__":
    unittest.main()
