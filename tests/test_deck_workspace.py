"""U1 versioned deck editing and local-only HTTP API contracts."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from commander_sim.deck_workspace import (
    compose_draft, save_draft, saved_versions,
    get_saved_version, observe_saved_version
)
from commander_sim.deck_fixtures import FIXTURES, SHARED_CATALOG
from commander_sim.card_cache import pinned_deck_entries
from commander_sim.snapshots import validate_snapshot
from tools.deck_lab import post_response


class DeckWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name) / "workspace"
        self.key = "wretched_ranks"
        self.swaps = [{"remove": "Swamp", "add": "Pestilence"}]

    def test_real_cached_singleton_swap_is_valid_and_reports_diff(self):
        result = compose_draft(self.key, self.swaps)
        self.assertEqual(result["physical_cards"], 100)
        self.assertEqual(result["swaps"], 1)
        changed = {x["name"]: x["delta"] for x in result["diff"]}
        self.assertEqual(changed, {"Swamp": -1, "Pestilence": 1})
        self.assertFalse(result["actual_gameplay_available"])

    def test_saved_version_observation_accepts_mulligan_policy(self):
        save_draft(self.key, self.swaps, 'Mulligan test', workspace=self.workspace)
        version = saved_versions(workspace=self.workspace)[0]
        result=observe_saved_version(version['id'],workspace=self.workspace,seed=0,mulligan='one-free')
        self.assertEqual(result['mulligan']['policy'],'one-free')
        self.assertEqual(len(result['opening_hand']),7)

    def test_save_as_pins_replay_and_never_edits_original_fixture(self):
        fixture = next(f for f in FIXTURES if f.key == self.key)
        before = hashlib.sha256(fixture.deck_path.read_bytes()).hexdigest()
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network")):
            saved = save_draft(self.key, self.swaps, "Gisa Bog Test",
                               workspace=self.workspace)
        deck = Path(saved["deck_path"])
        self.assertTrue(deck.is_file())
        self.assertEqual(len(saved_versions(workspace=self.workspace)), 1)
        self.assertEqual(hashlib.sha256(fixture.deck_path.read_bytes()).hexdigest(), before)
        snapshot = validate_snapshot(deck, saved["snapshot"],
                                     commander="Ghoulcaller Gisa")
        self.assertEqual(snapshot.deck.count, 100)
        self.assertEqual(len(pinned_deck_entries(
            deck, saved["manifest"], SHARED_CATALOG)), len(snapshot.cards))
        with self.assertRaisesRegex(ValueError, "already exists"):
            save_draft(self.key, self.swaps, "Gisa Bog Test",
                       workspace=self.workspace)

    def test_rejects_invalid_duplicate_nonbasic(self):
        with self.assertRaisesRegex(ValueError, "Duplicate nonbasic"):
            compose_draft(self.key, [{"remove": "Swamp", "add": "Sol Ring"}])

    def test_rejects_off_color_addition(self):
        with self.assertRaisesRegex(ValueError, "outside commander color identity"):
            compose_draft(self.key, [{"remove": "Swamp", "add": "Island"}])

    def test_rejects_unverified_new_name_without_auto_fetch(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network")):
            with self.assertRaisesRegex(ValueError, "Card metadata unavailable"):
                compose_draft(self.key, [{"remove": "Swamp",
                                          "add": "Obviously Not A Scryfall Card"}])

    def test_rejects_invalid_removals_commander_or_draft_shape(self):
        for changes in (
            [{"remove": "Ghoulcaller Gisa", "add": "Swamp"}],
            [{"remove": "Swamp", "add": "Ghoulcaller Gisa"}],
            [{"remove": "Missing Card", "add": "Swamp"}],
            [{"remove": "Swamp", "add": "Sol Ring", "extra": "x"}],
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                compose_draft(self.key, changes)

    def test_preview_post_is_read_only_save_creates_new_workspace_version(self):
        payload = {"base_key": self.key, "changes": self.swaps}
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network")):
            preview = post_response("/api/draft/preview", payload)
            self.assertEqual(preview["physical_cards"], 100)
            self.assertNotIn("deck_text", preview)
            saved = post_response("/api/draft/save",
                         dict(payload, title="Test U1 saved"),
                         workspace=self.workspace)
            self.assertEqual(saved["base_key"], self.key)
            self.assertTrue(Path(saved["deck_path"]).is_file())
        with self.assertRaises(ValueError):
            post_response("/api/draft/preview", dict(payload, title="bad"))
        with self.assertRaises(KeyError):
            post_response("/api/draft/unknown", payload)

    def test_saved_variant_produces_deterministic_offline_observations(self):
        saved = save_draft(self.key, self.swaps, "Observe Gisa Experiment",
                           workspace=self.workspace)
        version = saved_versions(workspace=self.workspace)[0]
        self.assertEqual(get_saved_version(
            version["id"], workspace=self.workspace)["deck_sha256"],
            saved["deck_sha256"])
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network")):
            first = observe_saved_version(version["id"],
                        workspace=self.workspace, seed=5, turns=4)
            again = observe_saved_version(version["id"],
                        workspace=self.workspace, seed=5, turns=4)
        self.assertEqual(first, again)
        self.assertEqual(first["mode"], "observation")
        self.assertEqual(len(first["trace"]), 4)

    def test_saved_variant_id_rejects_traversal_and_unknown(self):
        with self.assertRaisesRegex(ValueError, "Invalid saved version ID"):
            get_saved_version("../secret", workspace=self.workspace)
        with self.assertRaisesRegex(ValueError, "Saved version not found"):
            observe_saved_version("no-such-version", workspace=self.workspace)

    def test_saved_version_tampering_is_detected(self):
        saved = save_draft(self.key, self.swaps, "Integrity Test",
                           workspace=self.workspace)
        Path(saved["deck_path"]).write_text("edited after save", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed since validation"):
            saved_versions(workspace=self.workspace)


if __name__ == "__main__":
    unittest.main()
