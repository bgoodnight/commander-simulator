"""Offline unit tests of strict MTGJSON stock precon import safety."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.commander_deck_library import load_library
from tools.import_mtgjson_stock_precons import EXPANDED_STOCK, select_entries, convert, import_expanded


class ExpandedStockTests(unittest.TestCase):
    def setUp(self):
        self.registry = {x["key"]: x for x in load_library()["decks"]}

    def test_curated_inventory_is_role_gated(self):
        self.assertEqual(len(EXPANDED_STOCK), 8)
        for slug in EXPANDED_STOCK:
            with self.subTest(slug=slug):
                self.assertEqual(self.registry[slug]["role"], "opponent")
                self.assertEqual(self.registry[slug]["provenance"], "stock_precon")

    def sample_source(self, slug):
        commander = self.registry[slug]["commander"]
        colors = self.registry[slug]["color_identity"]
        return {"data": {"name": EXPANDED_STOCK[slug], "type": "Commander Deck",
                         "code": "TEST",
                         "commander": [{"name": commander, "count": 1, "colorIdentity": colors}],
                         "mainBoard": [{"name": "Swamp", "count": 99}], "sideBoard": []}}

    def test_convert_exact_source(self):
        slug = "squirreled-away"
        deck = convert(self.sample_source(slug), slug, self.registry[slug])
        self.assertEqual(deck["commander"], self.registry[slug]["commander"])
        self.assertEqual(sum(x["count"] for x in deck["cards"]), 100)

    def test_reject_identity_and_count_errors(self):
        slug = "squirreled-away"
        source = self.sample_source(slug)
        source["data"]["commander"][0]["name"] = "Unverified Commander"
        with self.assertRaisesRegex(ValueError, "commander"):
            convert(source, slug, self.registry[slug])
        source = self.sample_source(slug)
        source["data"]["commander"][0]["colorIdentity"] = ["R"]
        with self.assertRaisesRegex(ValueError, "color identity"):
            convert(source, slug, self.registry[slug])
        source = self.sample_source(slug)
        source["data"]["mainBoard"][0]["count"] = 98
        with self.assertRaisesRegex(ValueError, "100 cards"):
            convert(source, slug, self.registry[slug])
        source = self.sample_source(slug)
        source["data"]["sideBoard"] = [{"name":"Additional card","count":1}]
        with self.assertRaisesRegex(ValueError, "sideboard"):
            convert(source, slug, self.registry[slug])

    def test_select_decks_by_unique_exact_name_and_type(self):
        rows = [{"name":name,"type":"Commander Deck","fileName":slug+"_TEST","code":"TEST"}
                for slug,name in EXPANDED_STOCK.items()]
        matched = select_entries({"data":rows})
        self.assertEqual(set(matched), set(EXPANDED_STOCK))
        rows[0]["type"] = "Theme Deck"
        with self.assertRaisesRegex(ValueError, "expected one"):
            select_entries({"data":rows})

    def test_fail_closed_before_writing_any_deck(self):
        rows = [{"name":name,"type":"Commander Deck","fileName":slug+"_TEST","code":"TEST"}
                for slug,name in EXPANDED_STOCK.items()]
        source = {"/DeckList.json": {"data": rows}}
        for slug in EXPANDED_STOCK:
            source["/decks/"+slug+"_TEST.json"] = self.sample_source(slug)
        # Make final import invalid; no partial outputs may be written.
        final = list(EXPANDED_STOCK)[-1]
        source["/decks/"+final+"_TEST.json"]["data"]["mainBoard"][0]["count"] = 90
        def fetch(url):
            return json.dumps(source[url.removeprefix("https://mtgjson.com/api/v5")]).encode()
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "100 cards"):
                import_expanded(Path(td), fetch=fetch)
            self.assertEqual(list(Path(td).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
