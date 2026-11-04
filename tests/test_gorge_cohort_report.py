"""Ensure Gorge high-level statistics never inherit the replay sample."""
import unittest

from tools.gorge_cohort_report import eligible, make_report, regression


def game(seed, winner, hero="mortarion_current", retained=False):
    seat=seed % 4
    opponents=["necron_dynasties","wretched_ranks","science-pip"]
    decks=opponents[:]
    decks.insert(seat,hero)
    archetypes={
        "necron_dynasties":("artifact_recursion",["artifact_synergy"],["B"]),
        "wretched_ranks":("tokens",["zombies"],["B"]),
        "science-pip":("artifacts",["energy"],["W","U","R"]),
    }
    metadata=[]
    for i,deck in enumerate(decks):
        theme,more,colors=archetypes.get(deck,("aristocrats",[],["B"]))
        metadata.append({"seat":i,"deck_key":deck,
                         "role":"player" if i==seat else "opponent",
                         "primary_archetype":theme,
                         "secondary_archetypes":more,
                         "color_identity":colors})
    return {"seed":seed,"finished":True,"replay_verified":True,
            "player_seat":seat,"player_deck":hero,"decks":decks,
            "winner_seat":winner,"draw":False,"turns":25+(seed%9),
            "seat_metadata":metadata,"detailed_replay_retained":retained}


class FullCohortTests(unittest.TestCase):
    def test_full_denominator_excludes_sample_bias(self):
        rows=[]
        for n in range(150):
            seat=n%4
            rows.append(game(10000+n, seat if n%3==0 else (seat+1)%4,
                             retained=n<3))
        report=make_report(rows)
        full=report["decks"]["mortarion_current"]
        self.assertEqual(full["n"],150)
        self.assertEqual(full["wins"],50)
        self.assertEqual(full["detailed_replay_count"],3)
        self.assertEqual(full["groups"]["opponents"][0]["n"],150)
        self.assertEqual(full["groups"]["seats"][0]["n"],38)
        self.assertEqual(full["regressions"]["opponents"]["n"],150)
        self.assertEqual(full["regressions"]["opponents"]["status"],"ready")
        self.assertEqual(full["regressions"]["colors"]["status"],"ready")
        self.assertGreaterEqual(full["median_game_turns"],25)

    def test_rejects_wrong_player_seat_or_duplicate_seeds(self):
        row=game(7000,0)
        self.assertTrue(eligible(row))
        bad={**row,"player_deck":"magnus_budget"}
        self.assertFalse(eligible(bad))
        with self.assertRaisesRegex(ValueError,"Invalid or unverified"):
            make_report([bad])
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            make_report([row,row])

    def test_regression_reports_insufficient_outcome_variation(self):
        rows=[game(20000+i,i%4) for i in range(100)]
        model=regression(rows,"opponents")
        self.assertEqual(model["status"],"insufficient_data")
        self.assertEqual(model["n"],100)


if __name__=="__main__":
    unittest.main()
