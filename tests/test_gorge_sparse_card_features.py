import unittest
from tools.gorge_sparse_card_features import extract_card_rows

def fixture():
    empty={"zones":{"hand":[],"battlefield":[],"graveyard":[],"exile":[]}}
    def snap(t,seq,hand,board):
        return {"turn":t,"after_event_seq":seq,
                "boundary":"first_pending_decision_of_turn",
                "players":[{"zones":{"hand":hand,"battlefield":board,
                                     "graveyard":[],"exile":[]}},empty,empty,empty]}
    return {"schema":"gorge-native-trace-v1","seed":123,
            "objects":[{"object_id":1,"owner":0,"card_name":"Sol Ring"},
                       {"object_id":2,"owner":0,"card_name":"Swamp"},
                       {"object_id":3,"owner":1,"card_name":"Other"},
                       {"object_id":4,"owner":0,"card_name":"Bastion of Remembrance"}],
            "log":{"events":[{"seq":0,"kind":0},{"seq":1,"kind":11,"obj":1},
                             {"seq":2,"kind":13},{"seq":5,"kind":11,"obj":3},
                             {"seq":9,"kind":11,"obj":4}],"intents":[]},
            "snapshots":[snap(4,2,[2],[1]),snap(8,9,[2,4],[1])]}

class SparseTests(unittest.TestCase):
    def test_temporal_cutoff(self):
        rows,qa=extract_card_rows(fixture(),0,"batch-1",(4,8,12))
        early=[r for r in rows if r["landmark_global_turn"]==4]
        late=[r for r in rows if r["landmark_global_turn"]==8]
        self.assertEqual({r["card_name"] for r in early},{"Sol Ring","Swamp"})
        self.assertIn("Bastion of Remembrance",{r["card_name"] for r in late})
        self.assertEqual(next(r for r in early if r["card_name"]=="Sol Ring")["observed_first_cast_seq_owner"],1)
        self.assertEqual(qa["landmarks_observed"],2)
        self.assertFalse(any(r["landmark_global_turn"]==12 for r in rows))

    def test_missing_owner_not_zero(self):
        n=fixture()
        n["log"]["events"][1]["obj"]=900
        rows,qa=extract_card_rows(n,0,"batch-1",(4,))
        self.assertEqual(qa["unresolved_cast_events"],1)
        self.assertTrue(all(not r["cast_ownership_complete_through_landmark"] for r in rows))

    def test_future_object_not_early_feature(self):
        n=fixture()
        n["objects"].append({"object_id":5,"owner":0,"card_name":"Future"})
        rows,_=extract_card_rows(n,0,"batch-1",(4,8))
        self.assertFalse(any(r["card_name"]=="Future" for r in rows))

    def test_bad_snapshot_rejected(self):
        n=fixture()
        n["snapshots"][0]["after_event_seq"]=100
        with self.assertRaises(ValueError):
            extract_card_rows(n,0,"batch-1")

if __name__=="__main__":
    unittest.main()
