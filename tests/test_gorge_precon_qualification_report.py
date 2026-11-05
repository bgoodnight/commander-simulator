"""Offline source-evidence contract tests; does not execute Gorge games."""
import unittest
from tools.gorge_precon_qualification_report import report, select_trial_pool


def fixture():
    decks = [{"key":f"deck-{i:02}", "name":f"Deck {i}", "commander":f"Commander {i}",
              "color_identity":["U"],"decklist_sha256":f"sha-{i}",
              "oracle_complete":True} for i in range(60)]
    q={"schema":"gorge-precon-qualification-queue-v1",
       "oracle_bulk_sha256":"oracle-001","source_catalog_commit":"catalog-001",
       "decks":decks}
    runs={}
    for hero in ("mortarion_current","magnus_premium"):
        games=[]
        for j in range(60):
            picks=[f"deck-{(3*j+k)%60:02}" for k in range(3)]
            seat=j%4
            names=picks[:]
            names.insert(seat,hero)
            games.append({"seed":186000+j,"decks":names,"hero_seat":seat,
                          "finished":True,"replay_verified":True,
                          "draw":False,"winner_seat":seat,
                          "stall_reason":"","error":None})
        runs[hero]=games
    return q,runs


class PreconEvidenceTests(unittest.TestCase):
    def test_every_deck_has_six_clean_source_observations(self):
        q,runs=fixture()
        evidence=report(q,runs)
        self.assertEqual(evidence["eligible_bounded_trial"],60)
        self.assertEqual(evidence["approved_production_opponents"],0)
        self.assertTrue(all(row["rules_fidelity"]=="not_certified" and
                            not row["production_eligible"] for row in evidence["decks"]))
        panel={"schema":"gorge-initial-trial-opponents-v1",
               "source_oracle_sha256":"oracle-001",
               "opponents":["deck-00","deck-07","deck-31"]}
        selected=select_trial_pool(evidence,panel)
        self.assertEqual(selected["status"],"experimental_rotation_only")
        self.assertFalse(selected["eligible_for_analytics"])

    def test_failed_game_blocks_affected_deck_from_trial_pool(self):
        q,runs=fixture()
        runs["magnus_premium"][0]["finished"]=False
        runs["magnus_premium"][0]["replay_verified"]=False
        runs["magnus_premium"][0]["stall_reason"]="turns"
        evidence=report(q,runs)
        self.assertEqual(evidence["eligible_bounded_trial"],57)
        panel={"schema":"gorge-initial-trial-opponents-v1",
               "source_oracle_sha256":"oracle-001",
               "opponents":["deck-00","deck-01","deck-02"]}
        with self.assertRaisesRegex(ValueError,"not a validated"):
            select_trial_pool(evidence,panel)

    def test_ambiguous_provenance_is_rejected(self):
        q,runs=fixture()
        runs["mortarion_current"][0]["decks"][1]="mortarion_current"
        with self.assertRaisesRegex(ValueError,"Invalid hero"):
            report(q,runs)
        q,runs=fixture()
        runs["magnus_premium"][1]["seed"]=186000
        with self.assertRaisesRegex(ValueError,"fixed seeds"):
            report(q,runs)

    def test_unknown_or_custom_opponent_cannot_be_activated(self):
        q,runs=fixture()
        evidence=report(q,runs)
        panel={"schema":"gorge-initial-trial-opponents-v1",
               "source_oracle_sha256":"oracle-001",
               "opponents":["deck-00","deck-01","mortarion_current"]}
        with self.assertRaisesRegex(ValueError,"not a validated"):
            select_trial_pool(evidence,panel)


if __name__=="__main__":
    unittest.main()
