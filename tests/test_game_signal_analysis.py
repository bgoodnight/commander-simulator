"""Discovery is fitted only to observed, seed-grouped game evidence."""
import unittest
from tools.discover_game_signals import design, features, analyze


def example(seed,scenario,won):
    combo=scenario=="mixed"
    hand=["Swamp"]*6+["Blood Artist" if seed%3==0 else "Cabal Coffers"]
    return {
        "format":"commander-game-observations-v1",
        "schema_version":1,
        "deck_key":"mortarion_physical_final",
        "deck_sha256":"a"*64,
        "seed":seed,
        "scenario":scenario,
        "pilot_style":"adaptive",
        "provisional_mode":"safe",
        "requested_rounds":30,
        "completed_rounds":3 if seed==0 else 12,
        "mulligan":{"opening_hand":hand},
        "opponent_roles":{"1":"aggro","2":"control",
                          "3":"combo" if combo else "value"},
        "outcome":{"status":"win" if won else "loss",
                   "completed_rounds":3 if seed==0 else 12},
        "life_history":[{"life_totals":{"0":40,"1":40,"2":40,"3":40}}]*13,
        "state_snapshots":[{"hand":["Swamp"],"battlefield":[],"graveyard":[]}] *12,
        "turn_records":[{"events":[],"land_count":3,"creature_count":0,
                         "mana_rock_count":0,"hand_size":4}]*12
    }


class ElasticNetDiscoveryTests(unittest.TestCase):
    def test_pregame_features_do_not_look_ahead(self):
        row=example(3,"balanced",True)
        row["turn_records"][0]["events"].append({"type":"creature_cast","card":"Black Lotus"})
        prior=features(row,0)
        self.assertIn("opening:Blood Artist",prior)
        self.assertNotIn("actions:casts",prior)
        self.assertNotIn("Black Lotus",str(prior))

    def test_landmark_excludes_early_terminal_games(self):
        rows=[example(i,"mixed",i%3==0) for i in range(15)]
        cohort,names,matrix,y,parents=design(rows,landmark=6,min_support=2)
        self.assertEqual(len(cohort),14)
        self.assertEqual(len(matrix),14)
        self.assertIn("resource:land_count",names)

    def test_fits_exploratory_model_without_tree_or_ridge(self):
        try:
            import sklearn
        except ImportError:
            self.skipTest("Analysis-only optional scikit-learn dependency")
        rows=[example(i,scenario, i%3==0 or (scenario=="balanced" and i%4==0))
              for scenario in ("balanced","mixed") for i in range(60)]
        result=analyze(rows,landmark=0,min_support=6,bootstrap=2)
        self.assertEqual(result["status"],"ready")
        self.assertEqual(result["independent_seeds"],60)
        self.assertGreater(result["candidate_main_effects"],1)
        self.assertIn("holdout_brier",result)
        self.assertIn("opponent_baseline_brier",result)
        self.assertEqual(result["method"],"hierarchical_elastic_net_logistic")


if __name__=="__main__":
    unittest.main()
