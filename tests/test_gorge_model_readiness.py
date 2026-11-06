"""Model readiness gates must fail closed on missing and outcome leakage."""
import unittest
from tools.gorge_model_readiness import audit


def row(seed, won, status="decisive", native=True):
    return {"deck":"mortarion_current","seed":seed,"status":status,
            "won":won,"full_native_available":native,"hero_seat":seed%4,
            "opening_basic_lands":2+seed%3,"opening_sol_ring":seed%2,
            "opening_arcane_signet":(seed//2)%2,"opening_mind_stone":seed%3==0}


class ModelReadinessTests(unittest.TestCase):
    def test_small_batch_not_fit_ready(self):
        r=audit([row(i,i%3==0) for i in range(12)])
        self.assertEqual(r["attempts"],12)
        self.assertEqual(r["statistical_readiness"],"not_ready")
        self.assertEqual(r["independent_seed_groups_complete"],12)

    def test_excluded_and_missing_not_zeros(self):
        rows=[row(1,1), row(2,0),row(3,None,"turn_cap")]
        rows[0]["opening_sol_ring"]=None
        r=audit(rows)
        self.assertEqual(r["decisive"],2)
        self.assertEqual(r["complete_case_decisive"],1)
        self.assertEqual(r["feature_missing_counts"]["opening_sol_ring"],1)
        self.assertEqual(r["outcome_status_counts"]["turn_cap"],1)

    def test_rejects_leakage(self):
        with self.assertRaisesRegex(ValueError,"postgame"):
            audit([row(1,1)],features=("game_turns",))

    def test_rejects_duplicates(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            audit([row(1,1),row(1,0)])

    def test_large_adequate_fixture_is_sample_only(self):
        rows=[row(i,i%2) for i in range(120)]
        r=audit(rows)
        self.assertEqual(r["statistical_readiness"],"sample_size_only_pass")
        self.assertFalse(r["production_eligible"])


if __name__ == "__main__":
    unittest.main()
