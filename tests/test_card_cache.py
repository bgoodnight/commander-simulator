"""Shared Scryfall catalog tests. All network access is mocked."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from commander_sim.card_cache import (
    CardCatalog, pinned_deck_entries, digest, deck_names,
)
from commander_sim.snapshots import validate_snapshot
from tools.fetch_deck_identities import fetch, _match_card

ROOT = Path(__file__).resolve().parents[1]


def card(name, oracle_id, types="Artifact", color_identity=(), *,
         oracle_text="Original metadata", faces=None):
    result = {
        "oracle_id": oracle_id, "name": name, "type_line": types,
        "cmc": 2, "mana_cost": "{2}", "keywords": [],
        "layout": "normal" if faces is None else "adventure",
        "colors": [], "color_identity": list(color_identity),
        "scryfall_uri": "https://scryfall.com/card/test/" + oracle_id,
        "legalities": {"commander": "legal"}, "oracle_text": oracle_text,
    }
    if faces is not None:
        result["card_faces"] = faces
    return result


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.catalog_path = self.base / "shared.json"
        self.magnus = card("Magnus the Red", "magnus", "Legendary Creature — Demon Primarch", ("U", "R"))
        self.gisa = card("Ghoulcaller Gisa", "gisa", "Legendary Creature — Human Wizard", ("B",))
        self.sol = card("Sol Ring", "sol-ring")
        self.island = card("Island", "island", "Basic Land — Island")
        self.swamp = card("Swamp", "swamp", "Basic Land — Swamp")
        self.records = {c["name"]: c for c in
                        (self.magnus, self.gisa, self.sol, self.island, self.swamp)}
        self.requests = []
        self.deck_a = self.base / "magnus.txt"
        self.deck_a.write_text("# A test deck\nCommander\n1 Magnus the Red\nLibrary\n1 Sol Ring\n98 Island\n")
        self.deck_b = self.base / "gisa.txt"
        self.deck_b.write_text("Commander\n1 Ghoulcaller Gisa\nLibrary\n1 Sol Ring\n98 Swamp\n")
        self.output_a = self.base / "magnus.json"
        self.output_b = self.base / "gisa.json"

    def request(self, names):
        self.requests.append(tuple(names))
        return [self.records[n] for n in names]

    def import_deck(self, deck, output, **kwargs):
        return fetch(deck, output, catalog_path=self.catalog_path,
                     request_batch=self.request, **kwargs)

    def test_first_import_fetches_each_unique_identity_once(self):
        manifest = self.import_deck(self.deck_a, self.output_a)
        self.assertEqual(self.requests, [("Magnus the Red", "Sol Ring", "Island")])
        self.assertEqual(len(manifest["cards"]), 3)
        self.assertEqual(len(CardCatalog(self.catalog_path).current), 3)
        self.assertEqual(len(pinned_deck_entries(self.deck_a,
                         self.output_a.with_suffix(".manifest.json"), self.catalog_path)), 3)
        validated = validate_snapshot(self.deck_a, self.output_a)
        self.assertEqual(validated.deck.count, 100)

    def test_repeat_and_overlapping_imports_only_fetch_missing_names(self):
        self.import_deck(self.deck_a, self.output_a)
        self.import_deck(self.deck_a, self.output_a)
        self.assertEqual(len(self.requests), 1)
        self.import_deck(self.deck_b, self.output_b)
        self.assertEqual(self.requests[-1], ("Ghoulcaller Gisa", "Swamp"))
        self.assertEqual(len(self.requests), 2)
        self.import_deck(self.deck_b, self.output_b)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(len(CardCatalog(self.catalog_path).current), 5)

    def test_offline_cache_hit_and_fail_closed_cache_miss(self):
        with self.assertRaisesRegex(ValueError, "Missing offline identities"):
            self.import_deck(self.deck_a, self.output_a, offline=True)
        self.assertFalse(self.catalog_path.exists())
        self.assertFalse(self.output_a.exists())
        self.assertEqual(self.requests, [])
        self.import_deck(self.deck_a, self.output_a)
        self.requests.clear()
        self.import_deck(self.deck_a, self.output_a, offline=True)
        self.assertEqual(self.requests, [])

    def test_seed_checked_in_snapshot_and_use_offline_without_network(self):
        deck = ROOT / "decklists/fixtures/magnus_flameslinger_v0_7_pre_delivery.txt"
        snap = ROOT / "simulator/card_data/flameslinger_v0_7_scryfall.json"
        output = self.base / "imported_from_seed.json"
        manifest = fetch(deck, output, catalog_path=self.catalog_path,
                         seed_pairs=((deck, snap),), offline=True, request_batch=self.request)
        self.assertEqual(len(manifest["cards"]), 76)
        self.assertEqual(self.requests, [])
        self.assertEqual(len(CardCatalog(self.catalog_path).current), 76)
        self.assertEqual(validate_snapshot(deck, output).deck.count, 100)

    def test_old_pinned_revision_remains_after_refresh_with_new_output(self):
        self.import_deck(self.deck_a, self.output_a)
        initial = pinned_deck_entries(self.deck_a,
                    self.output_a.with_suffix(".manifest.json"), self.catalog_path)
        updated = dict(self.sol, oracle_text="Updated rules text")
        self.records["Sol Ring"] = updated
        revised = self.base / "magnus_refreshed.json"
        self.import_deck(self.deck_a, revised, refresh=True)
        old_entries = pinned_deck_entries(self.deck_a,
                       self.output_a.with_suffix(".manifest.json"), self.catalog_path)
        new_entries = pinned_deck_entries(self.deck_a,
                       revised.with_suffix(".manifest.json"), self.catalog_path)
        self.assertEqual(initial, old_entries)
        self.assertEqual(old_entries[1]["card"]["oracle_text"], "Original metadata")
        self.assertEqual(new_entries[1]["card"]["oracle_text"], "Updated rules text")
        self.assertEqual(len(CardCatalog(self.catalog_path).revisions["sol-ring"]), 2)
        with self.assertRaisesRegex(ValueError, "Manifest already pins different"):
            self.import_deck(self.deck_a, self.output_a)

    def test_corrupt_revision_fails_closed(self):
        self.import_deck(self.deck_a, self.output_a)
        cached = json.loads(self.catalog_path.read_text())
        cached["revisions"]["sol-ring"][cached["current"]["sol-ring"]]["type_line"] = "Instant"
        self.catalog_path.write_text(json.dumps(cached))
        with self.assertRaisesRegex(ValueError, "Corrupt catalog"):
            CardCatalog(self.catalog_path)

    def test_ambiguous_alias_rejected_and_import_not_saved(self):
        duplicate = card("Sol Ring", "counterfeit-sol")
        self.records["Island"] = duplicate
        with self.assertRaisesRegex(ValueError, "Ambiguous cached card alias"):
            self.import_deck(self.deck_a, self.output_a)
        self.assertFalse(self.output_a.exists())
        self.assertFalse(self.catalog_path.exists())

    def test_network_failure_does_not_write_partial_cache_or_manifest(self):
        def fail(names):
            self.requests.append(tuple(names))
            raise TimeoutError("simulated outage")
        with self.assertRaisesRegex(ValueError, "Scryfall import failed"):
            fetch(self.deck_a, self.output_a, catalog_path=self.catalog_path,
                  request_batch=fail)
        self.assertFalse(self.output_a.exists())
        self.assertFalse(self.catalog_path.exists())

    def test_missing_or_changed_manifest_or_deck_hash_rejected(self):
        self.import_deck(self.deck_a, self.output_a)
        manifest = self.output_a.with_suffix(".manifest.json")
        self.deck_a.write_text(self.deck_a.read_text() + "# changed file\n")
        with self.assertRaisesRegex(ValueError, "does not match"):
            pinned_deck_entries(self.deck_a, manifest, self.catalog_path)

    def test_adventure_face_exact_matching_not_prefix_guessing(self):
        item = card("Research", "adventure-1", "Creature — Wizard",
                    faces=[{"name": "Research"}, {"name": "Quest"}])
        self.assertIs(_match_card("Research // Quest", [item]), item)
        with self.assertRaisesRegex(ValueError, "Expected one exact"):
            _match_card("Research // Fake", [item])

    def test_declared_card_names_ignore_comments_and_headings(self):
        raw = b"# note\nCommander\n1 Magnus the Red\nCreatures (1)\n1 Sol Ring\nLands (98)\n98 Island\n"
        self.assertEqual(deck_names(raw), ["Magnus the Red", "Sol Ring", "Island"])


if __name__ == "__main__":
    unittest.main()
