"""Archived Python recordings must be complete, deterministic, and restorable."""
from pathlib import Path
import tempfile
import unittest

from tools.build_simulation_archive import write_archive
from tools.publish_simulation_archive import KEYS, publish_archives
from tools.archive_legacy_python import make_bundle, source_paths, verify_download


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
        "seed": seed, "deck_key": deck, "deck_sha256": "a" * 64,
        "mode": "bounded_authoritative_early_actions",
        "mulligan": {"policy": "keep"},
        "events": events, "state_snapshots": snapshots}


class LegacyPythonBackupTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.incoming = self.root / "incoming"
        self.incoming.mkdir()
        self.source = self.root / "published"
        self.deck = sorted(KEYS)[0]
        write_archive(self.incoming, self.deck, seeds=2, turns=3, runner=fake_run)
        publish_archives(self.incoming, self.source,
                         engine_commit=ENGINE, keys=(self.deck,))

    def test_deterministic_complete_roundtrip(self):
        a = make_bundle(self.source, self.root / "backup1")
        b = make_bundle(self.source, self.root / "backup2")
        self.assertEqual(a, b)
        self.assertEqual(a["release_count"], 1)
        self.assertEqual(a["source_file_count"], 3)
        self.assertTrue(verify_download(
            self.root / "backup1/legacy-python-source.tar.gz", a
        ))
        self.assertTrue(a["r2_object_key"].startswith("legacy-python/v1/"))

    def test_unindexed_file_refused(self):
        (self.source / "unexpected.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            source_paths(self.source)

    def test_corrupt_archive_refused(self):
        a = make_bundle(self.source, self.root / "backup")
        archive = self.root / "backup/legacy-python-source.tar.gz"
        archive.write_bytes(archive.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify_download(archive, a)


if __name__ == "__main__":
    unittest.main()
