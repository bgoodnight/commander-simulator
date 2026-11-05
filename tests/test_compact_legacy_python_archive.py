"""The compacted old Python catalog must preserve actual UI-compatible games."""
import json
from pathlib import Path
import tempfile
import unittest

from tests.test_simulation_publishing import ENGINE, fake_run
from tools.build_simulation_archive import write_archive
from tools.compact_legacy_python_archive import compact, compact_index
from tools.publish_simulation_archive import KEYS, publish_archives, validate_index


class LegacyHotCatalogTests(unittest.TestCase):
    def test_keeps_first_matching_release_and_verified_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incoming = root / "incoming"
            incoming.mkdir()
            old = root / "source"
            key = sorted(KEYS)[0]
            write_archive(incoming, key, seeds=2, turns=3, runner=fake_run)
            publish_archives(incoming, old, engine_commit=ENGINE, keys=(key,))
            write_archive(incoming, key, seeds=2, turns=3,
                          start_seed=100, runner=fake_run)
            publish_archives(incoming, old,
                             engine_commit="b"*40, keys=(key,))
            decks = root / "decks.json"
            decks.write_text(json.dumps({
                "decks": [{"key": key, "deck_sha256": "a"*64}]
            }))
            full = validate_index(old)
            expected_id = full["releases"][0]["id"]
            result = compact(old, decks, root / "hot")
            hot = validate_index(root / "hot")
            self.assertEqual(result["original_releases"], 2)
            self.assertEqual(result["kept_releases"], 1)
            self.assertEqual(result["selected_decks"][key], expected_id)
            self.assertEqual(hot["releases"][0]["id"], expected_id)
            self.assertEqual(result["kept_files"], 3)
            self.assertEqual(
                (root/"hot"/hot["releases"][0]["decks"][key]["runs"]).read_bytes(),
                (old/hot["releases"][0]["decks"][key]["runs"]).read_bytes())

    def test_does_not_select_different_deck_hash(self):
        index = {"format": "commander-simulation-library-v1",
                 "releases": [{"id": "one", "decks": {
                     "deck-a": {"deck_sha256": "a"*64}}}]}
        with self.assertRaisesRegex(ValueError, "No live deck identities"):
            compact_index(index, {"decks": [
                {"key": "deck-a", "deck_sha256": "b"*64}]})

    def test_rejects_in_place_pruning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "distinct"):
                compact(root, root/"decks.json", root)


if __name__ == "__main__":
    unittest.main()
