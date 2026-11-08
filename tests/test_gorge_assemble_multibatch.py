import unittest
from tools.gorge_assemble_multibatch import assemble_batches


def batch(name, seed=9, cutoff=22):
    return {
        "batch_id":name,"deck":"mortarion_current","shard":0,
        "cohort_id":"candidate-only",
        "games":[{"seed":seed,"deck":"mortarion_current","hero_seat":0,
                  "status":"decisive","won":1}],
        "landmarks":[{"seed":seed,"hero":"mortarion_current",
                      "landmark_global_turn":4,"landmark_observed":True,
                      "native_available":True,"source_event_seq":cutoff,
                      "hero_life":32}],
        "events":[{"seed":seed,"hero":"mortarion_current",
                   "landmark_global_turn":4,"landmark_observed":True,
                   "event_cutoff_seq":cutoff,"pod_cast_events":3}],
    }


class MultiBatchAssemblerTests(unittest.TestCase):
    def test_same_seed_different_batch_kept_separate(self):
        first=batch("42143344243-1",cutoff=22)
        second=batch("42143344244-1",cutoff=45)
        rows=assemble_batches([second,first])
        self.assertEqual(len(rows),2)
        self.assertNotEqual(rows[0]["game_id"],rows[1]["game_id"])
        self.assertEqual({row["source_event_seq"] for row in rows},{22,45})
        self.assertTrue(all(row["model_eligible"] is False for row in rows))

    def test_duplicate_source_rejected(self):
        src=batch("42143344243-1")
        with self.assertRaisesRegex(ValueError,"Duplicate canonical"):
            assemble_batches([src,src])

    def test_missing_landmark_rejected(self):
        src=batch("42143344243-1")
        src["landmarks"]=[]
        with self.assertRaisesRegex(ValueError,"landmarks"):
            assemble_batches([src])

    def test_event_cutoff_conflict_rejected(self):
        src=batch("42143344243-1")
        src["events"][0]["event_cutoff_seq"]=23
        with self.assertRaisesRegex(ValueError,"cutoff"):
            assemble_batches([src])

    def test_incorrect_hero_rejected(self):
        src=batch("42143344243-1")
        src["events"][0]["hero"]="magnus_premium"
        with self.assertRaisesRegex(ValueError,"deck identity"):
            assemble_batches([src])


if __name__=="__main__":unittest.main()
