"""Precon-only opponent selection, metadata and fixed Gorge role contracts."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.commander_deck_library import (
    load_library, opponent_keys, player_keys, validate_pod,
    validate_deck_files, matchup_annotations,
)

class DeckRoleTests(unittest.TestCase):
    def setUp(self):
        self.library = load_library()

    def test_six_stock_precons_only(self):
        self.assertEqual(set(opponent_keys(self.library)), {
            "necron_dynasties", "wretched_ranks", "cavalry-charge",
            "science-pip", "deadly-disguise", "avengers-assemble"
        })
        self.assertTrue(all("mortarion" not in x and "magnus" not in x
                            for x in opponent_keys(self.library)))
        self.assertTrue(all("mortarion" in x or "magnus" in x
                            for x in player_keys(self.library)))

    def test_legal_player_and_opponent_roles(self):
        validate_pod(self.library,"mortarion_current",
                     ["necron_dynasties","wretched_ranks","science-pip"])
        with self.assertRaises(ValueError):
            validate_pod(self.library,"necron_dynasties",
                         ["wretched_ranks","science-pip","cavalry-charge"])
        with self.assertRaises(ValueError):
            validate_pod(self.library,"magnus_premium",
                         ["mortarion_current","science-pip","cavalry-charge"])
        with self.assertRaises(ValueError):
            validate_pod(self.library,"magnus_premium",
                         ["science-pip","science-pip","cavalry-charge"])
        with self.assertRaises(ValueError):
            validate_pod(self.library,"magnus_premium",
                         ["science-pip","not-a-precon","cavalry-charge"])

    def test_color_archetype_annotations(self):
        items=matchup_annotations(self.library,["magnus_premium","science-pip"])
        self.assertEqual([x["role"] for x in items],["player","opponent"])
        self.assertEqual(items[0]["color_identity"],["U","R"])
        self.assertEqual(items[0]["colors_present"],
                         {"W":False,"U":True,"B":False,"R":True,"G":False})
        self.assertEqual(items[1]["primary_archetype"],"artifacts")

    def test_source_deck_identity_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            keys=["magnus_premium","necron_dynasties",
                  "wretched_ranks","cavalry-charge"]
            for key in keys:
                commander=next(x["commander"] for x in self.library["decks"]
                               if x["key"]==key)
                (root/(key+".json")).write_text(json.dumps({
                    "format":"commander","commander":commander,
                    "cards":[{"name":commander,"count":1},
                             {"name":"Basic Land","count":99}]
                }))
            hashes=validate_deck_files(self.library,keys[0],keys[1:],root)
            self.assertEqual(set(hashes),set(keys))
            file=root/"cavalry-charge.json"
            d=json.loads(file.read_text());d["commander"]="Wrong Commander"
            file.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,"commander name"):
                validate_deck_files(self.library,keys[0],keys[1:],root)

if __name__=="__main__":
    unittest.main()
