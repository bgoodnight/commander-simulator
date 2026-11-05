"""Explicit bounded-trial pool cannot admit custom or repinned opponents."""
import unittest
from tools.stage_gorge_precon_qualification import build_queue
from tools.gorge_trial_panel_validate import validate
def fixtures():
    decks=[]; selected=[]
    for i in range(60):
        key=f"deck-{i:02d}"
        cards=[{"name":f"Card {i}","count":100,"resolved":True,
                "oracle_id":str(i),"mana_value":2,"types":["Creature"]}]
        decks.append({"key":key,"name":key,"commander":f"Commander {i}",
                      "set_code":"TEST","release_date":"2025-01-01",
                      "color_identity":["U"],"cards":cards,"cards_resolved":100,
                      "is_duplicate_variant":False,"active_opponent":False,
                      "counts":{"creatures":100},"mechanic_keywords":{},
                      "nonland_mean_mana_value":2})
        selected.append({"key":key})
    enrichment={"schema":"gorge-precon-card-metadata-enrichment-v1",
                "oracle_bulk_sha256":"abc","source_catalog_commit":"commit",
                "as_of":"2026-11-05","decks":decks}
    panel={"schema":"gorge-opponent-selection-assessment-v1",
           "status":"provisional_not_gorge_qualified",
           "source_oracle_sha256":"abc","source_catalog_commit":"commit",
           "as_of":"2026-11-05","selection_method":"fixture",
           "shortlist":selected}
    return enrichment,panel



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
