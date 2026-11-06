import unittest

from tools.gorge_analytic_identity import (
    game_id, parse_game_id, attach_identity, merge_source_batches,
)


class AnalyticIdentityTests(unittest.TestCase):
    def test_round_trip(self):
        gid=game_id("42143344243-1","mortarion_current",0,123)
        self.assertEqual(gid,"42143344243-1/mortarion_current/0/123")
        self.assertEqual(parse_game_id(gid),{
            "batch_id":"42143344243-1","deck":"mortarion_current",
            "shard":0,"seed":123,
        })

    def test_reject_noncanonical_or_injection(self):
        for bad in (
            "42143344243-1/mortarion_current/00/123",
            "42143344243-1/mortarion_current/0/0123",
            "../mortarion_current/0/123",
            "42143344243-1/mortarion_current/0/-1",
        ):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                parse_game_id(bad)

    def test_seed_reuse_across_batches_is_not_duplicate(self):
        descriptors=[
            {"batch_id":"42143344243-1","deck":"mortarion_current",
             "shard":0,"cohort_id":"cohort-a",
             "games":[{"seed":10,"deck":"mortarion_current","won":True}]},
            {"batch_id":"42143344244-1","deck":"mortarion_current",
             "shard":0,"cohort_id":"cohort-a",
             "games":[{"seed":10,"deck":"mortarion_current","won":False}]},
        ]
        joined=merge_source_batches(descriptors)
        self.assertEqual(len(joined),2)
        self.assertEqual(len({r["game_id"] for r in joined}),2)
        self.assertEqual({r["won"] for r in joined},{True,False})

    def test_duplicate_identity_fails(self):
        one={"batch_id":"42143344243-1","deck":"magnus_premium",
             "shard":0,"games":[{"seed":1,"deck":"magnus_premium"}]}
        with self.assertRaises(ValueError):
            merge_source_batches([one,one])

    def test_source_deck_and_hash_must_match(self):
        with self.assertRaises(ValueError):
            attach_identity({"seed":1,"hero":"magnus_premium"},
                batch="42143344243-1",deck="mortarion_current")
        with self.assertRaises(ValueError):
            attach_identity({"seed":1,"source_sha256":"a"*64},
                batch="42143344243-1",deck="mortarion_current",
                source_sha256="b"*64)
        with self.assertRaises(ValueError):
            attach_identity({"seed":1,"game_id":"other"},
                batch="42143344243-1",deck="mortarion_current")


if __name__=="__main__":
    unittest.main()
