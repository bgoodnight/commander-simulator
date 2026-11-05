"""Small validation fixtures for full-cohort Gorge warehouse export."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.gorge_warehouse_export import build_rows


class WarehouseExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        (self.folder / "native").mkdir()
        self.decks = ["mortarion_current", "wretched_ranks", "necron_dynasties", "science-pip"]
        self.row = {
            "seed": 1234, "finished": True, "replay_verified": True,
            "error": None, "hero_seat": 0, "decks": self.decks,
            "replay_chain": "chain-1234", "winner_seat": 0,
            "draw": False, "turns": 27, "policies": ["bot"] * 4,
        }
        self.source = {
            "schema": "gorge-native-trace-v1", "engine": "gorge",
            "format": "commander", "seed": 1234, "chain": "chain-1234",
            "decks": self.decks,
            "log": {"events": [
                {"seq": 1, "kind": 11, "text": "Example card", "player": 0},
                {"seq": 3, "kind": 27, "secret": True, "obj": 17},
            ], "intents": []},
        }
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        (self.folder / "runs.jsonl").write_text(json.dumps(self.row) + "\n")
        (self.folder / "native" / "gorge-seed-1234.json").write_text(json.dumps(self.source))

    def test_exact_native_events_and_private_metadata(self):
        games, events = build_rows(self.folder, "batch-7", "mortarion_current", 0)
        self.assertEqual(len(games), 1)
        self.assertEqual(len(events), 2)
        self.assertEqual(games[0]["native_event_count"], 2)
        self.assertEqual(games[0]["event_start_row"], 0)
        self.assertEqual(events[1]["seq"], 3)
        self.assertTrue(events[1]["secret"])
        self.assertEqual(json.loads(events[1]["event_json"]), self.source["log"]["events"][1])
        self.assertEqual(events[0]["game_id"], games[0]["game_id"])

    def test_event_offsets_are_contiguous_across_games(self):
        other = dict(self.row, seed=1235, replay_chain="chain-1235")
        rows = [self.row, other]
        (self.folder / "runs.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
        source2 = dict(self.source, seed=1235, chain="chain-1235")
        (self.folder / "native" / "gorge-seed-1235.json").write_text(
            json.dumps(source2))
        games, events = build_rows(self.folder, "batch-7", "mortarion_current", 0)
        self.assertEqual([g["event_start_row"] for g in games], [0, 2])
        self.assertEqual([g["native_event_count"] for g in games], [2, 2])
        for game in games:
            start = game["event_start_row"]
            end = start + game["native_event_count"]
            self.assertEqual({e["game_id"] for e in events[start:end]},
                             {game["game_id"]})

    def test_source_chain_mismatch_is_rejected(self):
        self.source["chain"] = "wrong"
        self.save()
        with self.assertRaisesRegex(ValueError, "mismatch"):
            build_rows(self.folder, "batch-7", "mortarion_current", 0)

    def test_unverified_game_is_rejected(self):
        self.row["replay_verified"] = False
        self.save()
        with self.assertRaisesRegex(ValueError, "Unverified"):
            build_rows(self.folder, "batch-7", "mortarion_current", 0)

    def test_duplicate_event_sequences_rejected(self):
        self.source["log"]["events"][1]["seq"] = 1
        self.save()
        with self.assertRaisesRegex(ValueError, "unordered"):
            build_rows(self.folder, "batch-7", "mortarion_current", 0)


if __name__ == "__main__":
    unittest.main()
