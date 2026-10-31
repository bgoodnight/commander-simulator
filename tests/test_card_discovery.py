"""Theorycraft-first-run metadata import and local autocomplete tests."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs

from commander_sim.card_cache import CardCatalog
from commander_sim.card_discovery import (
    local_suggestions, online_name_suggestions, prepare_theorycraft_deck
)
from tools.theorycraft import run


def card(name, identity, type_line="Artifact", color=(), faces=()):
    item = {
        "name": name, "oracle_id": identity, "layout": "normal",
        "cmc": 2, "type_line": type_line, "mana_cost": "{2}",
        "color_identity": list(color), "keywords": [],
        "scryfall_uri": "https://scryfall.com/card/test/" + identity,
        "legalities": {"commander": "legal"},
    }
    if faces:
        item["layout"] = "modal_dfc"
        item["card_faces"] = [{"name": f} for f in faces]
    return item


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.catalog = self.root / "cards.json"
        self.output = self.root / "prepared"
        self.deck = self.root / "theorycraft.txt"
        self.deck.write_text(
            "Commander\n1 Ghoulcaller Gisa\nLibrary\n1 Sol Ring\n98 Swamp\n",
            encoding="utf-8")
        self.records = {
            "Ghoulcaller Gisa": card("Ghoulcaller Gisa", "gisa",
                "Legendary Creature — Human Wizard", ("B",)),
            "Sol Ring": card("Sol Ring", "sol"),
            "Swamp": card("Swamp", "swamp", "Basic Land — Swamp"),
            "Midnight Banshee": card("Midnight Banshee", "banshee",
                "Creature — Spirit", ("B",)),
        }
        self.calls = []

    def request(self, names):
        self.calls.append(tuple(names))
        return [self.records[name] for name in names]

    def prepare(self, **kw):
        return prepare_theorycraft_deck(
            self.deck, "Ghoulcaller Gisa",
            catalog_path=self.catalog, output_dir=self.output,
            request_batch=self.request, **kw,
        )

    def test_first_run_fetches_missing_then_repeat_uses_cache_and_snapshot(self):
        first = self.prepare()
        self.assertEqual(first["new_identities_fetched"], 3)
        self.assertEqual(self.calls, [("Ghoulcaller Gisa", "Sol Ring", "Swamp")])
        self.assertEqual(first["physical_cards"], 100)
        self.assertFalse(first["gameplay_ready"])
        self.assertTrue(Path(first["manifest"]).exists())
        second = self.prepare()
        self.assertEqual(second["new_identities_fetched"], 0)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(second["snapshot"], first["snapshot"])
        self.assertEqual(second["deck_sha256"], first["deck_sha256"])
        self.assertEqual(len(CardCatalog(self.catalog).current), 3)

    def test_new_card_in_theorycrafted_deck_fetches_only_that_card(self):
        original = self.prepare()
        self.deck.write_text(
            "Commander\n1 Ghoulcaller Gisa\nLibrary\n1 Sol Ring\n"
            "1 Midnight Banshee\n97 Swamp\n", encoding="utf-8")
        updated = self.prepare()
        self.assertEqual(updated["new_identities_fetched"], 1)
        self.assertEqual(self.calls[-1], ("Midnight Banshee",))
        self.assertNotEqual(original["snapshot"], updated["snapshot"])
        self.assertTrue(Path(original["manifest"]).exists())
        self.assertEqual(len(CardCatalog(self.catalog).current), 4)
        self.assertEqual(self.prepare()["new_identities_fetched"], 0)

    def test_auto_fetch_can_be_disabled_offline(self):
        with self.assertRaisesRegex(ValueError, "Missing offline identities"):
            self.prepare(auto_fetch=False)
        self.assertEqual(self.calls, [])
        self.prepare()
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network")):
            self.assertEqual(self.prepare(auto_fetch=False)["new_identities_fetched"], 0)

    def test_invalid_or_typo_identity_never_silently_fuzzy_matched(self):
        self.deck.write_text(
            "Commander\n1 Ghoulcaller Gisa\nLibrary\n"
            "1 Midnite Banshee\n98 Swamp\n", encoding="utf-8")
        def fake(names):
            self.calls.append(tuple(names))
            return [self.records.get(n, self.records["Midnight Banshee"]) for n in names]
        with self.assertRaisesRegex(ValueError, "Expected one exact card/face"):
            prepare_theorycraft_deck(
                self.deck, "Ghoulcaller Gisa", catalog_path=self.catalog,
                output_dir=self.output, request_batch=fake
            )
        self.assertFalse(any(self.output.glob("*.manifest.json")))

    def test_local_autocomplete_is_case_insensitive_and_never_requests_network(self):
        self.prepare()
        self.deck.write_text(
            "Commander\n1 Ghoulcaller Gisa\nLibrary\n1 Sol Ring\n"
            "1 Midnight Banshee\n97 Swamp\n", encoding="utf-8")
        self.prepare()
        with patch("urllib.request.urlopen", side_effect=AssertionError("No API requests")):
            matches = local_suggestions("mid", catalog_path=self.catalog)
            self.assertEqual([m["name"] for m in matches], ["Midnight Banshee"])
            self.assertEqual(matches[0]["source"], "local_cache")
            self.assertEqual(local_suggestions("so", catalog_path=self.catalog)[0]["name"], "Sol Ring")
            self.assertEqual(local_suggestions("x", catalog_path=self.catalog), [])
        with self.assertRaises(ValueError):
            local_suggestions("b" * 151, catalog_path=self.catalog)

    def test_remote_autocomplete_is_separate_explicit_nonwriting_lookup(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, *args):
                return b'{"object":"catalog","data":["Midnight Banshee","Midnight Reaper"]}'
        requested = []
        def fake_open(request, timeout):
            requested.append((request.full_url, timeout))
            return FakeResponse()
        self.assertEqual(online_name_suggestions("Mid", opener=fake_open),
                         ["Midnight Banshee", "Midnight Reaper"])
        self.assertEqual(parse_qs(urlparse(requested[0][0]).query)["q"], ["Mid"])
        self.assertFalse(self.catalog.exists())  # separate from metadata writes
        self.assertEqual(online_name_suggestions("x", opener=fake_open), [])
        self.assertEqual(len(requested), 1)

    def test_theorycraft_command_prepares_then_observes_without_gameplay_claims(self):
        result = run(
            self.deck, "Ghoulcaller Gisa",
            catalog_path=self.catalog, output_dir=self.output,
            request_batch=self.request, turns=3, seed=4,
        )
        self.assertEqual(result["observation"]["mode"], "observation")
        self.assertEqual(len(result["observation"]["trace"]), 3)
        self.assertFalse(result["preflight"]["gameplay_ready"])
        again = run(
            self.deck, "Ghoulcaller Gisa", offline=True,
            catalog_path=self.catalog, output_dir=self.output,
            request_batch=self.request, turns=3, seed=4,
        )
        self.assertEqual(again["preflight"]["new_identities_fetched"], 0)
        self.assertEqual(again["observation"], result["observation"])


if __name__ == "__main__":
    unittest.main()
