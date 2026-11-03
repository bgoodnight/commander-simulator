"""Precon corpus provenance, native gorge replay contract, and pilot config."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.fetch_gorge_precons import (
    PRECONS,STOCK_SLUGS,GORGE_COMMIT,BASE,fetch_precons,validate_precon)
from tools.gorge_native_replay import index_native_trace


class GorgePreconTests(unittest.TestCase):
    def test_stock_sources_are_explicitly_classified(self):
        self.assertGreaterEqual(len(STOCK_SLUGS),4)
        self.assertEqual(len({p.slug for p in PRECONS}),len(PRECONS))
        self.assertTrue(all(p.provenance for p in PRECONS))
        self.assertTrue(any(p.kind=="upgraded_precon" for p in PRECONS))

    def test_stock_only_fetch_does_not_copy_upgraded_decks(self):
        requests=[]
        def fake(url):
            requests.append(url)
            name=url.split("/")[-1][:-5]
            return json.dumps({"name":name,"format":"commander",
                "commander":"Commanding Card",
                "cards":[{"name":"Commanding Card","count":1},
                         {"name":"Swamp","count":99}]}).encode()
        with tempfile.TemporaryDirectory() as td:
            doc=fetch_precons(td,fetch=fake)
            self.assertEqual(len(doc["decks"]),len(STOCK_SLUGS))
            self.assertEqual(len(requests),len(STOCK_SLUGS))
            self.assertEqual(doc["gorge_commit"],GORGE_COMMIT)
            self.assertEqual(
                {x["key"] for x in doc["decks"]},set(STOCK_SLUGS))
            self.assertTrue(all(x["kind"]=="stock_precon" for x in doc["decks"]))
            self.assertTrue(all(x["source"].startswith(BASE+"/") for x in doc["decks"]))
            self.assertTrue((Path(td)/"library_manifest.json").exists())

    def test_validation_fails_closed_on_wrong_counts_and_duplicates(self):
        valid={"format":"commander","commander":"The Captain",
               "cards":[{"name":"The Captain","count":1},
                        {"name":"Island","count":99}]}
        self.assertIs(validate_precon(valid,"test"),valid)
        for bad in (
            {**valid,"format":"constructed"},
            {**valid,"cards":[{"name":"The Captain","count":1}]},
            {**valid,"cards":[{"name":"The Captain","count":1},
                             {"name":"Island","count":50},
                             {"name":"Island","count":49}]},
        ):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_precon(bad,"test")

    def test_native_event_index_preserves_event_counts_and_unknowns(self):
        trace={
            "schema":"gorge-native-trace-v1","engine":"gorge",
            "format":"commander","seed":12,"chain":"abc",
            "decks":["a","b","c","d"],
            "policies":["bot"]*4,
            "log":{"seed":12,"intents":[{"something":"unchanged"}],
                   "events":[
                       {"seq":0,"kind":0},
                       {"seq":1,"kind":9},
                       {"seq":2,"kind":3,"player":0},
                       {"seq":3,"kind":250,"text":"new engine event"},
                       {"seq":4,"kind":9},
                       {"seq":5,"kind":13,"amount":1}
                   ]}
        }
        result=index_native_trace(trace)
        self.assertEqual(result["event_count"],6)
        self.assertEqual(result["intent_count"],1)
        self.assertEqual([x["events"] for x in result["segments"]],[1,3,2])
        self.assertEqual(result["segments"][1]["kinds"]["unknown_250"],1)
        self.assertEqual(result["segments"][-1]["raw_event_range"],[4,6])
        self.assertEqual(trace["log"]["events"][3]["text"],"new engine event")

    def test_native_trace_rejects_out_of_order_sequences_and_not_commander(self):
        good={"schema":"gorge-native-trace-v1","engine":"gorge",
              "format":"commander","decks":["a","b","c","d"],
              "policies":["bot"]*4,
              "log":{"events":[{"seq":1,"kind":9},{"seq":1,"kind":9}]}}
        with self.assertRaises(ValueError):
            index_native_trace(good)
        good["log"]["events"]=[]
        good["format"]="constructed"
        with self.assertRaises(ValueError):
            index_native_trace(good)


if __name__=="__main__":
    unittest.main()
