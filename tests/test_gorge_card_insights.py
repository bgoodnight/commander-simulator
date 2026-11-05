"""Card insights must reflect every source-verified game, not replay samples."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.gorge_card_insights import KINDS, merge_shards


def row(seed, chain):
    return {"seed": seed, "chain": chain, "decks":
            ["mortarion_current", "necron_dynasties", "wretched_ranks",
             "science-pip"], "player_seat": 0, "player_deck": "mortarion_current"}


def shard(seeds, casts):
    types={kind: [] for kind in KINDS}
    for kind in ("played", "creature"):
        types[kind]=[{"name": "Plague Marine",
                      "counts": [[seed,casts.get(seed,0)] for seed in seeds
                                 if casts.get(seed,0)],
                      "seen": [seed for seed in seeds if casts.get(seed,0)],
                      "durations": [],"timesPlayed": sum(casts.get(seed,0)
                                                         for seed in seeds),
                      "events": [[seed,4] for seed in seeds if casts.get(seed,0)]}]
    return {"schema":"gorge-card-insights-shard-v1",
            "deck":"mortarion_current",
            "deck_sha256":"a"*64,
            "completed_verified_games":len(seeds),
            "seed_chains":[[seed,"chain-"+str(seed)] for seed in seeds],
            "confirmed_tutors":0,"categories":types}


class CardInsightCoverage(unittest.TestCase):
    def test_full_cohort_not_biased_by_replay_sample(self):
        seeds=[30001,30002,30003,30004]
        with TemporaryDirectory() as tmp:
            files=[]
            for i,part in enumerate((seeds[:2],seeds[2:])):
                filename=Path(tmp)/f"shard-{i}.json"
                filename.write_text(json.dumps(shard(part,{30001:2,30004:1})))
                files.append(filename)
            report=merge_shards(files,[row(s,"chain-"+str(s)) for s in seeds])
            deck=report["decks"]["mortarion_current"]
            self.assertEqual(deck["verified_games"],4)
            self.assertEqual(deck["observed_games"],4)
            cast=deck["categories"]["played"][0]
            self.assertEqual(cast["games"],2)
            self.assertEqual(cast["eventCount"],3)
            self.assertEqual(cast["average"],.75)
            self.assertEqual(cast["score"],2)
            self.assertEqual(cast["median"],.5)
            with self.assertRaisesRegex(ValueError,"coverage incomplete"):
                merge_shards(files[:1],[row(s,"chain-"+str(s)) for s in seeds])

    def test_rejects_wrong_chain_or_duplicate_game(self):
        with TemporaryDirectory() as tmp:
            file=Path(tmp)/"shard.json"
            file.write_text(json.dumps(shard([30001,30002],{30001:1})))
            with self.assertRaisesRegex(ValueError,"misattributed"):
                merge_shards([file],[row(30001,"wrong"),row(30002,"chain-30002")])
            with self.assertRaisesRegex(ValueError,"misattributed"):
                merge_shards([file,file],[row(s,"chain-"+str(s)) for s in [30001,30002]])


if __name__=="__main__":
    unittest.main()
