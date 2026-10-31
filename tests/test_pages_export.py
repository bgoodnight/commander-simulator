"""Static GitHub Pages release gate: no Python backend or unverified results."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.build_pages_deck_lab import build, DEFAULT_SEEDS, card_image


class StaticPagesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.destination=Path(self.temp.name)/"pages"

    def run_build(self, **kwargs):
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network")):
            return build(self.destination, **kwargs)

    def test_six_verified_decks_and_fixed_seed_observations_are_exported(self):
        manifest=self.run_build()
        self.assertEqual(manifest["decks"],6)
        self.assertGreater(manifest["cards"],80)
        self.assertGreater(manifest["names"],30000)
        self.assertEqual(manifest["seeds"],list(DEFAULT_SEEDS))
        datasets=json.loads((self.destination/"decks.json").read_text())
        results=json.loads((self.destination/"observations.json").read_text())
        self.assertEqual(datasets["data_mode"],"precomputed_observation_only")
        self.assertEqual(len(datasets["decks"]),6)
        for deck in datasets["decks"]:
            with self.subTest(deck=deck["key"]):
                self.assertEqual(deck["card_count"],100)
                self.assertEqual(sum(e["qty"] for e in deck["cards"]),100)
                self.assertIn(deck["commander_id"],datasets["cards"])
                self.assertEqual(set(results[deck["key"]]),set(map(str,DEFAULT_SEEDS)))
                for seed,record in results[deck["key"]].items():
                    self.assertEqual(record["seed"],int(seed))
                    self.assertEqual(record["deck_sha256"],deck["deck_sha256"])
                    self.assertEqual(record["mode"],"observation")
                    self.assertEqual(len(record["trace"]),6)
                    self.assertTrue(all(not t["playable_now"] for t in record["trace"]))

    def test_only_allowlisted_site_data_and_no_workspace_are_exported(self):
        self.run_build()
        permitted={"index.html","app.js","style.css","decks.json",
                   "observations.json","names.json","build-manifest.json",".nojekyll"}
        self.assertEqual({p.name for p in self.destination.iterdir()},permitted)
        self.assertNotIn("shared_scryfall_catalog.json",permitted)
        self.assertFalse(any(p.is_dir() for p in self.destination.iterdir()))
        page=(self.destination/"index.html").read_text()
        script=(self.destination/"app.js").read_text()
        self.assertIn("commander-rail",page)
        self.assertIn("drop-ring",page)
        self.assertIn("audio-toggle",page)
        self.assertIn("Cached Results",page)
        self.assertIn("prefers-reduced-motion",(self.destination/"style.css").read_text())
        self.assertIn("observations.json",script)
        self.assertIn("localStorage",script)
        self.assertNotIn("/api/observation",script)
        self.assertNotIn("eval(",script)

    def test_all_canonical_commander_art_paths_are_optional_official_cdn(self):
        self.run_build()
        data=json.loads((self.destination/"decks.json").read_text())
        for deck in data["decks"]:
            image=data["cards"][deck["commander_id"]]["art"]
            self.assertIsNotNone(image)
            self.assertTrue(image.startswith("https://cards.scryfall.io/art_crop/front/"))
        self.assertIsNone(card_image({"id":"not-a-real-id"}))

    def test_build_refuses_duplicate_seeds(self):
        with self.assertRaisesRegex(ValueError,"distinct"):
            self.run_build(seeds=(1,1))


if __name__=="__main__":
    unittest.main()
