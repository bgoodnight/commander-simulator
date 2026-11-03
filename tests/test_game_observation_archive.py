"""Complete observation archives are validated before upload or release."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.validate_game_observations import validate


def record(seed, rounds=2):
    return {"format":"commander-game-observations-v1", "schema_version":1,
            "deck_key":"necron_dynasties","deck_sha256":"a"*64,
            "scenario":"balanced","pilot_style":"adaptive",
            "provisional_mode":"safe","seed":seed,
            "requested_rounds":6,"completed_rounds":rounds,
            "mulligan":{"opening_hand":["Swamp"]*7},
            "outcome":{"completed_rounds":rounds,"status":"loss"},
            "turn_records":[{"turn":i} for i in range(1,rounds+1)],
            "state_snapshots":[{"turn":i} for i in range(1,rounds+1)],
            "life_history":[{"round":i} for i in range(rounds+1)]}


class ObservationValidationTests(unittest.TestCase):
    def test_complete_cohort_passes_and_early_terminal_is_accepted(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"balanced.jsonl"
            p.write_text("".join(json.dumps(record(i))+"\\n" for i in range(3)))
            result=validate([p],expected_games=3,expected_rounds=6)
            self.assertEqual(result,{"files":1,"games":3,"cohorts":1})

    def test_missing_hand_or_corrupt_turn_does_not_pass(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"balanced.jsonl"
            row=record(1)
            del row["mulligan"]["opening_hand"]
            p.write_text(json.dumps(row)+"\\n")
            with self.assertRaisesRegex(ValueError,"Invalid or incomplete"):
                validate([p],expected_games=1,expected_rounds=6)
            row=record(1)
            row["state_snapshots"][1]["turn"]=7
            p.write_text(json.dumps(row)+"\\n")
            with self.assertRaisesRegex(ValueError,"Invalid or incomplete"):
                validate([p],expected_games=1,expected_rounds=6)


if __name__=="__main__":
    unittest.main()
