"""Read-only Deck Lab U0 contracts, using real pinned M1 deck files."""
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen
import json

from commander_sim.deck_fixtures import FIXTURES
from commander_sim.deck_lab_api import catalog_response, deck_detail, observation_response
from tools.deck_lab import respond, Handler


class DeckLabTests(unittest.TestCase):
    def test_all_six_commander_decks_are_inspectable_offline(self):
        data = catalog_response()
        self.assertEqual(len(data["decks"]), 6)
        self.assertTrue(all(d["status"] == "validated_observation"
                            for d in data["decks"]))
        self.assertTrue(all(not d["actual_gameplay_available"] for d in data["decks"]))
        for fixture in FIXTURES:
            with self.subTest(deck=fixture.key):
                detail = deck_detail(fixture.key)
                self.assertEqual(detail["physical_cards"], 100)
                self.assertEqual(sum(c["quantity"] for c in detail["cards"]), 100)
                self.assertEqual(detail["commander"], fixture.commander)
                self.assertFalse(detail["actual_gameplay_available"])
                self.assertEqual(detail["ability_coverage"], "not assessed by card metadata import")

    def test_observation_replay_and_no_legal_spell_claims(self):
        for key in ("magnus_premium", "wretched_ranks", "mortarion_current",
                    "necron_dynasties"):
            with self.subTest(deck=key):
                a = observation_response(key, seed=11, turns=6)
                b = observation_response(key, seed=11, turns=6)
                self.assertEqual(a, b)
                self.assertEqual(a["mode"], "observation")
                self.assertTrue(all(t["playable_now"] == [] for t in a["trace"]))
                self.assertEqual(len(a["trace"]), 6)

    def test_local_api_is_read_only_and_unknown_routes_fail_closed(self):
        self.assertEqual(len(respond("/api/decks", {})["decks"]), 6)
        self.assertEqual(respond("/api/deck", {"key": ["mortarion_ideal"]})["physical_cards"], 100)
        obs = respond("/api/observation",
                      {"key": ["wretched_ranks"], "turns": ["3"], "seed": ["5"]})
        self.assertEqual(obs["turns"], 3)
        with self.assertRaises(KeyError):
            respond("/api/edits", {})
        with self.assertRaisesRegex(ValueError, "Unknown deck fixture"):
            respond("/api/deck", {"key": ["fake"]})

    def test_local_http_server_serves_static_page_and_read_only_api(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        runner = Thread(target=server.serve_forever, daemon=True)
        runner.start()
        try:
            base = "http://127.0.0.1:" + str(server.server_port)
            with urlopen(base + "/", timeout=5) as response:
                self.assertEqual(response.status, 200)
                html = response.read().decode("utf-8")
                self.assertIn("Commander Deck Lab", html)
                self.assertIn("Observation mode only.", html)
            with urlopen(base + "/api/decks", timeout=5) as response:
                self.assertEqual(response.status, 200)
                body = json.load(response)
                self.assertEqual(len(body["decks"]), 6)
            with urlopen(base + "/api/observation?key=wretched_ranks&seed=0&turns=3",
                         timeout=5) as response:
                self.assertEqual(response.status, 200)
                body = json.load(response)
                self.assertEqual(body["turns"], 3)
                self.assertEqual(body["mode"], "observation")
        finally:
            server.shutdown()
            server.server_close()
            runner.join(timeout=5)

    def test_inputs_are_bounded_and_no_metadata_api_called(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Unexpected network")):
            data = respond("/api/observation",
                           {"key": ["mortarion_current"], "turns": ["4"], "seed": ["0"]})
            self.assertEqual(data["turns"], 4)
            with self.assertRaises(ValueError):
                respond("/api/observation", {"key": ["mortarion_current"], "turns": ["1000"]})
            with self.assertRaises(ValueError):
                respond("/api/observation", {"key": ["mortarion_current"], "seed": ["x"]})
            with self.assertRaises(ValueError):
                respond("/api/deck", {"key": ["mortarion_ideal", "magnus_premium"]})


if __name__ == "__main__":
    unittest.main()
