"""Persistent, immutable published archives and safe Pages export."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.build_simulation_archive import write_archive
from tools.publish_simulation_archive import (
    KEYS, PUBLIC_FORMAT, publish_archives, validate_index)


ENGINE = "a" * 40


def fake_run(deck, *, seed, turns):
    events = []
    snapshots = []
    for turn in range(1, turns + 1):
        events.append({
            "turn": turn, "land_count": turn, "creature_count": 0,
            "mana_rock_count": 0, "hand_size": 7,
            "unsupported_cards_in_hand": [],
            "events": [{"type": "draw", "card": "Swamp"}]})
        snapshots.append({
            "turn": turn, "battlefield": [], "hand": [],
            "graveyard": [], "exile": [], "untracked_tokens": [],
            "object_views": {"battlefield": [], "hand": [],
                             "graveyard": [], "exile": []}})
    return {
        "seed": seed, "deck_key": deck, "deck_sha256": "a"*64,
        "mode": "bounded_authoritative_early_actions",
        "mulligan": {"policy": "keep"},
        "events": events, "state_snapshots": snapshots}


class PublishedSimulationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.source = Path(temp.name) / "incoming"
        self.destination = Path(temp.name) / "public"
        self.source.mkdir()
        self.key = sorted(KEYS)[0]

    def prepare(self, *, seeds=2, start_seed=0):
        write_archive(self.source, self.key, seeds=seeds, turns=3,
                      start_seed=start_seed, runner=fake_run)

    def test_published_index_preserves_immutable_verified_data(self):
        self.prepare()
        result = publish_archives(
            self.source, self.destination, engine_commit=ENGINE,
            keys=(self.key,))
        self.assertEqual(result["format"], PUBLIC_FORMAT)
        self.assertEqual(len(result["releases"]), 1)
        release = result["releases"][0]
        self.assertEqual(release["engine_commit"], ENGINE)
        entry = release["decks"][self.key]
        self.assertEqual(len(entry["deck_sha256"]), 64)
        self.assertEqual(hashlib.sha256(
            (self.destination / entry["runs"]).read_bytes()).hexdigest(),
            entry["run_sha256"])
        self.assertEqual(validate_index(self.destination), result)

    def test_idempotence_and_preserve_prior_releases(self):
        self.prepare()
        a = publish_archives(self.source, self.destination, engine_commit=ENGINE,
                             keys=(self.key,))
        b = publish_archives(self.source, self.destination, engine_commit=ENGINE,
                             keys=(self.key,))
        self.assertEqual(a, b)
        self.prepare(start_seed=100)
        c = publish_archives(self.source, self.destination, engine_commit=ENGINE,
                             keys=(self.key,))
        self.assertEqual(len(c["releases"]), 2)
        self.assertEqual(validate_index(self.destination), c)

    def test_newest_published_release_first_even_when_sha_sorts_earlier(self):
        self.prepare()
        first = publish_archives(
            self.source, self.destination, engine_commit="f" * 40,
            keys=(self.key,))
        self.assertEqual(first["releases"][0]["engine_commit"], "f" * 40)
        # A later commit may have a lexically smaller SHA. Publication
        # order, not SHA sorting, determines the current UI archive.
        self.prepare(start_seed=200)
        second = publish_archives(
            self.source, self.destination, engine_commit="0" * 40,
            keys=(self.key,))
        self.assertEqual(len(second["releases"]), 2)
        self.assertEqual(second["releases"][0]["engine_commit"], "0" * 40)
        self.assertEqual(second["releases"][1]["engine_commit"], "f" * 40)
        self.assertEqual(validate_index(self.destination), second)
        # Republishing the same version must not reshuffle history.
        third = publish_archives(
            self.source, self.destination, engine_commit="0" * 40,
            keys=(self.key,))
        self.assertEqual(third, second)

    def test_rejects_archive_tampering(self):
        self.prepare()
        publish_archives(self.source, self.destination, engine_commit=ENGINE,
                         keys=(self.key,))
        release = validate_index(self.destination)["releases"][0]
        path = self.destination / release["decks"][self.key]["runs"]
        path.write_bytes(path.read_bytes() + b"!")
        with self.assertRaisesRegex(ValueError, "checksum"):
            validate_index(self.destination)

    def test_rejects_unsafe_relative_paths(self):
        self.prepare()
        publish_archives(self.source, self.destination, engine_commit=ENGINE,
                         keys=(self.key,))
        path = self.destination / "manifest.json"
        index = json.loads(path.read_text())
        index["releases"][0]["decks"][self.key]["runs"] = "../secret.json"
        path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            validate_index(self.destination)

    def test_invalid_engine_sha_refused(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "commit SHA"):
            publish_archives(self.source, self.destination, engine_commit="main",
                             keys=(self.key,))

    def test_pages_export_includes_archive_without_touching_existing_results(self):
        from tools.build_pages_deck_lab import build
        self.prepare()
        publish_archives(self.source, self.destination, engine_commit=ENGINE,
                         keys=(self.key,))
        with tempfile.TemporaryDirectory() as output_dir:
            output = Path(output_dir) / "pages"
            manifest = build(output, archive_source=self.destination)
            self.assertTrue((output / "bounded-batches.json").is_file())
            self.assertTrue((output / "simulation-data/manifest.json").is_file())
            self.assertEqual(
                validate_index(output / "simulation-data"),
                validate_index(self.destination))
            self.assertIn("simulation-data/manifest.json", manifest["asset_sha256"])


if __name__ == "__main__":
    unittest.main()
