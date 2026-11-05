"""Explicit bounded-trial pool cannot admit custom or repinned opponents."""
import unittest
from tools.stage_gorge_precon_qualification import build_queue
from tools.gorge_trial_panel_validate import validate
from test_stage_gorge_precon_qualification import fixtures


def setup():
    queue=build_queue(*fixtures())
    keys=[d["key"] for d in queue["decks"][:12]]
    panel={"schema":"gorge-initial-trial-opponents-v1",
           "status":"requires_source_qualification_check",
           "approved_for_production":False,
           "source_oracle_sha256":queue["oracle_bulk_sha256"],
           "observed_by_hero":{"mortarion_current":3,"magnus_premium":3},
           "opponents":keys,
           "pinned_decklists":{d["key"]:d["decklist_sha256"] for d in queue["decks"][:12]}}
    return queue,panel


class TrialPanelTests(unittest.TestCase):
    def test_exact_source_pinned_pool(self):
        queue,panel=setup()
        self.assertEqual(len(validate(queue,panel)),12)

    def test_source_and_role_changes_refused(self):
        for mutation in ("hash","oracle","production","role","status","insufficient"):
            queue,panel=setup()
            if mutation=="hash":
                panel["pinned_decklists"][panel["opponents"][0]]="wrong"
            elif mutation=="oracle":
                panel["source_oracle_sha256"]="wrong"
            elif mutation=="production":
                panel["approved_for_production"]=True
            elif mutation=="role":
                queue["decks"][0]["active_opponent"]=True
            elif mutation=="status":
                panel["status"]="current"
            elif mutation=="insufficient":
                panel["observed_by_hero"]["magnus_premium"]=2
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate(queue,panel)

if __name__=="__main__":
    unittest.main()
