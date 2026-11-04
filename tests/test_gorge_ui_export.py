"""Gorge UI export regression tests with real-shaped events and secrets."""
import unittest
from tools.gorge_ui_export import convert

def sample():
    return {"schema":"gorge-native-trace-v1","engine":"gorge",
            "format":"commander","seed":100,"chain":"abc",
            "decks":["mortarion_current","magnus_premium",
                     "necron_dynasties","wretched_ranks"],
            "policies":["bot"]*4,
            "log":{"intents":[{"seq":10,"player":0,"choices":[0]}],
                   "events":[
                       {"seq":0,"kind":0,"amount":4},
                       {"seq":1,"kind":2,"obj":2,"to":1,"secret":True},
                       {"seq":2,"kind":9,"amount":1},
                       {"seq":3,"kind":11,"obj":2,"text":"Wayfarer's Bauble"},
                       {"seq":4,"kind":13,"amount":1,"counter":"B"},
                       {"seq":5,"kind":3,"obj":3,"secret":True},
                       {"seq":6,"kind":23,"obj":4},
                       {"seq":7,"kind":9,"amount":2,"player":1},
                       {"seq":8,"kind":31,"text":"ur_1_1_elemental"},
                       {"seq":9,"kind":500,"text":"future event"},
                   ]}}

class GorgeUIExportTests(unittest.TestCase):
    def test_source_evidence_and_privacy(self):
        doc=convert(sample())
        self.assertEqual(doc["schema"],"gorge-ui-replay-v1")
        self.assertEqual(doc["visibility"],"public_events_only")
        self.assertEqual(doc["source"]["omitted_hidden_events"],2)
        self.assertEqual(doc["source"]["total_native_decisions"],1)
        self.assertEqual(doc["object_identity"]["2"],"Wayfarer's Bauble")
        self.assertEqual(next(e["card_name"] for e in doc["turns"][1]["events"] if e["kind"]=="cast"),
                         "Wayfarer's Bauble")
        self.assertEqual(doc["turns"][2]["events"][-1]["kind"],"native_500")
        self.assertIsNone(doc["state"]["hands"])
        self.assertIsNone(doc["state"]["life"])
        self.assertFalse(any(e["kind"]=="draw" for t in doc["turns"]
                             for e in t["events"]))

    def test_full_trace_can_be_retained_only_with_explicit_opt_in(self):
        doc=convert(sample(),include_hidden=True)
        self.assertEqual(doc["visibility"],"omniscient")
        self.assertEqual(doc["source"]["omitted_hidden_events"],0)

    def test_explicit_hidden_draw_can_be_identified_without_inferring_a_card(self):
        raw=sample()
        raw["objects"]=[{"object_id":3,"card_name":"Swamp","effective_name":"Swamp"}]
        doc=convert(raw,include_hidden=True)
        draws=[e for t in doc["turns"] for e in t["events"] if e["kind"]=="draw"]
        self.assertEqual(len(draws),1)
        self.assertEqual(draws[0]["card_name"],"Swamp")
        self.assertEqual(doc["object_identity"]["3"],"Swamp")
        self.assertTrue(doc["synthetic_simulation_only"])
        self.assertNotIn("objects",doc)
        self.assertNotIn("log",doc)

    def test_invalid_events_fail_closed(self):
        raw=sample()
        raw["log"]["events"][3]["seq"]=2
        with self.assertRaises(ValueError):
            convert(raw)

    def test_requires_commander_and_four_seats(self):
        raw=sample()
        raw["format"]="standard"
        with self.assertRaises(ValueError):
            convert(raw)
        raw=sample()
        raw["decks"]=["a","b"]
        with self.assertRaises(ValueError):
            convert(raw)

if __name__=="__main__":
    unittest.main()
