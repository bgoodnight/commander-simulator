"""Prove source-sequenced counts, null-vs-zero and cast owner ambiguity."""
import unittest
from tools.gorge_event_features import event_features


def example():
    return {
        "schema":"gorge-native-trace-v1",
        "objects":[
            {"object_id":1,"card_name":"Sol Ring","owner":0},
            {"object_id":2,"card_name":"Arcane Signet","owner":1},
        ],
        "log":{"events":[
            {"seq":0,"kind":0},
            {"seq":1,"kind":11,"obj":1},
            {"seq":2,"kind":13,"amount":2},
            {"seq":3,"kind":31},
            {"seq":4,"kind":23},
            {"seq":5,"kind":11,"obj":2},
            {"seq":6,"kind":11,"obj":1},
            {"seq":7,"kind":5,"amount":4},
        ],"intents":[]},
        "snapshots":[
            {"turn":4,"after_event_seq":3,"boundary":"first_pending_decision_of_turn"},
            {"turn":8,"after_event_seq":7,"boundary":"first_pending_decision_of_turn"},
        ],
    }


class GorgeEventFeaturesTests(unittest.TestCase):
    def test_cutoff_and_owner_not_caster(self):
        a=event_features(example(),0,(4,8,12))
        self.assertEqual(a[0]["pod_cast_events"],1)
        self.assertEqual(a[0]["pod_mana_events"],1)
        self.assertEqual(a[0]["pod_token_creation_events"],1)
        self.assertEqual(a[0]["pod_land_play_events"],0)
        self.assertEqual(a[0]["hero_owned_card_cast_events"],1)
        self.assertEqual(a[1]["pod_cast_events"],3)
        self.assertEqual(a[1]["hero_owned_card_cast_events"],2)
        self.assertEqual(a[1]["hero_owned_card_cast_unique_cards"],1)
        self.assertEqual(a[1]["evidence_event_sequences"]["pod_cast_events"],[1,5,6])
        self.assertIsNone(a[1]["hero_mana_generated"])
        self.assertIsNone(a[1]["sacrifice_event_count"])
        self.assertIsNone(a[2]["pod_cast_events"])
        self.assertFalse(a[2]["landmark_observed"])

    def test_unknown_cast_owner_is_missing_not_zero(self):
        n=example()
        n["log"]["events"][1]["obj"]=900
        a=event_features(n,0,(4,))[0]
        self.assertEqual(a["pod_cast_events"],1)
        self.assertIsNone(a["hero_owned_card_cast_events"])
        self.assertFalse(a["hero_owned_cast_attribution_complete"])

    def test_no_events_before_cutoff_is_valid_zero(self):
        n=example()
        n["snapshots"]=[{"turn":1,"after_event_seq":0}]
        a=event_features(n,0,(1,))[0]
        self.assertEqual(a["pod_cast_events"],0)
        self.assertEqual(a["hero_owned_card_cast_events"],0)

    def test_future_event_cannot_be_used(self):
        a=event_features(example(),0,(4,))[0]
        self.assertNotIn(5,a["evidence_event_sequences"]["pod_cast_events"])
        self.assertNotIn(7,a["evidence_event_sequences"]["pod_damage_events"])

    def test_bad_source_order_rejected(self):
        n=example()
        n["log"]["events"][2]["seq"]=1
        with self.assertRaisesRegex(ValueError,"unordered event"):
            event_features(n,0,(4,))

    def test_unknown_snapshot_event_cutoff_rejected(self):
        n=example()
        n["snapshots"][1]["after_event_seq"]=400
        with self.assertRaisesRegex(ValueError,"snapshot cutoff"):
            event_features(n,0,(8,))


if __name__=="__main__":
    unittest.main()
