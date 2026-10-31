"""M1 fixture registration and honest offline readiness checks."""
from pathlib import Path
import tempfile
import unittest

from commander_sim.card_cache import CardCatalog, deck_names
from commander_sim.deck_fixtures import FIXTURES, LEGACY_SEEDS, ROOT
from tools.import_deck_fixtures import prepare
from commander_sim.snapshots import validate_snapshot
from commander_sim.observation import observe


class DeckFixtureTests(unittest.TestCase):
    def test_six_authentic_variants_are_100_cards_with_distinct_fixture_keys(self):
        self.assertEqual(len(FIXTURES), 6)
        self.assertEqual(len({fixture.key for fixture in FIXTURES}), len(FIXTURES))
        for fixture in FIXTURES:
            with self.subTest(deck=fixture.key):
                raw = fixture.deck_path.read_text(encoding="utf-8")
                self.assertIn("Commander\n1 " + fixture.commander + "\n", raw)
                self.assertIn("Library\n", raw)
                entries = [line for line in raw.splitlines() if line.strip()
                           and line.strip()[0].isdigit()]
                self.assertEqual(sum(int(line.split()[0]) for line in entries), 100)
                self.assertGreaterEqual(len(deck_names(raw.encode("utf-8"))), 55)

    def test_legacy_snapshot_sources_are_present_and_hash_checked(self):
        for deck, snapshot in LEGACY_SEEDS:
            with self.subTest(deck=deck):
                self.assertTrue((ROOT / deck).is_file())
                self.assertTrue((ROOT / snapshot).is_file())
        with tempfile.TemporaryDirectory() as temp:
            cache = CardCatalog(Path(temp) / "catalog.json")
            for deck, snapshot in LEGACY_SEEDS:
                cache.seed_snapshot(ROOT / snapshot, deck_path=ROOT / deck)
            cache.save()
            self.assertIsNotNone(CardCatalog(cache.path).lookup("Sol Ring"))

    def test_only_gisa_fully_importable_without_any_additional_api(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            report = prepare(catalog_path=p / "catalog.json", output_dir=p,
                             selected=["wretched_ranks", "mortarion_current"])
            deck_status = {deck["key"]: deck for deck in report["decks"]}
            self.assertEqual(report["mode"], "offline_only")
            self.assertEqual(deck_status["wretched_ranks"]["status"], "validated_observation")
            self.assertEqual(deck_status["wretched_ranks"]["fetched"], 0)
            self.assertEqual(deck_status["wretched_ranks"]["physical_cards"], 100)
            self.assertEqual(deck_status["mortarion_current"]["status"], "missing_metadata")
            self.assertGreater(deck_status["mortarion_current"]["missing_before_import"], 0)
            self.assertFalse((p / "mortarion_current_m1_scryfall.json").exists())
            fixture = next(f for f in FIXTURES if f.key == "wretched_ranks")
            self.assertEqual(validate_snapshot(fixture.deck_path,
                             p / "wretched_ranks_m1_scryfall.json",
                             commander=fixture.commander).deck.count, 100)
            trace = observe(fixture.deck_path,
                            p / "wretched_ranks_m1_scryfall.json",
                            commander=fixture.commander, seed=0)
            self.assertEqual(len(trace["trace"]), 6)
            self.assertTrue(all(not t["playable_now"] for t in trace["trace"]))

    def test_unknown_fixture_name_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "Unknown fixture"):
                prepare(selected=["made_up"], catalog_path=Path(temp) / "cache.json")


if __name__ == "__main__":
    unittest.main()
