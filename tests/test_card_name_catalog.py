"""Name-list cache: one explicit API call, offline suggestions thereafter."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from commander_sim.card_cache import CardCatalog
from commander_sim.card_name_catalog import (
    read_name_catalog, refresh_name_catalog
)
from commander_sim.card_discovery import local_suggestions


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, *args):
        return json.dumps(self.payload).encode("utf-8")


class NameCatalogTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.names_path = self.root / "names.json"
        self.catalog = self.root / "catalog.json"

    def test_one_explicit_refresh_saves_complete_name_list_then_offline_searches(self):
        calls = []
        def open_fake(request, timeout):
            calls.append(request.full_url)
            return Response({"object": "catalog", "data": [
                "Sol Ring", "Midnight Banshee", "Midnight Reaper", "Sol Ring"
            ]})
        result = refresh_name_catalog(self.names_path, opener=open_fake)
        self.assertEqual(result["names"], 3)
        self.assertEqual(len(calls), 1)
        self.assertIn("/catalog/card-names", calls[0])
        self.assertEqual(len(read_name_catalog(self.names_path)), 3)
        with patch("urllib.request.urlopen", side_effect=AssertionError("No HTTP")):
            suggestions = local_suggestions(
                "mid", catalog_path=self.catalog,
                name_catalog_path=self.names_path
            )
            self.assertEqual([x["name"] for x in suggestions],
                             ["Midnight Banshee", "Midnight Reaper"])
            self.assertTrue(all(x["requires_metadata_import"] for x in suggestions))
            self.assertTrue(all(x["oracle_id"] is None for x in suggestions))

    def test_cached_metadata_is_preferred_over_names_only_suggestion(self):
        refresh_name_catalog(
            self.names_path, opener=lambda *args, **kwargs: Response(
                {"data": ["Sol Ring", "Sol Ringlet", "Sol Crystal"]}
            )
        )
        cached = CardCatalog(self.catalog)
        cached.add_card({
            "name": "Sol Ring", "oracle_id": "sol",
            "layout": "normal", "type_line": "Artifact",
            "cmc": 1, "color_identity": [], "keywords": [],
            "scryfall_uri": "https://scryfall.com/test/sol",
        })
        cached.save()
        matches = local_suggestions(
            "Sol Ring", catalog_path=self.catalog,
            name_catalog_path=self.names_path
        )
        self.assertEqual(matches[0]["name"], "Sol Ring")
        self.assertEqual(matches[0]["source"], "local_cache")
        self.assertFalse(matches[0]["requires_metadata_import"])
        self.assertEqual(sum(x["name"] == "Sol Ring" for x in matches), 1)

    def test_corrupt_names_list_never_authorizes_an_identity(self):
        self.names_path.write_text('{"schema_version":1,"source":"Scryfall card-names catalog","names":["Fake"]}')
        with self.assertRaisesRegex(ValueError, "Invalid or modified"):
            read_name_catalog(self.names_path)
        self.names_path.write_text("[]")
        with self.assertRaisesRegex(ValueError, "Invalid offline"):
            read_name_catalog(self.names_path)

    def test_unavailable_catalog_falls_back_to_cached_cards(self):
        self.assertEqual(read_name_catalog(self.names_path), ())
        with patch("urllib.request.urlopen", side_effect=AssertionError("No HTTP")):
            self.assertEqual(local_suggestions(
                "Missing", catalog_path=self.catalog,
                name_catalog_path=self.names_path
            ), [])


if __name__ == "__main__":
    unittest.main()
