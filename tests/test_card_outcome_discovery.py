"""Opening-hand binary discovery tests: seed grouping, selection and failures."""
import math
import unittest
from random import Random

from tools.analyze_card_outcomes import (
    analyze, _records, _split, _ridge_logistic, _prob
)


def samples(seeds=120, scenarios=("balanced", "mixed")):
    batches = []
    for scenario in scenarios:
        rows = []
        for seed in range(seeds):
            rng = Random(seed*37+13)
            has_artist = seed % 4 == 0
            filler = ["Swamp", "Swamp", "Mountain", "Sol Ring",
                      "Rampant Growth", "Other Card", "Extra Card"]
            hand = (["Blood Artist"]+filler[:6]) if has_artist else filler
            win = rng.random() < (0.83 if has_artist else 0.14)
            rows.append({"seed": seed, "opening_hand": hand,
                         "opponent_roles": {"1":"aggro", "2":"control", "3":"value"},
                         "outcome":{"status":"win" if win else "loss"}})
        batches.append({
            "format":"commander-modeled-outcomes-v1", "schema_version":1,
            "deck_key":"mortarion_current", "deck_sha256":"a"*64,
            "requested_rounds":20, "scenario":scenario,
            "pilot_style":"adaptive", "provisional_mode":"safe",
            "pilot_archetype":{"primary":"aristocrats"},
            "opponent_fidelity":"abstract_opponent_pressure_not_card_exact",
            "outcomes_are_competitive_win_rates":False, "runs":rows
        })
    return batches


class OpeningHandDiscoveryTests(unittest.TestCase):
    def test_tree_selects_real_signal_and_logistic_validates_heldout(self):
        r=analyze(samples(),min_presence=7,top_k=4,trees=96)
        self.assertEqual(r["format"],"commander-opening-hand-discovery-v1")
        self.assertEqual(r["sample"]["games"],240)
        self.assertEqual(r["sample"]["distinct_seeds"],120)
        cards=r["logistic"]["card_effects"]
        self.assertIn("Blood Artist",[c["card"] for c in cards])
        artist=next(c for c in cards if c["card"]=="Blood Artist")
        self.assertGreater(artist["tree_gain"],0)
        self.assertGreater(artist["ridge_odds_ratio"],1)
        self.assertTrue(r["validation"]["cards_improve_heldout_brier"])

    def test_reused_seeds_not_split_across_train_and_test(self):
        rows,_=_records(samples(seeds=100))
        train,test=_split(rows)
        self.assertFalse({r["seed"] for r in train} &
                         {r["seed"] for r in test})
        self.assertEqual(len(train)+len(test),200)

    def test_missing_hand_is_not_zeros(self):
        data=samples()
        del data[0]["runs"][0]["opening_hand"]
        with self.assertRaisesRegex(ValueError,"rerun"):
            analyze(data)

    def test_mixed_pilot_and_horizon_fail_closed(self):
        data=samples()
        data[1]["pilot_style"]="conservative"
        with self.assertRaisesRegex(ValueError,"Mixed"):
            analyze(data)
        data=samples()
        data[1]["requested_rounds"]=30
        with self.assertRaisesRegex(ValueError,"Mixed"):
            analyze(data)

    def test_insufficient_seeds_and_unevaluated_refused(self):
        with self.assertRaisesRegex(ValueError,"20 distinct"):
            analyze(samples(seeds=12))
        data=samples()
        data[0]["runs"][0]["outcome"]["status"]="not_evaluated"
        with self.assertRaisesRegex(ValueError,"unevaluated"):
            analyze(data)

    def test_small_ridge_logistic_stays_finite(self):
        x=[[1,1],[1,1],[1,0],[1,0],[1,1],[1,0]]
        y=[1,1,0,0,1,0]
        beta=_ridge_logistic(x,y)
        self.assertTrue(all(math.isfinite(value) for value in beta))
        self.assertGreater(_prob(beta[0]+beta[1]),_prob(beta[0]))

    def test_same_seed_and_data_give_exact_same_report(self):
        a=analyze(samples(),top_k=4,trees=24)
        b=analyze(samples(),top_k=4,trees=24)
        self.assertEqual(a,b)

    def test_duplicate_scenario_seed_fails_closed(self):
        data=samples()
        data[0]["runs"].append(dict(data[0]["runs"][0]))
        with self.assertRaisesRegex(ValueError,"duplicate simulation seed"):
            analyze(data)


if __name__=="__main__":
    unittest.main()
