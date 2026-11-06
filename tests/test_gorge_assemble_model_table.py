"""Source-joined Gorge analytic dataset preserves timing and missingness."""
import unittest
from tools.gorge_assemble_model_table import assemble


class AssembleTests(unittest.TestCase):
    def test_join_and_missing_landmark(self):
        game={"seed":9,"deck":"mortarion_current","hero_seat":0,
              "status":"decisive","won":1,"opening_basic_lands":3}
        landmarks=[{"seed":9,"hero":"mortarion_current",
                    "landmark_global_turn":4,"landmark_observed":True,
                    "native_available":True,"source_event_seq":20,
                    "hero_life":35,"hero_hand_count":4},
                   {"seed":9,"hero":"mortarion_current",
                    "landmark_global_turn":8,"landmark_observed":False,
                    "native_available":True}]
        rows=assemble([game],landmarks)
        self.assertEqual(rows[0]["hero_life"],35)
        self.assertEqual(rows[0]["source_event_seq"],20)
        self.assertIsNone(rows[1]["hero_life"])
        self.assertFalse(rows[0]["model_eligible"])

    def test_reject_unknown_seed(self):
        with self.assertRaisesRegex(ValueError,"matching hero"):
            assemble([{"seed":1,"deck":"mortarion_current"}],
                     [{"seed":2,"hero":"mortarion_current","landmark_global_turn":4}])

    def test_reject_phantom_state(self):
        with self.assertRaisesRegex(ValueError,"non-null"):
            assemble([{"seed":1,"deck":"mortarion_current"}],
                     [{"seed":1,"hero":"mortarion_current","landmark_global_turn":4,
                       "landmark_observed":False,"hero_life":40}])

    def test_reject_duplicate_landmark(self):
        with self.assertRaisesRegex(ValueError,"Duplicate game/landmark"):
            assemble([{"seed":1,"deck":"mortarion_current"}],
                     [{"seed":1,"hero":"mortarion_current","landmark_global_turn":4},
                      {"seed":1,"hero":"mortarion_current","landmark_global_turn":4}])


if __name__=="__main__":
    unittest.main()
